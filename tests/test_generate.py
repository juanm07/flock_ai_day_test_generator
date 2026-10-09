"""Generación determinista: BVA, pairwise, category-partition, riesgo, cobertura."""

from itertools import product

from tbg import modelcheck, pipeline
from tbg.generate import bva, pairwise
from tbg.schemas import Bounds, Constraint


def test_bva_8_to_64_gives_exact_boundaries():
    values = bva.boundary_values(Bounds(min=8, max=64, origin="PO"))
    assert [(v.value, v.valid) for v in values] == [
        (7, False), (8, True), (9, True), (63, True), (64, True), (65, False)]
    assert bva.concrete(values[0], "chars") == "'Abcdefg' (7 caracteres)"


def test_bva_never_produces_negative_lengths():
    values = bva.boundary_values(Bounds(min=0, max=3, origin="HU"))
    assert [v.value for v in values] == [0, 1, 2, 3, 4]


def test_pairwise_covers_all_pairs_with_fewer_rows_and_respects_constraints():
    dims = [("formato", ["csv", "xlsx", "pdf"]), ("rango", ["dia", "mes", "anio"]),
            ("moneda", ["ARS", "USD"]), ("cuenta", ["ahorro", "corriente"])]

    def forbidden(p1, v1, p2, v2):
        return {(p1, v1), (p2, v2)} == {("formato", "pdf"), ("rango", "anio")}

    rows = pairwise.generate(dims, forbidden)
    covered, total = pairwise.pair_coverage(rows, dims, forbidden)
    assert covered == total
    assert len(rows) < len(list(product(*[v for _, v in dims])))  # 36 combinaciones
    assert not any(r["formato"] == "pdf" and r["rango"] == "anio" for r in rows)


def test_generation_is_deterministic(story, model):
    a = pipeline.build(story, model).model_dump_json()
    b = pipeline.build(story, model).model_dump_json()
    assert a == b


def test_hu101_frames(story, model):
    assert not [i for i in modelcheck.check(model, story) if i.level == "error"]
    fs = pipeline.build(story, model)
    assert fs.mode == "completo"
    assert [f.case_id for f in fs.frames] == [f"CP-{i:03d}" for i in range(1, len(fs.frames) + 1)]
    assert fs.coverage.ac_percent == 100.0 and fs.coverage.pairs_percent == 100.0
    assert any(f.smoke for f in fs.frames)
    # particiones asumidas o sin esperado definido → el frame exige [SUPUESTO]
    unicode = next(f for f in fs.frames if f.bindings.get("password_nueva") == "unicode")
    assert unicode.supuestos
    # subsunción: no queda un frame solo-CA-3 con unicode si existe el de CA-3+CA-4
    assert sum(1 for f in fs.frames if f.bindings.get("password_nueva") == "unicode" and f.type == "Funcional") == 1
    # reglas de seguridad presentes y priorizadas alto
    enum = next(f for f in fs.frames if f.origin == "rule:auth.enumeration")
    assert enum.impact == "Alto" and enum.priority == "Alta" and not enum.supuestos  # la HU lo define


def test_answering_bounds_adds_boundary_frames_and_keeps_other_ids(story, model):
    before = {f.frame_id for f in pipeline.build(story, model).frames}
    next(p for p in model.parameters if p.name == "password_nueva").bounds = Bounds(min=8, max=64, origin="PO")
    fs = pipeline.build(story, model)
    after = {f.frame_id for f in fs.frames}
    assert before < after  # los frames existentes conservan su id → la redacción previa se reutiliza
    borde = [f for f in fs.frames if f.type == "Borde"]
    assert len(borde) == 2 and fs.coverage.boundaries_covered == fs.coverage.boundaries_total == 6


def test_model_check_rejects_invented_quotes_and_unknown_tags(story, model):
    model.feature_tags.append("blockchain")
    model.acceptance_criteria[1].text = "El sistema envía un SMS con un código."
    model.parameters[0].choices[0].quote = "el sistema bloquea la cuenta"
    model.constraints.append(Constraint(if_choice={"email_solicitud": "nope"}, forbids={}, reason="x"))
    errors = [i.path for i in modelcheck.check(model, story) if i.level == "error"]
    assert "feature_tags" in errors
    assert any(p.startswith("acceptance_criteria[1]") for p in errors)
    assert any("choices[0]" in p for p in errors)
    assert any(p.startswith("constraints") for p in errors)
