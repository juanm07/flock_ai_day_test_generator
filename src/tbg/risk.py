"""Priorización por riesgo (Amland 2000): prioridad = matriz[probabilidad][impacto], con reglas en rules/risk.yaml.

Cada prioridad trae su `risk_reason`: la justificación es parte de la salida, no una intuición.
"""

from __future__ import annotations

from . import rules
from .lint import match_any
from .schemas import Frame

_UP = {"Baja": "Media", "Media": "Alta", "Alta": "Alta"}


def assess(frames: list[Frame], feature_tags: list[str]) -> None:
    spec = rules.load("risk")
    gap_rules = {r["id"]: r for r in rules.load("gaps")["rules"]}
    critical = bool(set(feature_tags) & set(spec["critical_tags"]))

    smoke_budget = spec["max_smoke"]
    seen_ac: set[str] = set()
    for f in frames:
        if f.origin == "ac-happy-path" and smoke_budget > 0 and not set(f.ac_refs) <= seen_ac:
            f.smoke = True
            smoke_budget -= 1
            seen_ac |= set(f.ac_refs)

    for f in frames:
        prob = spec["probability_by_type"][f.type]
        why_p = [f"tipo {f.type}"]
        text = " ".join([f.title_hint, *f.bindings.values(), *f.data.values(), *f.expected_hints])
        for bump in spec["probability_bumps"]:
            hit = match_any(bump["match"], text)
            if hit:
                prob = _UP[prob]
                why_p.append(f"{bump['reason']} («{hit}»)")
                break

        impact = spec["impact_by_type"][f.type]["critical" if critical else "normal"]
        why_i = [f"tipo {f.type}" + (" en funcionalidad crítica" if critical else "")]
        if f.origin.startswith("rule:"):
            cat = gap_rules[f.origin[5:]]["category"]
            if cat in spec["high_impact_categories"]:
                impact = "Alto"
                why_i = [f"regla de {cat}"]

        prio = spec["matrix"][prob][impact]
        reason = f"Prob. {prob} ({'; '.join(why_p)}) × Impacto {impact} ({'; '.join(why_i)}) → {prio}"
        if f.smoke and prio != spec["smoke_priority"]:
            prio = spec["smoke_priority"]
            reason += f"; humo → {prio}"
        f.probability, f.impact, f.priority, f.risk_reason = prob, impact, prio, reason
