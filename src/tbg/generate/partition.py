"""Construcción de test frames — Category-Partition Method (Ostrand & Balcer, CACM 31(6), 1988).

- Unidad funcional = criterio de aceptación (CA): sus parámetros son las categorías a combinar.
- Elecciones válidas → combinación 2-wise (pairwise), filtrada por las restricciones del modelo.
- Elecciones [error] (invalid) y de excepción → un frame propio cada una, con el resto en su elección base
  (en TSL: `[error]`/`[single]` no se combinan, para no enmascarar un error con otro).
- Parámetros con límites → frames de valores límite (BVA).
- Reglas de rules/gaps.yaml con `frame` → heurísticas de testing (seguridad, estados, excepciones).

Todo es determinista: mismo TestModel ⇒ mismos frames, mismo orden, mismos IDs.
"""

from __future__ import annotations

import hashlib
import json
import re

from .. import rules
from ..gaps import bounds_gap_id, supuesto_for
from ..lint import match_any
from ..schemas import Choice, Frame, Gap, Parameter, TestModel
from . import bva, pairwise

_TYPE_ORDER = {"Funcional": 0, "Negativo": 1, "Borde": 2, "Excepción": 3, "No funcional": 4}


def _ac_num(ac_id: str) -> int:
    m = re.search(r"\d+", ac_id)
    return int(m.group()) if m else 999


def make_forbidden(model: TestModel) -> pairwise.Forbidden:
    banned: set[tuple[str, str, str, str]] = set()
    for c in model.constraints:
        for p1, v1 in c.if_choice.items():
            for p2, vs in c.forbids.items():
                for v2 in vs:
                    banned.add((p1, v1, p2, v2))
                    banned.add((p2, v2, p1, v1))

    def forbidden(p1: str, v1: str, p2: str, v2: str) -> bool:
        return (p1, v1, p2, v2) in banned

    return forbidden


def base_choice(p: Parameter) -> Choice | None:
    return next((c for c in p.choices if c.kind == "valid"), None)


def ac_groups(model: TestModel) -> list[tuple[str, list[Parameter]]]:
    return [(ac.id, [p for p in model.parameters if ac.id in p.ac_refs]) for ac in model.acceptance_criteria]


def valid_dims(params: list[Parameter]) -> list[tuple[str, list[str]]]:
    return [(p.name, [c.name for c in p.choices if c.kind == "valid"]) for p in params if base_choice(p)]


class _Builder:
    def __init__(self, model: TestModel, gaps: list[Gap]):
        self.model = model
        self.gaps = {g.id: g for g in gaps}
        self.params = {p.name: p for p in model.parameters}
        self.frames: dict[str, Frame] = {}

    def _choice(self, pname: str, cname: str) -> Choice:
        return next(c for c in self.params[pname].choices if c.name == cname)

    def add(self, *, type: str, title_hint: str, ac_refs: list[str], bindings: dict[str, str], origin: str,
            data: dict[str, str] | None = None, expected: list[str] | None = None, supuestos: list[str] | None = None,
            exploratory: bool = False, extra_key: str = "", examples: list[dict[str, str]] | None = None) -> None:
        sig = json.dumps({"t": type, "b": bindings, "o": origin.split(":")[0] if not origin.startswith("rule") else origin,
                          "k": extra_key}, sort_keys=True, ensure_ascii=False)
        if sig in self.frames:  # mismo frame alcanzado desde otro CA → se fusiona la trazabilidad
            f = self.frames[sig]
            f.ac_refs = sorted(set(f.ac_refs) | set(ac_refs), key=_ac_num)
            return
        if data is None:
            data = {}
            for p, c in bindings.items():
                ex = self._choice(p, c).example
                if ex is not None:
                    data[p] = ex if ex != "" else "'' (vacío)"
        exp, sup = list(expected or []), list(supuestos or [])
        for p, c in bindings.items():
            if p in self.params and any(ch.name == c for ch in self.params[p].choices):
                ch = self._choice(p, c)
                if ch.expected and ch.expected not in exp:
                    exp.append(ch.expected)
                if ch.assumed:
                    sup.append(f"«{ch.description}» se considera {'válido' if ch.kind == 'valid' else 'inválido'} "
                               "aunque la HU no lo dice")
                if ch.kind != "valid" and ch.expected is None:
                    g = self.gaps.get(f"choice.expected.{p}.{c}")
                    if g and g.status == "answered":
                        exp.append(g.answer or "")
                    else:
                        sup.append(f"Se rechaza con un mensaje que explica el error y no cambia el estado "
                                   f"(ver choice.expected.{p}.{c})")
        self.frames[sig] = Frame(
            frame_id="F-" + hashlib.sha1(sig.encode()).hexdigest()[:8], type=type, title_hint=title_hint,
            ac_refs=sorted(set(ac_refs), key=_ac_num), bindings=bindings, data=data, expected_hints=exp,
            supuestos=sup, exploratory=exploratory, origin=origin, examples=examples or [],
        )

    # ---- técnicas -------------------------------------------------------

    def valid_combinations(self) -> None:
        forbidden = make_forbidden(self.model)
        for ac_id, params in ac_groups(self.model):
            dims = valid_dims(params)
            base = {p.name: base_choice(p).name for p in params if base_choice(p)}
            rows = pairwise.generate(dims, forbidden)
            # el happy path (todas las elecciones base) va primero y siempre existe
            rows = [base] + [r for r in rows if r != base] if base or not dims else rows
            for row in rows:
                is_base = row == base
                variant = ", ".join(f"{p}={c}" for p, c in row.items() if c != base.get(p))
                self.add(type="Funcional", ac_refs=[ac_id], bindings=row,
                         origin="ac-happy-path" if is_base else ("pairwise" if len(dims) >= 2 else "each-choice"),
                         title_hint=f"Camino feliz de {ac_id}" if is_base else f"{ac_id} con {variant}",
                         extra_key="" if row else ac_id)  # sin parámetros: un caso por criterio, no uno para todos

    def error_choices(self) -> None:
        for p in self.model.parameters:
            for c in p.choices:
                if c.kind == "valid":
                    continue
                neighbors = {q.name: base_choice(q).name for q in self.model.parameters
                             if q.name != p.name and set(q.ac_refs) & set(p.ac_refs) and base_choice(q)}
                self.add(type="Negativo" if c.kind == "invalid" else "Excepción", ac_refs=p.ac_refs,
                         bindings={**neighbors, p.name: c.name}, origin="error-choice",
                         title_hint=f"{p.description}: {c.description}")

    def boundaries(self) -> None:
        for p in self.model.parameters:
            if not p.bounds:
                continue
            values = bva.boundary_values(p.bounds)
            neighbors = {q.name: base_choice(q).name for q in self.model.parameters
                         if q.name != p.name and set(q.ac_refs) & set(p.ac_refs) and base_choice(q)}
            neighbor_data = {}
            for q, c in neighbors.items():
                ex = self._choice(q, c).example
                if ex:
                    neighbor_data[q] = ex
            sup = []
            if p.bounds.origin == "SUPUESTO":
                lo = "" if p.bounds.min is None else f"{p.bounds.min:g}"
                hi = "" if p.bounds.max is None else f"{p.bounds.max:g}"
                sup.append(f"Límites {lo}–{hi} {p.bounds.unit} asumidos (ver {bounds_gap_id(p.name, self.model)})")
            for side in ("inferior", "superior"):
                vals = [v for v in values if v.side == side]
                if not vals:
                    continue
                data = dict(neighbor_data)
                exp = []
                for v in vals:
                    data[f"{p.name} [{v.label}]"] = bva.concrete(v, p.bounds.unit)
                    exp.append(f"{p.name} {v.label} ({v.value:g} {p.bounds.unit}): {'aceptado' if v.valid else 'rechazado'}")
                self.add(type="Borde", ac_refs=p.ac_refs, bindings={**neighbors, p.name: "bva:" + ",".join(v.label for v in vals)},
                         origin="bva", data=data, expected=exp, supuestos=sup,
                         title_hint=f"Límite {side} de {p.description}",
                         # los valores son parte de la identidad: si el PO cambia el límite, el caso se re-redacta
                         extra_key=",".join(f"{v.value:g}{p.bounds.unit}" for v in vals),
                         examples=[{"etiqueta": v.label, "valor": bva.literal(v, p.bounds.unit),
                                    "medida": f"{v.value:g} {p.bounds.unit}",
                                    "resultado": "aceptado" if v.valid else "rechazado"} for v in vals])

    def rule_frames(self, story_text_by_ac: dict[str, str]) -> None:
        for rule in rules.load("gaps")["rules"]:
            spec = rule.get("frame")
            gap = self.gaps.get(rule["id"])
            if not spec or not gap:
                continue
            acs: list[str] = []
            for term in spec["anchor"]:  # gana el término más específico que matchee algún CA
                acs = [ac for ac, txt in story_text_by_ac.items() if match_any([term], txt)]
                if acs:
                    break
            exp, sup, exploratory = [spec["expected_hint"]], [], False
            if gap.status == "answered":
                exp.append(f"Según respuesta: {gap.answer}")
            elif gap.status == "open":
                sup.append(supuesto_for(gap))
                exploratory = bool(spec.get("exploratory_if_open"))
            self.add(type=spec["type"], ac_refs=acs, bindings={}, origin=f"rule:{rule['id']}", expected=exp,
                     supuestos=sup, exploratory=exploratory, title_hint=spec["title_hint"])


def subsume(frames: list[Frame]) -> list[Frame]:
    """Fusiona frames funcionales cuyos bindings están contenidos en los de otro: ejecutar el mayor ya ejercita
    el menor (ej. 'CA-3 con contraseña unicode' ⊂ 'CA-4 login con contraseña unicode')."""
    kept: list[Frame] = []
    for f in frames:
        sup = None
        if f.type == "Funcional" and f.bindings:
            items = set(f.bindings.items())
            supersets = [g for g in frames if g is not f and g.type == "Funcional" and items < set(g.bindings.items())]
            sup = max(supersets, key=lambda g: len(g.bindings), default=None)  # el maximal nunca se descarta
        if sup is None:
            kept.append(f)
            continue
        sup.ac_refs = sorted(set(sup.ac_refs) | set(f.ac_refs), key=_ac_num)
        if f.origin == "ac-happy-path":
            sup.origin, sup.title_hint = "ac-happy-path", f.title_hint
        sup.expected_hints += [e for e in f.expected_hints if e not in sup.expected_hints]
        sup.supuestos += [s for s in f.supuestos if s not in sup.supuestos]
    return kept


def build_frames(model: TestModel, gaps: list[Gap]) -> list[Frame]:
    b = _Builder(model, gaps)
    b.valid_combinations()
    b.error_choices()
    b.boundaries()
    b.rule_frames({ac.id: ac.text for ac in model.acceptance_criteria})
    created = {id(f): i for i, f in enumerate(b.frames.values())}  # orden de generación (determinista) como desempate
    frames = subsume(list(b.frames.values()))
    frames.sort(key=lambda f: (min((_ac_num(a) for a in f.ac_refs), default=999), _TYPE_ORDER[f.type],
                               0 if f.origin == "ac-happy-path" else 1, created[id(f)]))
    for i, f in enumerate(frames, 1):
        f.case_id = f"CP-{i:03d}"
    return frames
