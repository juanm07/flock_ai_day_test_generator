"""Evaluación del flujo B contra el golden del dataset.

Para cada eval/dataset/golden/bug-*.yaml busca la extracción del agente en eval/runs/bugs/<BUG>/facts.json
(hecha con AGENTS.md, Flujo B, paso 2), corre `tbg bug-check` y compara:
  - severidad (valor y si es preliminar) vs `severidad_esperada` / `preliminar`
  - faltantes críticos detectados vs `faltantes_criticos` (precisión y recall)
  - hechos rechazados por cita inexistente (alucinaciones atrapadas)

Uso: python eval/evaluate_bugs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tbg import bug  # noqa: E402
from tbg.schemas import BugFacts  # noqa: E402


def main() -> None:
    rows = []
    for g_path in sorted((ROOT / "eval/dataset/golden").glob("bug-*.yaml")):
        g = yaml.safe_load(g_path.read_text(encoding="utf-8"))
        bid = g["bug"]
        facts = ROOT / "eval/runs/bugs" / bid / "facts.json"
        report = ROOT / "eval/dataset/bugs" / f"{bid}.md"
        if not facts.exists():
            rows.append((bid, None))
            continue
        bc = bug.check(BugFacts.model_validate_json(facts.read_text(encoding="utf-8")), report.read_text(encoding="utf-8"))
        got = {m["field"] for m in bc.missing if m["critical"]}
        exp = set(g.get("faltantes_criticos") or [])
        rows.append((bid, {
            "sev_ok": bc.severity.value == g["severidad_esperada"],
            "prelim_ok": (not bc.severity.firm) == bool(g.get("preliminar")),
            "sev": f"{bc.severity.value}{'' if bc.severity.firm else '*'} vs {g['severidad_esperada']}{'*' if g.get('preliminar') else ''}",
            "falt_recall": len(got & exp) / len(exp) if exp else 1.0,
            "falt_prec": len(got & exp) / len(got) if got else 1.0,
            "rechazados": len(bc.rejected),
        }))
    done = [r for _, r in rows if r]
    if not done:
        print("No hay extracciones en eval/runs/bugs/<BUG>/facts.json todavía.")
        return
    n = len(done)
    print(f"Bugs evaluados: {n}/{len(rows)} · severidad exacta {sum(r['sev_ok'] for r in done)}/{n} · "
          f"firme/preliminar correcto {sum(r['prelim_ok'] for r in done)}/{n} · "
          f"faltantes críticos recall {sum(r['falt_recall'] for r in done) / n:.0%} precisión {sum(r['falt_prec'] for r in done) / n:.0%}")
    print("\n| Bug | Severidad (tbg vs golden, * = preliminar) | Faltantes R/P | Citas rechazadas |\n|---|---|---|---|")
    for bid, r in rows:
        print(f"| {bid} | " + (f"{r['sev']} | {r['falt_recall']:.0%}/{r['falt_prec']:.0%} | {r['rechazados']} |" if r else "sin extracción | — | — |"))


if __name__ == "__main__":
    main()
