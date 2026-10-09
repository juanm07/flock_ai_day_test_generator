"""¿Cuánto varía la suite según la extracción del TestModel? Compara tres condiciones sobre la misma HU:

  A. extracción única, prompt v1 (AGENTS.md original)        → eval/runs/pipeline/<HU>/run-*/model.json
  B. extracción única, prompt v2 (prompts/extraer-modelo.md) → eval/runs/consensus/<HU>/ext-*/model.json
  C. consenso de 3 extracciones v2 (`tbg consensus`)          → grupos disjuntos de B: (1,2,3), (4,5,6), (7,8,9)

Para cada modelo se generan los frames con `tbg` (determinista) y se mide, entre todos los pares de la condición:
Jaccard de frame_id (identidad exacta del diseño), Jaccard de firmas semánticas (tipo × CAs × técnica) y
coeficiente de variación de la cantidad de frames. No interviene la redacción: aísla la varianza de extracción.

Uso: python eval/model_stability.py HU-202
"""

from __future__ import annotations

import itertools
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tbg import pipeline  # noqa: E402
from tbg.consensus import merge  # noqa: E402
from tbg.hu import load_story  # noqa: E402
from tbg.schemas import TestModel  # noqa: E402


def load(p: Path) -> TestModel:
    return TestModel.model_validate_json(p.read_text(encoding="utf-8"))


def jac_set(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 1.0


def jac_multi(a: Counter, b: Counter) -> float:
    u = sum((a | b).values())
    return sum((a & b).values()) / u if u else 1.0


def measure(story, models: list[TestModel]) -> dict:
    sets = [pipeline.build(story, m) for m in models]
    ids = [{f.frame_id for f in fs.frames} for fs in sets]
    sig = [Counter((f.type, tuple(f.ac_refs), f.origin.split(":")[0] if not f.origin.startswith("rule") else f.origin)
                   for f in fs.frames) for fs in sets]
    n = [len(fs.frames) for fs in sets]
    pairs = list(itertools.combinations(range(len(models)), 2))
    return {
        "modelos": len(models),
        "frames": n,
        "cv_frames": round(statistics.pstdev(n) / statistics.mean(n), 3),
        "jaccard_frame_id": round(statistics.mean(jac_set(ids[i], ids[j]) for i, j in pairs), 3),
        "jaccard_firmas": round(statistics.mean(jac_multi(sig[i], sig[j]) for i, j in pairs), 3),
        "parametros": [sorted(p.name for p in m.parameters) for m in models],
    }


def main(hu_id: str) -> None:
    story = load_story(ROOT / "ejemplos" / f"{hu_id.lower()}.md")
    a = [load(p) for p in sorted((ROOT / "eval/runs/pipeline" / hu_id).glob("run-*/model.json"))]
    b_paths = sorted((ROOT / "eval/runs/consensus" / hu_id).glob("ext-*/model.json"),
                     key=lambda p: int(p.parent.name.split("-")[1]))
    b = [load(p) for p in b_paths]
    groups = [b[i:i + 3] for i in range(0, len(b) - len(b) % 3, 3)]
    c = [merge(g).model for g in groups]
    out_dir = ROOT / "eval/runs/consensus" / hu_id
    for k, m in enumerate(c, 1):
        (out_dir / f"consenso-{k}.model.json").write_text(m.model_dump_json(indent=2, exclude_none=True) + "\n",
                                                          encoding="utf-8")

    rows = {"A. única, prompt v1": measure(story, a), "B. única, prompt v2": measure(story, b),
            "C. consenso 3× v2": measure(story, c)}
    lines = [f"# Estabilidad de la extracción — {hu_id}", "",
             "| Condición | Modelos | Frames por modelo | CV frames | Jaccard frame_id | Jaccard firmas tipo×CA×técnica |",
             "|---|---|---|---|---|---|"]
    for name, r in rows.items():
        lines.append(f"| {name} | {r['modelos']} | {', '.join(map(str, r['frames']))} | {r['cv_frames']} | "
                     f"{r['jaccard_frame_id']} | {r['jaccard_firmas']} |")
    lines += ["", "Parámetros por modelo:"]
    for name, r in rows.items():
        for ps in r["parametros"]:
            lines.append(f"- {name}: {', '.join(ps)}")
    text = "\n".join(lines) + "\n"
    (ROOT / "eval" / f"stability_{hu_id}.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "HU-202")
