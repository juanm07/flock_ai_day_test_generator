"""Render determinista de los entregables markdown (las plantillas del equipo viven en templates/)."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .schemas import FrameSet, SuiteDraft, TestModel
from .validate import Report

_TEMPLATES = Path(__file__).parent / "templates"
_PRIO = {"Alta": 0, "Media": 1, "Baja": 2}


def render_bug(bc, report_text: str) -> str:
    return env().get_template("bug.md.j2").render(
        b=bc.facts, bc=bc, report=report_text, hedged=bc.hedged, rejected_paths={r.path for r in bc.rejected},
        missing_by_field={m["field"]: m for m in bc.missing},
        unknown=[k for k, v in bc.features.items() if v is None],
    )


def env() -> Environment:
    return Environment(loader=FileSystemLoader(_TEMPLATES), undefined=StrictUndefined, keep_trailing_newline=True,
                       trim_blocks=False, lstrip_blocks=False)


def _cell(s: str, ids: dict[str, str]) -> str:
    s = re.sub(r"\bF-[0-9a-f]{8}\b", lambda m: ids.get(m.group(0), m.group(0)), s)  # frame_id estable → CP-NNN
    return s.replace("|", "\\|").replace("\n", " ")


def render_suite(fs: FrameSet, model: TestModel, suite: SuiteDraft, report: Report) -> str:
    drafts = {c.frame_id: c for c in suite.cases}
    ids = {f.frame_id: f.case_id for f in fs.frames}
    cases = []
    for f in fs.frames:
        d = drafts.get(f.frame_id)
        if d is None:
            continue
        d = d.model_copy(deep=True)
        d.title, d.preconditions, d.evidence, d.notes = (_cell(x, ids) for x in (d.title, d.preconditions, d.evidence, d.notes))
        for s in d.steps:
            s.action, s.expected = _cell(s.action, ids), _cell(s.expected, ids)
        cases.append({"frame": f, "draft": d})

    asked = [g for g in fs.gaps if g.asked]
    pid = {g.id: f"P-{i}" for i, g in enumerate(asked, 1)}
    questions = [{"pid": pid[g.id], "gap": g} for g in asked]
    resolved = [g for g in fs.gaps if g.status != "open"]
    silent = [g for g in fs.gaps if g.status == "open" and not g.asked
              and not any(g.id in s for f in fs.frames for s in f.supuestos)]

    sup: dict[str, list[str]] = {}
    for f in fs.frames:
        for s in f.supuestos:
            for gid, p in pid.items():  # referencias legibles: "ver token.expiration" → "ver P-2"
                s = s.replace(f"ver {gid})", f"ver {p})")
            sup.setdefault(s, []).append(f.case_id)

    order = sorted(fs.frames, key=lambda f: (not f.smoke, _PRIO[f.priority], f.case_id))
    techniques = dict(sorted(Counter(f.origin.split(":")[0] for f in fs.frames).items()))
    return env().get_template("suite.md.j2").render(
        fs=fs, model=model, cases=cases, questions=questions, resolved=resolved, silent=silent,
        supuestos=list(sup.items()), order=[f.case_id for f in order], smoke=[f.case_id for f in fs.frames if f.smoke],
        report=report, techniques=techniques,
    )
