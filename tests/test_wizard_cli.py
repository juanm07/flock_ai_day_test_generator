"""Asistente guiado y CLI completo (sin LLM: entradas simuladas)."""

import json

import pytest
from typer.testing import CliRunner

from tbg.cli import app

from .conftest import ROOT

runner = CliRunner()


@pytest.fixture
def env(tmp_path, monkeypatch):
    for var in ("TBG_LLM", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("TBG_WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setenv("TBG_CONFIG", str(tmp_path / "cfg.json"))
    return tmp_path


def test_every_cli_command_loads():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    for cmd in ("asistente", "ui", "lint-hu", "generate", "validate", "export", "brief", "import-suite", "bug-check"):
        assert cmd in r.output


def test_wizard_hu_answers_po_and_exports(env, monkeypatch, model):
    from tbg import flows, llm, workspace

    def fake_analyze(sid):  # simula las 3 lecturas de la IA con el modelo de referencia
        workspace.HUSpace(sid).save_model(model)

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(flows, "analyze_with_ai", fake_analyze)
    hu = ROOT / "ejemplos" / "hu-101.md"
    # s: interpretación ok · s: analizar con IA · s: responder ahora · P-1: mín 8, máx 64, Enter · P-2: d (default) ·
    # resto Enter · 2: paquete para otra IA · Enter: importar después
    answers = "s\ns\ns\n8\n64\n\nd\n" + "\n" * 6 + "2\n\n"
    r = runner.invoke(app, ["asistente", str(hu), "--hu", "-o", str(env / "salidas")], input=answers)
    assert r.exit_code == 0, r.output
    assert "1 respuesta, 1 límite" in r.output
    out = env / "salidas" / "HU-101"
    assert (out / "HU-101_para_redactar.md").exists() and (out / "HU-101_casos_disenados.md").exists()
    assert "valores límite 6/6" in r.output


def test_wizard_bug_with_another_ai_answer(env):
    report = ROOT / "ejemplos" / "reporte-001.md"
    answer = env / "respuesta.json"
    answer.write_text("Acá va:\n```json\n" + (ROOT / "ejemplos" / "reporte-001.facts.json").read_text(encoding="utf-8")
                      + "\n```", encoding="utf-8")
    r = runner.invoke(app, ["asistente", str(report), "--bug", "-o", str(env / "salidas")], input=f"{answer}\n")
    assert r.exit_code == 0, r.output
    assert "Severidad S2 (preliminar)" in r.output and "pérdida de datos → S1" in r.output
    assert list((env / "salidas").glob("BUG-*/bug_normalizado_*.md"))


def test_cli_brief_and_import_suite_roundtrip(env):
    w = env / "w"
    w.mkdir()
    r = runner.invoke(app, ["generate", str(ROOT / "ejemplos/hu-101.model.json"), "--hu", str(ROOT / "ejemplos/hu-101.md"),
                            "-o", str(w / "frames.json")])
    assert r.exit_code == 0, r.output
    r = runner.invoke(app, ["brief", "--frames", str(w / "frames.json"), "--hu", str(ROOT / "ejemplos/hu-101.md"),
                            "-o", str(w / "paquete.md")])
    assert r.exit_code == 0 and "## Casos a redactar (16)" in (w / "paquete.md").read_text(encoding="utf-8")
    r = runner.invoke(app, ["import-suite", str(ROOT / "ejemplos/hu-101.suite.json"), "--frames", str(w / "frames.json"),
                            "--suite", str(w / "suite.json")])
    assert r.exit_code == 0 and "Gate APROBADO" in r.output
    assert len(json.loads((w / "suite.json").read_text(encoding="utf-8"))["cases"]) == 16
