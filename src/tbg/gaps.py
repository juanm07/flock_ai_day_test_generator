"""Detección determinista de lagunas (preguntas al PO).

Tres fuentes, todas reproducibles:
1. Estructura: HU sin CAs, CAs con smells o sin resultado observable (salida del lint).
2. Reglas por feature_tag (rules/gaps.yaml): el checklist de preguntas-al-po.md hecho ejecutable.
3. Completitud del TestModel: parámetros que deberían tener límites y no los tienen, elecciones
   inválidas sin comportamiento esperado definido.
"""

from __future__ import annotations

from . import rules
from .hu import UserStory
from .lint import match_any
from .schemas import Finding, Gap, TestModel

_CLASS_RANK = {"BLOQUEANTE": 0, "IMPORTANTE": 1, "MENOR": 2}


def _param_matches(rule: dict, model: TestModel | None):
    if not model or not rule.get("param_terms"):
        return []
    return [p for p in model.parameters if match_any(rule["param_terms"], f"{p.name} {p.description}")]


def _fmt_bounds(b) -> str:
    lo = "" if b.min is None else f"{b.min:g}"
    hi = "" if b.max is None else f"{b.max:g}"
    return f"{lo}–{hi} {b.unit} ({b.origin})"


def detect(story: UserStory, tags: set[str], findings: list[Finding], model: TestModel | None = None) -> list[Gap]:
    answers = model.answers if model else {}
    gaps: list[Gap] = []

    # 1. Estructura
    if not story.acceptance_criteria and not (model and model.acceptance_criteria):
        gaps.append(Gap(id="structure.no_ac", category="A. Criterios de aceptación", gap_class="BLOQUEANTE",
                        question="La HU no tiene criterios de aceptación: ¿cuáles son las condiciones para darla por terminada?",
                        why="Sin CAs no hay oráculo: cualquier resultado esperado sería inventado.",
                        default="No se generan casos hasta tener CAs (modo análisis).", source="structure"))
    seen_ac: set[str] = set()
    ac_order = lambda f: int(f.location[3:]) if f.location.startswith("CA-") and f.location[3:].isdigit() else 0  # noqa: E731
    for f in sorted(findings, key=ac_order):
        if f.location.startswith("CA-") and f.location not in seen_ac and (
            f.rule.startswith("smell.") and f.rule != "smell.negative_statements" or f.rule == "qus.ac_observable"
        ):
            seen_ac.add(f.location)
            gap_id = f"ac.verifiable.{f.location}"
            gaps.append(Gap(id=gap_id, category="A. Criterios de aceptación", gap_class="IMPORTANTE",
                            question=f"En {f.location}, «{f.text or 'el criterio'}» no es verificable: ¿cuál es el resultado/umbral concreto?",
                            why=f"{f.message} Sin umbral, otra persona no puede decir 'pasó' o 'falló'.",
                            default="Se prueba de forma exploratoria y se documenta lo observado.",
                            source=f.rule))

    # 2. Reglas por tag
    spec = rules.load("gaps")
    merged_params: set[str] = set()
    for rule in spec["rules"]:
        if not tags.intersection(rule["when_tags"]):
            continue
        gap = Gap(id=rule["id"], category=rule["category"], gap_class=rule["class"], question=rule["question"],
                  why=rule["why"], default=rule["default"], source="tag:" + ",".join(sorted(tags.intersection(rule["when_tags"]))))
        hit = match_any(rule.get("covered_if", []), story.text)
        params = _param_matches(rule, model)
        merged_params.update(p.name for p in params)
        bounded = [p for p in params if p.bounds and p.bounds.origin != "SUPUESTO"]
        assumed = [p for p in params if p.bounds and p.bounds.origin == "SUPUESTO"]
        if rule["id"] in answers:
            gap.status, gap.answer = "answered", answers[rule["id"]].value
        elif bounded:
            gap.status, gap.answer = "answered", "; ".join(f"{p.name}: {_fmt_bounds(p.bounds)}" for p in bounded)
        elif assumed:  # el agente asumió límites: la pregunta sigue abierta y el default pasa a ser lo asumido
            gap.default = "; ".join(f"{p.name}: {_fmt_bounds(p.bounds)}" for p in assumed) + ". " + gap.default
        elif hit:
            gap.status, gap.answer = "covered", f"La HU lo define («{hit}»)"
        gaps.append(gap)

    # 3. Completitud del modelo
    if model:
        for p in model.parameters:
            unknown = p.bounds is None or p.bounds.origin == "SUPUESTO"
            if p.bounds_relevant and unknown and p.name not in merged_params:
                gid = f"param.bounds.{p.name}"
                default = (f"{_fmt_bounds(p.bounds)}." if p.bounds else
                           "Se prueba con valores típicos; los bordes quedan como exploratorios.")
                g = Gap(id=gid, category="B. Datos", gap_class="IMPORTANTE",
                        question=f"¿Cuáles son los límites de «{p.description}» (mínimo/máximo)?",
                        why="Sin límites no se pueden calcular los valores de borde (mín-1, mín, máx, máx+1).",
                        default=default, source="schema:bounds")
                if gid in answers:
                    g.status, g.answer = "answered", answers[gid].value
                gaps.append(g)
            for c in p.choices:
                if c.kind != "valid" and c.expected is None:
                    gid = f"choice.expected.{p.name}.{c.name}"
                    g = Gap(id=gid, category="C. Errores", gap_class="MENOR",
                            question=f"¿Qué ve el usuario cuando «{p.description}» es «{c.description}»?",
                            why="El comportamiento ante este error no está definido en la HU.",
                            default="Se rechaza con un mensaje que explica el error y no cambia el estado del sistema.",
                            source="schema:expected")
                    if gid in answers:
                        g.status, g.answer = "answered", answers[gid].value
                    gaps.append(g)

    order = {g.id: i for i, g in enumerate(gaps)}
    gaps.sort(key=lambda g: (_CLASS_RANK[g.gap_class], order[g.id]))
    budget = spec.get("max_questions", 8)
    for g in gaps:
        if g.status == "open" and budget > 0:
            g.asked = True
            budget -= 1
    return gaps


def bounds_gap_id(param_name: str, model: TestModel) -> str:
    """Id de la laguna que gobierna los límites de un parámetro (regla con param_terms o param.bounds.<name>)."""
    p = next(p for p in model.parameters if p.name == param_name)
    for rule in rules.load("gaps")["rules"]:
        if rule.get("param_terms") and match_any(rule["param_terms"], f"{p.name} {p.description}"):
            if set(model.feature_tags).intersection(rule["when_tags"]):
                return rule["id"]
    return f"param.bounds.{p.name}"


def supuesto_for(gap: Gap) -> str | None:
    """Texto del supuesto que rige mientras la laguna no tenga respuesta."""
    return None if gap.status != "open" else f"{gap.default} (ver {gap.id})"
