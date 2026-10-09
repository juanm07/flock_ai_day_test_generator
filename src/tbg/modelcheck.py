"""Validación del TestModel que produjo el LLM, antes de generar nada (filtro "assured" de entrada)."""

from __future__ import annotations

from dataclasses import dataclass

from . import rules
from .hu import UserStory
from .quotes import quote_in
from .schemas import TestModel


@dataclass(frozen=True)
class Issue:
    level: str  # "error" | "warning"
    path: str
    message: str


def check(model: TestModel, story: UserStory) -> list[Issue]:
    out: list[Issue] = []

    def err(path: str, msg: str) -> None:
        out.append(Issue("error", path, msg))

    def warn(path: str, msg: str) -> None:
        out.append(Issue("warning", path, msg))

    vocab = set(rules.load("tags"))
    for t in model.feature_tags:
        if t not in vocab:
            err("feature_tags", f"Tag '{t}' fuera del vocabulario (rules/tags.yaml): {sorted(vocab)}")

    ac_ids = [ac.id for ac in model.acceptance_criteria]
    if len(set(ac_ids)) != len(ac_ids):
        err("acceptance_criteria", "IDs de CA duplicados")
    for i, ac in enumerate(model.acceptance_criteria):
        if not quote_in(ac.text, story.text):
            err(f"acceptance_criteria[{i}].text", f"{ac.id}: el texto no aparece literalmente en la HU (¿parafraseado o inventado?)")
    parsed = dict(story.acceptance_criteria)
    if parsed and set(parsed) != set(ac_ids):
        warn("acceptance_criteria", f"El parser encontró {sorted(parsed)} y el modelo trae {sorted(ac_ids)}")

    names = [p.name for p in model.parameters]
    if len(set(names)) != len(names):
        err("parameters", "Nombres de parámetro duplicados")
    choices_by_param: dict[str, set[str]] = {}
    for i, p in enumerate(model.parameters):
        path = f"parameters[{i}]({p.name})"
        cn = [c.name for c in p.choices]
        if len(set(cn)) != len(cn):
            err(path, "Elecciones con nombre duplicado")
        choices_by_param[p.name] = set(cn)
        for ref in p.ac_refs:
            if ref not in ac_ids:
                err(path, f"ac_refs referencia {ref}, que no existe")
        if not p.ac_refs:
            warn(path, "Parámetro sin CA asociado: no entra en ninguna combinación")
        if not any(c.kind == "valid" for c in p.choices):
            warn(path, "Sin elección válida: no hay caso base para este parámetro")
        if p.bounds and p.bounds.min is not None and p.bounds.max is not None and p.bounds.min > p.bounds.max:
            err(path, "bounds.min > bounds.max")
        for j, c in enumerate(p.choices):
            cpath = f"{path}.choices[{j}]({c.name})"
            if c.quote is not None and not quote_in(c.quote, story.text):
                err(cpath, f"La cita «{c.quote}» no aparece en la HU")
            if c.expected is not None and c.quote is None and not c.assumed:
                err(cpath, "'expected' sin 'quote': si la HU no lo dice, dejar expected=null (→ [SUPUESTO]) o marcar assumed")
            if c.example is None and c.kind != "exception":
                warn(cpath, "Sin 'example': el caso no tendrá dato concreto")

    for i, c in enumerate(model.constraints):
        for p, v in [*c.if_choice.items(), *((p, v) for p, vs in c.forbids.items() for v in vs)]:
            if p not in choices_by_param or v not in choices_by_param[p]:
                err(f"constraints[{i}]", f"Referencia inexistente {p}={v}")
    return out
