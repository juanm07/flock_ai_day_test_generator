"""Elementos minoritarios del consenso: lo que vio una sola de las N lecturas independientes de la IA.

No entran al modelo automáticamente (no tienen mayoría), pero una persona puede decidir que sí corresponden.
Este módulo los describe en lenguaje de QA y los agrega al TestModel cuando se lo pide.
"""

from __future__ import annotations

from . import rules
from .schemas import Choice, Constraint, Parameter, TestModel

_KIND = {"valid": "válida", "invalid": "inválida (el sistema debe rechazarla)", "exception": "excepción del entorno"}


def _param_label(model: TestModel, name: str) -> str:
    p = next((p for p in model.parameters if p.name == name), None)
    return p.description if p else name.replace("_", " ")


def _choice_label(model: TestModel, param: str, choice: str) -> str:
    p = next((p for p in model.parameters if p.name == param), None)
    c = next((c for c in p.choices if c.name == choice), None) if p else None
    return c.description if c else choice.replace("_", " ")


def _payload(m: dict) -> dict:
    """Payload del elemento; reconstruido desde el nombre para consensos guardados por versiones anteriores."""
    if m.get("payload"):
        return m["payload"]
    if m["kind"] == "tag":
        return {"tag": m["name"]}
    if m["kind"] == "restricción":
        try:
            return {"constraint": Constraint.model_validate_json(m["name"]).model_dump()}
        except ValueError:
            return {}
    if m["kind"] == "elección" and "." in m["name"]:
        param, choice = m["name"].split(".", 1)
        return {"param": param, "choice": {"name": choice, "description": m.get("detail") or choice, "kind": "invalid"},
                "legacy": True}
    return {}


def describe(m: dict, model: TestModel) -> str:
    pl = _payload(m)
    if m["kind"] == "tag":
        desc = rules.load("tags").get(pl.get("tag", m["name"]), {}).get("description", "")
        return f"Tipo de funcionalidad «{pl.get('tag', m['name'])}»" + (f": {desc}" if desc else "")
    if m["kind"] == "parámetro" and pl.get("parameter"):
        p = pl["parameter"]
        variants = ", ".join(c["description"] for c in p.get("choices", []))
        return f"Dato «{p['description']}» (variantes: {variants})"
    if m["kind"] == "elección" and pl.get("choice"):
        c = pl["choice"]
        return f"Variante «{c['description']}» de «{_param_label(model, pl.get('param', ''))}» — {_KIND.get(c['kind'], c['kind'])}"
    if m["kind"] == "restricción" and pl.get("constraint"):
        c = pl["constraint"]
        cond = " y ".join(f"«{_param_label(model, p)}» es «{_choice_label(model, p, v)}»" for p, v in c["if_choice"].items())
        bans = "; ".join(f"«{_param_label(model, p)}» no puede ser " + " ni ".join(f"«{_choice_label(model, p, v)}»" for v in vs)
                         for p, vs in c["forbids"].items())
        why = f" ({m['detail']})" if m.get("detail") and m["detail"] != "consenso" else ""
        return f"Combinación imposible: si {cond}, {bans}{why}"
    return f"{m['kind']} {m['name']}"


def present(m: dict, model: TestModel) -> bool:
    """¿Ya está en el modelo (por ejemplo, porque alguien lo agregó)?"""
    pl = _payload(m)
    if m["kind"] == "tag":
        return pl.get("tag") in model.feature_tags
    if m["kind"] == "parámetro" and pl.get("parameter"):
        return any(p.name == pl["parameter"]["name"] for p in model.parameters)
    if m["kind"] == "elección" and pl.get("choice"):
        p = next((p for p in model.parameters if p.name == pl.get("param")), None)
        return bool(p and any(c.name == pl["choice"]["name"] for c in p.choices))
    if m["kind"] == "restricción" and pl.get("constraint"):
        target = Constraint.model_validate(pl["constraint"])
        return any(c.if_choice == target.if_choice and c.forbids == target.forbids for c in model.constraints)
    return False


def apply(m: dict, model: TestModel) -> TestModel:
    """Devuelve una copia del modelo con el elemento agregado. ValueError si no se puede (falta lo que referencia)."""
    model = model.model_copy(deep=True)
    pl = _payload(m)
    if pl.get("legacy"):
        raise ValueError("Este análisis es de una versión anterior: tocá «Volver a analizar» para poder agregar variantes.")
    if m["kind"] == "tag":
        if pl.get("tag") not in model.feature_tags:
            model.feature_tags.append(pl["tag"])
    elif m["kind"] == "parámetro" and pl.get("parameter"):
        p = Parameter.model_validate(pl["parameter"])
        acs = {a.id for a in model.acceptance_criteria}
        p.ac_refs = [a for a in p.ac_refs if a in acs]
        if any(x.name == p.name for x in model.parameters):
            raise ValueError(f"Ya existe un dato llamado {p.name}")
        model.parameters.append(p)
    elif m["kind"] == "elección" and pl.get("choice"):
        p = next((p for p in model.parameters if p.name == pl.get("param")), None)
        if p is None:
            raise ValueError("El dato al que pertenece esta variante no está en el modelo: agregá primero el dato.")
        c = Choice.model_validate(pl["choice"])
        if any(x.name == c.name for x in p.choices):
            c = c.model_copy(update={"name": f"{c.name}_2"})
        p.choices.append(c)
        p.choices.sort(key=lambda x: x.kind != "valid")
    elif m["kind"] == "restricción" and pl.get("constraint"):
        c = Constraint.model_validate(pl["constraint"])
        names = {p.name: {x.name for x in p.choices} for p in model.parameters}
        refs = [*c.if_choice.items(), *((p, v) for p, vs in c.forbids.items() for v in vs)]
        missing = [f"{p}={v}" for p, v in refs if v not in names.get(p, set())]
        if missing:
            raise ValueError(f"La combinación menciona variantes que no están en el modelo: {', '.join(missing)}")
        model.constraints.append(c)
    else:
        raise ValueError("Elemento desconocido")
    return model
