"""Formulario del PO: generación y aplicación determinista de respuestas y límites."""

import pytest
import yaml

from tbg import pipeline
from tbg.po import apply_form, build_form


@pytest.fixture
def ctx(story, model):
    m = pipeline.with_suggested_tags(story, model)
    _, _, gaps = pipeline.analyze(story, m)
    return m, gaps


def _fill(form: str, gap_id: str, **fields) -> str:
    data = yaml.safe_load(form)
    item = next(q for q in data["preguntas"] if q["id"] == gap_id)
    for k, v in fields.items():
        if k == "limites":
            for p, spec in v.items():
                item["limites"][p].update(spec)
        else:
            item[k] = v
    return yaml.safe_dump(data, allow_unicode=True)


def test_form_is_valid_yaml_with_structured_bounds(ctx):
    m, gaps = ctx
    data = yaml.safe_load(build_form(m, gaps))
    ids = [q["id"] for q in data["preguntas"]]
    assert ids == [g.id for g in gaps if g.asked]
    policy = next(q for q in data["preguntas"] if q["id"] == "credential.policy")
    assert policy["limites"] == {"password_nueva": {"unidad": "chars", "min": None, "max": None}}


def test_bounds_from_form_enable_boundary_cases(story, ctx):
    m, gaps = ctx
    form = _fill(build_form(m, gaps), "credential.policy", limites={"password_nueva": {"min": 10, "max": 64}})
    res = apply_form(form, m, gaps)
    assert res.bounds == ["password_nueva: 10–64 chars"]
    fs = pipeline.build(story, m)
    values = {k for f in fs.frames if f.type == "Borde" for k in f.data if k.startswith("password_nueva [")}
    assert len(values) == 6 and fs.coverage.boundaries_percent == 100.0


def test_accepted_default_applies_default_bounds_and_closes_gap(story, ctx):
    m, gaps = ctx
    apply_form(_fill(build_form(m, gaps), "credential.policy", acepto_default=True), m, gaps)
    p = next(p for p in m.parameters if p.name == "password_nueva")
    assert (p.bounds.min, p.bounds.max, p.bounds.origin) == (8, 64, "PO")
    _, _, after = pipeline.analyze(story, m)
    assert next(g for g in after if g.id == "credential.policy").status == "answered"


def test_free_text_answer_removes_supuesto_from_rule_frame(story, ctx):
    m, gaps = ctx
    apply_form(_fill(build_form(m, gaps), "token.expiration", respuesta="1 hora"), m, gaps)
    frame = next(f for f in pipeline.build(story, m).frames if f.origin == "rule:token.expiration")
    assert not frame.supuestos and "Según respuesta: 1 hora" in frame.expected_hints


def test_changing_bounds_changes_boundary_frame_ids(story, ctx):
    m, gaps = ctx
    form = build_form(m, gaps)
    apply_form(_fill(form, "credential.policy", limites={"password_nueva": {"min": 8, "max": 64}}), m, gaps)
    ids_8 = {f.frame_id for f in pipeline.build(story, m).frames if f.type == "Borde"}
    apply_form(_fill(form, "credential.policy", limites={"password_nueva": {"min": 10, "max": 64}}), m, gaps)
    ids_10 = {f.frame_id for f in pipeline.build(story, m).frames if f.type == "Borde"}
    assert len(ids_8 & ids_10) == 1  # el límite superior no cambió; el inferior es otro caso


@pytest.mark.parametrize("limits,msg", [({"min": 64, "max": 8}, "min"), ({"min": "ocho"}, "números")])
def test_invalid_bounds_are_rejected(ctx, limits, msg):
    m, gaps = ctx
    form = _fill(build_form(m, gaps), "credential.policy", limites={"password_nueva": limits})
    with pytest.raises(ValueError, match=msg):
        apply_form(form, m, gaps)
