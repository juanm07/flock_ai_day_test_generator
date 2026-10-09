"""Operaciones de punta a punta compartidas por la app web y el asistente de terminal (`tbg asistente`).

Cada función trabaja sobre work/<ID>/ (workspace), así lo que se hace en una interfaz se ve en la otra.
"""

from __future__ import annotations

import json
import re

from . import ai, bug, export, llm, minorities, pipeline, po, workspace
from .hu import parse_story
from .schemas import AcceptanceCriterion, BugFacts, FrameSet, TestModel
from .validate import Report, validate

_HEADING_ID = re.compile(r"^(#{1,6}\s*)[A-Z][A-Z0-9]{0,9}-[A-Z]?\d+", re.M)


# ---------------------------------------------------------------------------- HU


def create_hu(text: str) -> tuple[str, list[str]]:
    """Guarda una HU pegada en cualquier formato. Devuelve (ID, avisos)."""
    fallback = workspace.next_id("HU")
    try:
        md, warns = ai.normalize_hu(text, fallback)
    except llm.LLMError as e:
        md, warns = ai.with_heading(text, parse_story(text), fallback), [str(e)]
    sid = parse_story(md).id
    if sid == "HU-000" or (workspace.root() / sid).exists():  # sin ID o ID ya usado: se le asigna uno nuevo
        md = _HEADING_ID.sub(lambda m: m.group(1) + fallback, md, count=1)
        if parse_story(md).id != fallback:
            md = f"## {fallback} — {parse_story(md).title}\n\n{md}"
        sid = fallback
    workspace.HUSpace(sid).save_hu(md)
    return sid, warns


def analyze_with_ai(sid: str):
    """3 lecturas independientes + consenso. Lanza llm.LLMError si la IA falla."""
    space = workspace.HUSpace(sid)
    models, result = ai.extract_with_consensus(space.story())
    for k, m in enumerate(models, 1):
        space.save_extraction(k, m)
    space.save_model(result.model)
    (space.dir / "consensus.json").write_text(json.dumps(
        {"n": result.n, "agreement": result.agreement, "minorities": [m.__dict__ for m in result.minorities]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def basic_model(sid: str) -> TestModel:
    """Seguir sin IA: criterios literales, sin datos/variantes. ValueError si la HU no tiene criterios."""
    space = workspace.HUSpace(sid)
    story = space.story()
    if not story.acceptance_criteria:
        raise ValueError("La historia no tiene criterios de aceptación detectables: editala primero.")
    model = TestModel(story_id=story.id, title=story.title, module=story.title, role=story.role or "usuario",
                      want=story.want or story.title, so_that=story.so_that,
                      acceptance_criteria=[AcceptanceCriterion(id=a, text=x) for a, x in story.acceptance_criteria])
    space.save_model(model)
    return model


def pending_minorities(sid: str) -> list[tuple[int, dict, str]]:
    space = workspace.HUSpace(sid)
    path, model = space.dir / "consensus.json", space.model()
    if not (path.exists() and model):
        return []
    items = json.loads(path.read_text(encoding="utf-8")).get("minorities", [])
    return [(i, m, minorities.describe(m, model)) for i, m in enumerate(items) if not minorities.present(m, model)]


def add_minority(sid: str, index: int) -> None:
    space = workspace.HUSpace(sid)
    items = json.loads((space.dir / "consensus.json").read_text(encoding="utf-8")).get("minorities", [])
    space.save_model(minorities.apply(items[index], space.model()))
    _refresh_frames(sid)


def questions(sid: str):
    """(modelo con tags sugeridos, lagunas). Las preguntas al PO son las `asked`."""
    space = workspace.HUSpace(sid)
    model = pipeline.with_suggested_tags(space.story(), space.model())
    _, _, gaps = pipeline.analyze(space.story(), model)
    return model, gaps


def apply_answers(sid: str, data: dict) -> po.Applied:
    """data = {"preguntas": [{id, respuesta, acepto_default, limites}]} (mismo contrato que el formulario del PO)."""
    space = workspace.HUSpace(sid)
    original = space.model()
    model, gaps = questions(sid)
    data = {"story_id": original.story_id, **data}
    res = po.apply_data(data, model, gaps)
    model.feature_tags = original.feature_tags
    space.save_model(model)
    _refresh_frames(sid)
    return res


def design(sid: str) -> FrameSet:
    space = workspace.HUSpace(sid)
    fs = pipeline.build(space.story(), space.model())
    space.save_frames(fs)
    return fs


def _refresh_frames(sid: str) -> None:
    if workspace.HUSpace(sid).frames_path.exists():
        design(sid)


def draft_with_ai(sid: str) -> Report:
    space = workspace.HUSpace(sid)
    suite = ai.draft_cases(space.story(), space.frames(), space.suite())
    space.save_suite(suite)
    return validate(space.frames(), suite)


def brief(sid: str) -> str:
    space = workspace.HUSpace(sid)
    return export.drafting_brief(space.hu_path.read_text(encoding="utf-8"), space.frames(), space.suite())


def import_answer(sid: str, text: str) -> tuple[Report, list[str]]:
    space = workspace.HUSpace(sid)
    suite, notes = export.import_drafts(text, space.frames(), space.suite())
    space.save_suite(suite)
    return validate(space.frames(), suite), notes


def export_all(sid: str, out_dir) -> list[str]:
    """Escribe en out_dir todo lo exportable según el estado. Devuelve las rutas escritas."""
    from .render import render_suite

    space = workspace.HUSpace(sid)
    fs, suite = space.frames(), space.suite()
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    def w(name: str, body: str) -> None:
        (out_dir / name).write_text(body, encoding="utf-8")
        written.append(str(out_dir / name))

    if fs:
        w(f"{sid}_casos_disenados.md", export.frames_markdown(fs))
    if fs and suite:
        report = validate(fs, suite)
        w(f"suite_{sid}.md", render_suite(fs, space.model(), suite, report))
        feature = export.to_gherkin(fs, suite)
        w(f"{sid}.feature", feature)
        w(f"{sid}.steps.ts", export.to_playwright_steps(feature))
    return written


# ---------------------------------------------------------------------------- bugs


def create_bug(text: str) -> str:
    bid = workspace.next_id("BUG")
    workspace.BugSpace(bid).save_report(text)
    return bid


def analyze_bug_with_ai(bid: str) -> bug.BugCheck:
    space = workspace.BugSpace(bid)
    space.save_facts(ai.extract_bug(space.report(), bid))
    return bug.check(space.facts(), space.report())


def bug_brief(bid: str) -> str:
    space = workspace.BugSpace(bid)
    return "\n".join([
        f"# Extraer hechos de un reporte de bug — {bid}", "",
        "Copiá TODO este archivo en tu IA y guardá su respuesta (el JSON) para importarla con la app o el asistente.", "",
        "## Instrucciones", "", ai._bug_system(), "", "## Reporte original", "", space.report().strip(), ""])


def import_bug_facts(bid: str, text: str) -> bug.BugCheck:
    space = workspace.BugSpace(bid)
    try:
        data = ai._json(text)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"La respuesta no contiene un JSON válido ({e}).") from e
    facts = BugFacts.model_validate({**data, "bug_id": bid})
    space.save_facts(facts)
    return bug.check(facts, space.report())


