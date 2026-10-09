"""Export a Gherkin y a steps de Playwright."""

import re

from tbg import export, pipeline
from tbg.schemas import Bounds, CaseDraft, Step, SuiteDraft

from .conftest import ROOT


def _suite():
    return SuiteDraft.model_validate_json((ROOT / "ejemplos" / "hu-101.suite.json").read_text(encoding="utf-8"))


def test_gherkin_has_one_scenario_per_drafted_case_with_traceability(story, model):
    fs = pipeline.build(story, model)
    g = export.to_gherkin(fs, _suite())
    assert g.startswith("# language: es")
    assert len(re.findall(r"^\s+Escenario:", g, re.M)) == len(fs.frames)
    assert "@CP-001 @HU-101 @CA-1 @CA-2 @funcional @prioridad-alta @humo" in g
    assert "[SUPUESTO" not in "\n".join(l for l in g.splitlines() if not l.strip().startswith("#"))
    assert "F-" not in g.replace("# ", "")  # referencias a frames traducidas a CP-NNN


def test_boundary_frames_become_scenario_outlines_with_exact_values(story, model):
    next(p for p in model.parameters if p.name == "password_nueva").bounds = Bounds(min=8, max=64, origin="PO")
    fs = pipeline.build(story, model)
    suite = _suite()
    for f in fs.frames:
        if f.type == "Borde":
            suite.cases.append(CaseDraft(frame_id=f.frame_id, title=f"Verificar el {f.title_hint.lower()}",
                                         preconditions="Enlace de recuperación vigente abierto",
                                         steps=[Step(action="Ingresar cada valor", expected="Resultado según la tabla")],
                                         evidence="-"))
    g = export.to_gherkin(fs, suite)
    assert g.count("Esquema del escenario:") == 2
    rows = re.findall(r"^\s+\| (máx\+1|mín-1) \| [^|]+ \| (\S+) \| (\w+) \|$", g, re.M)
    assert ("mín-1", "Abcdefg", "rechazado") in rows
    assert ("máx+1", ("Abcdefgh12" * 7)[:65], "rechazado") in rows


def test_playwright_steps_are_unique_and_parametrized(story, model):
    g = export.to_gherkin(pipeline.build(story, model), _suite())
    ts = export.to_playwright_steps(g)
    steps = re.findall(r"^(Given|When|Then)\('(.*)', async", ts, re.M)
    assert len(steps) == len({s for _, s in steps})
    assert ("Then", "se muestra exactamente {string}") in steps
    assert "async ({ page }, arg1: string)" in ts


def test_brief_lists_only_pending_cases_and_import_roundtrip(story, model):
    import json as _json
    fs = pipeline.build(story, model)
    full = _suite()
    partial = SuiteDraft(story_id=full.story_id, cases=full.cases[:3])
    brief = export.drafting_brief(story.text, fs, partial)
    pending = _json.loads(brief.split("```json")[1].split("```")[0])
    assert len(pending) == len(fs.frames) - 3 and "Respondé SOLO con un bloque JSON" in brief

    # la "otra IA" responde con texto alrededor, un caso inventado y uno roto
    answer = {"cases": [c.model_dump() for c in full.cases[3:]] + [
        {**full.cases[0].model_dump(), "frame_id": "F-00000000"}, {"frame_id": fs.frames[5].frame_id}]}
    text = "¡Listo! Acá están:\n```json\n" + _json.dumps(answer, ensure_ascii=False) + "\n```\nSaludos."
    suite, notes = export.import_drafts(text, fs, partial)
    assert len(suite.cases) == len(fs.frames)
    assert any("F-00000000" in n for n in notes) and any("formato inválido" in n for n in notes)
    from tbg.validate import validate
    assert validate(fs, suite).ok


def test_designed_cases_markdown_needs_no_drafting(story, model):
    md = export.frames_markdown(pipeline.build(story, model))
    assert md.startswith("# Casos diseñados — HU-101") and "[SUPUESTO]" in md and "CP-016" in md
