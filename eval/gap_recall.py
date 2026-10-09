"""Recall y precisión de lagunas SIN LLM: las preguntas al PO de `tbg` salen solo del texto de la HU + reglas,
así que se pueden evaluar sobre cientos de HUs en segundos.

  recall    = lagunas golden cubiertas por alguna pregunta / lagunas golden
  precisión = 1 - (temas `no_preguntar` que igual se preguntaron / temas `no_preguntar`)   (si el golden los trae)

Fuentes: eval/golden/*.gaps.yaml (HU en ejemplos/<id>.md) y eval/dataset/golden/hu-*.gaps.yaml (campo hu_file).
Uso: python eval/gap_recall.py [--detalle]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tbg import pipeline  # noqa: E402
from tbg.hu import load_story  # noqa: E402


def _hit(terms: list[str], text: str) -> bool:
    return any(re.search(t, text, re.I) for t in terms)


def evaluate(golden_path: Path) -> dict:
    g = yaml.safe_load(golden_path.read_text(encoding="utf-8"))
    hu = ROOT / (g.get("hu_file") or f"ejemplos/{g['story'].lower()}.md")
    story = load_story(hu)
    _, _, gaps = pipeline.analyze(story)
    asked = [x for x in gaps if x.asked]
    text = "\n".join(f"{x.question} {x.why} {x.default}" for x in asked)
    hits = [x["id"] for x in g["gaps"] if _hit(x["match"], text)]
    fps = [x["id"] for x in g.get("no_preguntar") or [] if _hit(x["match"], text)]
    return {"story": g["story"], "dominio": g.get("dominio", "—"), "tipo": g.get("tipo", "—"),
            "golden": len(g["gaps"]), "hits": hits, "missed": [x["id"] for x in g["gaps"] if x["id"] not in hits],
            "no_preguntar": len(g.get("no_preguntar") or []), "falsos_positivos": fps, "preguntas": len(asked)}


def main(detail: bool) -> None:
    paths = sorted((ROOT / "eval/golden").glob("*.gaps.yaml")) + sorted((ROOT / "eval/dataset/golden").glob("hu-*.gaps.yaml"))
    rows = [evaluate(p) for p in paths]
    tot_g = sum(r["golden"] for r in rows)
    tot_h = sum(len(r["hits"]) for r in rows)
    tot_np = sum(r["no_preguntar"] for r in rows)
    tot_fp = sum(len(r["falsos_positivos"]) for r in rows)
    print(f"HUs: {len(rows)} · recall micro: {tot_h}/{tot_g} = {tot_h / tot_g:.0%}"
          + (f" · precisión (no_preguntar): {1 - tot_fp / tot_np:.0%} ({tot_fp} falsos positivos de {tot_np})" if tot_np else ""))
    print("\n| HU | Dominio | Tipo | Recall | Preguntas | No detectadas | Falsos positivos |\n|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['story']} | {r['dominio']} | {r['tipo']} | {len(r['hits'])}/{r['golden']} | {r['preguntas']} | "
              f"{', '.join(r['missed']) or '—'} | {', '.join(r['falsos_positivos']) or '—'} |")
    if detail:
        missed = sorted({m for r in rows for m in r["missed"]})
        print("\nLagunas no detectadas (candidatas a nuevas reglas en rules/gaps.yaml):", ", ".join(missed) or "ninguna")


if __name__ == "__main__":
    main("--detalle" in sys.argv)
