"""El gate de calidad detecta las fallas típicas de redacción de un LLM."""

import pytest

from tbg import pipeline
from tbg.schemas import CaseDraft, Step, SuiteDraft
from tbg.validate import validate

from .conftest import ROOT


@pytest.fixture
def fs(story, model):
    return pipeline.build(story, model)


@pytest.fixture
def suite():
    return SuiteDraft.model_validate_json((ROOT / "ejemplos" / "hu-101.suite.json").read_text(encoding="utf-8"))


def failed(report):
    return {c.id for c in report.checks if not c.passed and c.critical}


def case(suite, fs, origin):
    fid = next(f.frame_id for f in fs.frames if f.origin == origin)
    return next(c for c in suite.cases if c.frame_id == fid)


def test_reference_suite_passes(fs, suite):
    report = validate(fs, suite)
    assert report.ok, [(c.id, c.details) for c in report.checks if not c.passed]


def test_vague_expected_result_fails_c4(fs, suite):
    suite.cases[0].steps[0].expected = "El formulario funciona correctamente"
    assert failed(validate(fs, suite)) == {"C4"}


def test_compound_action_fails_c3(fs, suite):
    suite.cases[0].steps[1].action = "Ingresar qa.usuario01@empresa.com y confirmar"
    assert failed(validate(fs, suite)) == {"C3"}


def test_missing_supuesto_marker_fails_c2(fs, suite):
    c = case(suite, fs, "rule:token.expiration")
    for s in c.steps:
        s.expected = s.expected.split(" [SUPUESTO")[0]
    assert failed(validate(fs, suite)) == {"C2"}


def test_changed_or_abstract_data_fails_c5(fs, suite):
    c = suite.cases[0]
    for s in c.steps:
        s.action = s.action.replace("qa.usuario01@empresa.com", "un email válido")
    c.preconditions = c.preconditions.replace("qa.usuario01@empresa.com", "otro@empresa.com")
    assert failed(validate(fs, suite)) == {"C5"}


def test_invented_or_missing_cases_fail_c1(fs, suite):
    suite.cases.pop()
    suite.cases.append(CaseDraft(frame_id="F-deadbeef", title="Verificar algo extra", preconditions="-",
                                 steps=[Step(action="Tocar X", expected="Se muestra Y")], evidence="-"))
    report = validate(fs, suite)
    assert failed(report) == {"C1"}
    details = next(c for c in report.checks if c.id == "C1").details
    assert any("F-deadbeef" in d for d in details) and any("sin redactar" in d for d in details)
