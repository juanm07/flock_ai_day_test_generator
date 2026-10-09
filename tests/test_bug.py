"""Flujo B: anti-alucinación por citas, faltantes y clasificación por reglas."""

import pytest

from tbg import bug
from tbg.schemas import BugFacts, Fact, Feature

from .conftest import ROOT


@pytest.fixture
def report():
    return (ROOT / "ejemplos" / "reporte-001.md").read_text(encoding="utf-8")


@pytest.fixture
def facts():
    return BugFacts.model_validate_json((ROOT / "ejemplos" / "reporte-001.facts.json").read_text(encoding="utf-8"))


def test_reference_extraction_matches_calibration(facts, report):
    bc = bug.check(facts, report)
    assert bc.ok and not bc.rejected
    assert (bc.severity.value, bc.severity.firm, bc.severity.conditions) == ("S2", False, {"data_loss": "S1"})
    assert bc.priority.value == "P2"
    missing = {m["field"] for m in bc.missing if m["critical"]}
    assert missing == {"expected", "error_text", "app_version"}
    assert "environment.platform" in bc.hedged  # "la última versión creo"


def test_injected_facts_are_rejected(facts, report):
    facts.environment.app_version = Fact(text="v2.3.1", quote="estoy en la versión 2.3.1")
    facts.features.data_loss = Feature(value=True, quote="se borraron mis datos")
    bc = bug.check(facts, report)
    assert not bc.ok
    paths = {r.path for r in bc.rejected}
    assert {"environment.app_version", "features.data_loss"} <= paths
    # una feature sin respaldo no puede subir la severidad
    assert bc.severity.value == "S2"
    assert any(m["field"] == "app_version" for m in bc.missing)


def test_feature_without_quote_is_ignored(facts, report):
    facts.features.security = Feature(value=True, quote=None)
    bc = bug.check(facts, report)
    assert bc.features["security"] is None and not bc.ok


@pytest.mark.parametrize("feats,expected", [
    ({"data_loss": True}, "S1"),
    ({"blocks_critical_flow": True, "workaround_exists": False, "affects_subset_only": False}, "S1"),
    ({"blocks_critical_flow": True, "workaround_exists": True}, "S2"),
    ({"cosmetic_only": True}, "S4"),
    ({"cosmetic_only": True, "security": True}, "S2"),  # piso de seguridad
    ({}, "S3"),
])
def test_severity_rules_follow_taxonomy(feats, expected, report):
    b = BugFacts(symptom=Fact(text="x", quote="login"))
    for k, v in feats.items():
        setattr(b.features, k, Feature(value=v, quote="login"))
    for k in ("data_loss", "security", "blocks_critical_flow", "workaround_exists", "affects_subset_only", "cosmetic_only"):
        if k not in feats:
            setattr(b.features, k, Feature(value=False, quote="login"))
    bc = bug.check(b, report)
    assert bc.severity.value == expected and bc.severity.firm


def test_regression_raises_priority(facts, report):
    facts.features.regression = Feature(value=True, quote="esa contraseña la uso hace meses")
    assert bug.check(facts, report).priority.value == "P1"
