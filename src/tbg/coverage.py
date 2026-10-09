"""Cobertura calculada por código (y verificada de forma independiente al generador):
CA ↔ casos, pares 2-wise de elecciones válidas, valores límite.
"""

from __future__ import annotations

from .generate import bva, pairwise
from .generate.partition import ac_groups, make_forbidden, valid_dims
from .schemas import Coverage, CoverageRow, Frame, Gap, TestModel


def _pct(a: int, b: int) -> float:
    return round(100.0 * a / b, 1) if b else 100.0


def compute(model: TestModel, frames: list[Frame], gaps: list[Gap]) -> Coverage:
    rows = []
    blocking = [g for g in gaps if g.gap_class == "BLOQUEANTE" and g.status == "open"]
    for ac in model.acceptance_criteria:
        ids = [f.case_id for f in frames if ac.id in f.ac_refs]
        reason = "" if ids else ("Bloqueante: " + ", ".join(g.id for g in blocking) if blocking
                                 else "Ningún caso generado para este CA")
        rows.append(CoverageRow(ac_id=ac.id, text=ac.text, case_ids=ids, covered=bool(ids), reason=reason))

    forbidden = make_forbidden(model)
    pc = pt = 0
    for ac_id, params in ac_groups(model):
        dims = valid_dims(params)
        tested = [f.bindings for f in frames if f.type == "Funcional" and ac_id in f.ac_refs]
        c, t = pairwise.pair_coverage(tested, dims, forbidden)
        pc, pt = pc + c, pt + t

    bt = bc = 0
    for p in model.parameters:
        if not p.bounds:
            continue
        expected = {f"{p.name} [{v.label}]" for v in bva.boundary_values(p.bounds)}
        got = {k for f in frames if f.type == "Borde" for k in f.data}
        bt += len(expected)
        bc += len(expected & got)

    covered = sum(r.covered for r in rows)
    return Coverage(acceptance=rows, ac_percent=_pct(covered, len(rows)), pairs_total=pt, pairs_covered=pc,
                    pairs_percent=_pct(pc, pt), boundaries_total=bt, boundaries_covered=bc,
                    boundaries_percent=_pct(bc, bt))
