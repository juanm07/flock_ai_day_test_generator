"""Formulario para el PO: las preguntas abiertas en un YAML que el PO completa, con campos ESTRUCTURADOS para los
límites (mín/máx/unidad). `po-apply` lo vuelca al TestModel de forma determinista: un límite respondido acá
habilita los casos de valores límite sin que nadie tenga que interpretar texto libre.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import yaml

from . import rules
from .gaps import bounds_gap_id
from .schemas import Answer, Bounds, Gap, TestModel

_UNITS = ("chars", "value", "bytes", "items", "days")


def _q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)  # string JSON = escalar YAML válido


def bounded_params(gap: Gap, model: TestModel) -> list[str]:
    """Parámetros cuyos límites responde esta pregunta."""
    if gap.id.startswith("param.bounds."):
        return [gap.id.removeprefix("param.bounds.")]
    return [p.name for p in model.parameters if p.bounds_relevant and bounds_gap_id(p.name, model) == gap.id]


def _default_bounds(gap_id: str) -> dict | None:
    rule = next((r for r in rules.load("gaps")["rules"] if r["id"] == gap_id), None)
    return rule.get("default_bounds") if rule else None


def build_form(model: TestModel, gaps: list[Gap]) -> str:
    asked = [g for g in gaps if g.asked]
    lines = [
        f"# Preguntas para el PO — {model.story_id}: {model.title}",
        "#",
        "# Cómo completarlo:",
        "#  - Escribí tu respuesta en `respuesta`, o poné `acepto_default: true` si el default propuesto está bien.",
        "#  - Si la pregunta tiene `limites`, completá `min` y/o `max` con números: con eso se generan solos los casos",
        "#    de valores límite (mín-1, mín, mín+1, máx-1, máx, máx+1).",
        "#  - Lo que quede vacío sigue como [SUPUESTO] en la suite.",
        "# Aplicar: tbg po-apply <este archivo> <model.json>",
        "",
        f"story_id: {_q(model.story_id)}",
        "preguntas:",
    ]
    for i, g in enumerate(asked, 1):
        lines += [
            f"  - id: {_q(g.id)}            # P-{i} · {g.category} · {g.gap_class}",
            f"    pregunta: {_q(g.question)}",
            f"    por_que: {_q(g.why)}",
            f"    default: {_q(g.default)}",
            "    acepto_default: false",
            '    respuesta: ""',
        ]
        params = bounded_params(g, model)
        if params:
            sug = _default_bounds(g.id) or {}
            lines.append("    limites:")
            for name in params:
                p = next(x for x in model.parameters if x.name == name)
                unit = (p.bounds.unit if p.bounds else None) or sug.get("unit", "chars")
                lines += [
                    f"      {name}:            # {p.description}",
                    f"        unidad: {unit}       # {' | '.join(_UNITS)}",
                    f"        min:              # sugerido: {sug.get('min', '—')}",
                    f"        max:              # sugerido: {sug.get('max', '—')}",
                ]
    return "\n".join(lines) + "\n"


@dataclass
class Applied:
    answers: list[str]
    bounds: list[str]
    skipped: list[str]


def apply_form(form_text: str, model: TestModel, gaps: list[Gap]) -> Applied:
    return apply_data(yaml.safe_load(form_text) or {}, model, gaps)


def apply_data(data: dict, model: TestModel, gaps: list[Gap]) -> Applied:
    """Mismo contrato que el YAML: {"story_id", "preguntas": [{id, respuesta, acepto_default, limites}]}."""
    if data.get("story_id") not in (None, model.story_id):
        raise ValueError(f"El formulario es de {data.get('story_id')} y el modelo de {model.story_id}")
    known = {g.id: g for g in gaps}
    params = {p.name: p for p in model.parameters}
    out = Applied([], [], [])
    for item in data.get("preguntas") or []:
        gid = item.get("id")
        if gid not in known:
            raise ValueError(f"Pregunta desconocida en el formulario: {gid}")
        gap = known[gid]
        filled_bounds = False
        for name, spec in (item.get("limites") or {}).items():
            spec = spec or {}
            lo, hi = spec.get("min"), spec.get("max")
            if lo is None and hi is None:
                continue
            if name not in params:
                raise ValueError(f"{gid}: parámetro inexistente {name}")
            for v in (lo, hi):
                if v is not None and not isinstance(v, (int, float)):
                    raise ValueError(f"{gid}.{name}: min/max deben ser números (recibido {v!r})")
            if lo is not None and hi is not None and lo > hi:
                raise ValueError(f"{gid}.{name}: min ({lo}) > max ({hi})")
            unit = spec.get("unidad") or "chars"
            if unit not in _UNITS:
                raise ValueError(f"{gid}.{name}: unidad inválida {unit!r}")
            params[name].bounds = Bounds(min=lo, max=hi, unit=unit, origin="PO",
                                         integer=all(isinstance(v, int) for v in (lo, hi) if v is not None))
            params[name].bounds_relevant = True
            filled_bounds = True
            out.bounds.append(f"{name}: {lo if lo is not None else ''}–{hi if hi is not None else ''} {unit}")
        text = (item.get("respuesta") or "").strip()
        if text:
            model.answers[gid] = Answer(value=text, by="PO")
            out.answers.append(gid)
        elif item.get("acepto_default"):
            model.answers[gid] = Answer(value=gap.default, by="PO")
            out.answers.append(f"{gid} (default)")
            sug = _default_bounds(gid)
            if sug and not filled_bounds:
                for name in bounded_params(gap, model):
                    params[name].bounds = Bounds(min=sug.get("min"), max=sug.get("max"), unit=sug.get("unit", "chars"),
                                                 origin="PO")
                    params[name].bounds_relevant = True
                    out.bounds.append(f"{name}: {sug.get('min')}–{sug.get('max')} {sug.get('unit', 'chars')} (default aceptado)")
        elif not filled_bounds:
            out.skipped.append(gid)
    return out



def summary(res: Applied) -> str:
    def n(k: int, one: str, many: str) -> str:
        return f"{k} {one if k == 1 else many}"

    return f"{n(len(res.answers), 'respuesta', 'respuestas')}, {n(len(res.bounds), 'límite', 'límites')}"
