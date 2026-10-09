"""Evaluación comparativa: baseline "solo prompt" vs pipeline `tbg`, con el MISMO criterio para ambos brazos.

Todo se mide sobre el markdown final (`suite.md`) de cada corrida:
  1. Recall de lagunas golden en la sección "Preguntas para el PO".
  2. Estabilidad entre corridas de la misma HU (determinism score): cantidad de casos, firmas (tipo × CAs),
     distribución de prioridades, preguntas.
  3. Violaciones de las reglas de redacción del equipo (plantilla-caso-prueba.md): pasos compuestos,
     resultados no observables, datos abstractos.

Uso:  python eval/evaluate.py            (lee eval/runs/<brazo>/<HU>/run-*/suite.md y eval/golden/*.gaps.yaml)
Salida: eval/results.md + eval/results.json
"""

from __future__ import annotations

import itertools
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tbg import rules  # noqa: E402
from tbg.validate import _compound_re  # noqa: E402

RUNS = ROOT / "eval" / "runs"
GOLDEN = ROOT / "eval" / "golden"


# ---------------------------------------------------------------------------- parsing


def section(md: str, start: str, end: str) -> str:
    m = re.search(rf"^##\s*{start}.*?$(.*?)(?=^##\s*{end}|\Z)", md, re.M | re.S)
    return m.group(1) if m else ""


def parse_cases(md: str) -> list[dict]:
    blocks = re.split(r"^###\s+(?=CP-\d+)", md, flags=re.M)[1:]
    cases = []
    for b in blocks:
        def field(name: str) -> str:
            m = re.search(rf"^\|\s*\*\*{name}\*\*\s*\|\s*(.*?)\s*\|\s*$", b, re.M)
            return m.group(1) if m else ""
        steps = re.findall(r"^\|\s*\d+\s*\|(.+?)\|(.+?)\|\s*$", b, re.M)
        cases.append({
            "id": re.match(r"CP-\d+", b).group(0),
            "tipo": norm_type(field("Tipo")),
            "prioridad": (re.search(r"Alta|Media|Baja", field("Prioridad")) or [""])[0],
            "acs": tuple(sorted(set(re.findall(r"CA-\d+", field("Origen"))))),
            "datos": field("Datos de prueba"),
            "steps": [(a.strip(), e.strip()) for a, e in steps],
        })
    return cases


def norm_type(t: str) -> str:
    t = re.split(r"[·—(/,]| - ", t)[0].lower()  # tipo principal: "Funcional · Humo" → Funcional
    for key, name in [("no funcional", "No funcional"), ("negativ", "Negativo"), ("borde", "Borde"),
                      ("excep", "Excepción"), ("e2e", "E2E"), ("regres", "Regresión"), ("humo", "Humo"),
                      ("funcional", "Funcional")]:
        if key in t:
            return name
    return "Otro"


# ---------------------------------------------------------------------------- métricas


def gap_recall(md: str, golden: dict) -> tuple[float, list[str]]:
    q = section(md, r"2\.", r"3\.")
    hits = [g["id"] for g in golden["gaps"] if any(re.search(p, q, re.I) for p in g["match"])]
    return len(hits) / len(golden["gaps"]), hits


def style_violations(cases: list[dict]) -> dict[str, int]:
    spec = rules.load("quality")
    compound = _compound_re(spec)
    vague = [re.compile(rf"(?<!\w){re.escape(v)}(?!\w)", re.I) for v in spec["vague_expected"]]
    abstract = [re.compile(rf"(?<!\w){re.escape(v)}(?!\w)", re.I) for v in spec["abstract_data"]]
    out = Counter()
    for c in cases:
        for a, e in c["steps"]:
            out["pasos_compuestos"] += bool(compound.search(a))
            out["esperado_no_observable"] += any(rx.search(e) for rx in vague)
        text = c["datos"] + " " + " ".join(a + " " + e for a, e in c["steps"])
        out["datos_abstractos"] += any(rx.search(text) for rx in abstract)
    out["pasos_totales"] = sum(len(c["steps"]) for c in cases)
    return dict(out)


def jaccard(a: Counter, b: Counter) -> float:
    inter = sum((a & b).values())
    union = sum((a | b).values())
    return inter / union if union else 1.0


def stability(runs: list[dict]) -> dict:
    if len(runs) < 2:
        return {}
    n = [r["n_cases"] for r in runs]
    sig = [Counter((c["tipo"], c["acs"]) for c in r["cases"]) for r in runs]
    prio = [Counter((c["tipo"], c["acs"], c["prioridad"]) for c in r["cases"]) for r in runs]
    qs = [set(r["gap_hits"]) for r in runs]
    pairs = list(itertools.combinations(range(len(runs)), 2))
    mean = statistics.mean(n)
    extra = {}
    if all("frames_by_origin" in r for r in runs):  # pipeline: ¿dónde vive la varianza?
        for kind in ("reglas", "modelo"):
            sets = [set(r["frames_by_origin"][kind]) for r in runs]
            extra[f"jaccard_frames_{kind}"] = round(statistics.mean(
                len(sets[i] & sets[j]) / len(sets[i] | sets[j]) if sets[i] | sets[j] else 1.0 for i, j in pairs), 3)
    return {
        **extra,
        "n_cases": n,
        "n_cases_cv": round(statistics.pstdev(n) / mean, 3) if mean else 0.0,
        "jaccard_firmas": round(statistics.mean(jaccard(sig[i], sig[j]) for i, j in pairs), 3),
        "jaccard_firmas_con_prioridad": round(statistics.mean(jaccard(prio[i], prio[j]) for i, j in pairs), 3),
        "jaccard_lagunas_preguntadas": round(statistics.mean(
            len(qs[i] & qs[j]) / len(qs[i] | qs[j]) if qs[i] | qs[j] else 1.0 for i, j in pairs), 3),
        "n_preguntas": [r["n_questions"] for r in runs],
    }


def evaluate_run(path: Path, golden: dict | None) -> dict:
    md = path.read_text(encoding="utf-8")
    cases = parse_cases(md)
    recall, hits = gap_recall(md, golden) if golden else (None, [])
    q = section(md, r"2\.", r"3\.")
    run = {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "n_cases": len(cases),
        "tipos": dict(Counter(c["tipo"] for c in cases)),
        "prioridades": dict(Counter(c["prioridad"] for c in cases)),
        "n_questions": len(re.findall(r"^\*\*P-\d+", q, re.M)),
        "gap_recall": recall,
        "gap_hits": hits,
        "estilo": style_violations(cases),
        "reporta_cobertura_pares": bool(re.search(r"2-wise|pares", md)),
        "cases": cases,
    }
    frames = path.parent / "frames.json"
    if frames.exists():
        fs = json.loads(frames.read_text(encoding="utf-8"))
        run["gate"] = "APROBADO" if "Gate: APROBADO" in md else "FALLIDO"
        run["frames_by_origin"] = {
            "reglas": sorted(f["frame_id"] for f in fs["frames"] if f["origin"].startswith("rule:")),
            "modelo": sorted(f["frame_id"] for f in fs["frames"] if not f["origin"].startswith("rule:")),
        }
    return run


def main() -> None:
    results: dict = {}
    for arm_dir in sorted(p for p in RUNS.iterdir() if p.is_dir()):
        for hu_dir in sorted(p for p in arm_dir.iterdir() if p.is_dir()):
            g = GOLDEN / f"{hu_dir.name.lower()}.gaps.yaml"
            golden = yaml.safe_load(g.read_text(encoding="utf-8")) if g.exists() else None
            runs = [evaluate_run(p, golden) for p in sorted(hu_dir.glob("run-*/suite.md"))]
            if runs:
                results.setdefault(hu_dir.name, {})[arm_dir.name] = {"runs": runs, "stability": stability(runs)}

    (ROOT / "eval" / "results.json").write_text(json.dumps(
        results, ensure_ascii=False, indent=2, default=list), encoding="utf-8")
    (ROOT / "eval" / "results.md").write_text(report(results), encoding="utf-8")
    print(report(results))


def _fmt_recall(runs):
    vals = [r["gap_recall"] for r in runs if r["gap_recall"] is not None]
    return " / ".join(f"{v:.0%}" for v in vals) if vals else "—"


def report(results: dict) -> str:
    lines = ["# Resultados de la evaluación (baseline solo-prompt vs pipeline tbg)", "",
             "Generado por `python eval/evaluate.py`. Mismo modelo LLM en ambos brazos; mismas métricas sobre el markdown final.", ""]
    for hu, arms in results.items():
        lines += [f"## {hu}", "", "| Métrica | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]

        def row(name, fn):
            lines.append(f"| {name} | " + " | ".join(fn(a) for a in arms.values()) + " |")

        row("Corridas", lambda a: str(len(a["runs"])))
        row("Recall de lagunas golden (por corrida)", lambda a: _fmt_recall(a["runs"]))
        row("Casos por corrida", lambda a: ", ".join(str(r["n_cases"]) for r in a["runs"]))
        row("CV de cantidad de casos", lambda a: str(a["stability"].get("n_cases_cv", "—")))
        row("Jaccard firmas tipo×CA (prom. entre pares de corridas)", lambda a: str(a["stability"].get("jaccard_firmas", "—")))
        row("Jaccard firmas + prioridad", lambda a: str(a["stability"].get("jaccard_firmas_con_prioridad", "—")))
        row("Jaccard de lagunas preguntadas", lambda a: str(a["stability"].get("jaccard_lagunas_preguntadas", "—")))
        row("Jaccard frames de reglas (solo pipeline)", lambda a: str(a["stability"].get("jaccard_frames_reglas", "—")))
        row("Jaccard frames del modelo extraído (solo pipeline)", lambda a: str(a["stability"].get("jaccard_frames_modelo", "—")))
        row("Preguntas al PO por corrida", lambda a: ", ".join(str(r["n_questions"]) for r in a["runs"]))
        row("Pasos compuestos (viola regla 1)", lambda a: ", ".join(str(r["estilo"].get("pasos_compuestos", 0)) for r in a["runs"]))
        row("Esperados no observables (regla 2)", lambda a: ", ".join(str(r["estilo"].get("esperado_no_observable", 0)) for r in a["runs"]))
        row("Casos con datos abstractos (regla 3)", lambda a: ", ".join(str(r["estilo"].get("datos_abstractos", 0)) for r in a["runs"]))
        row("Reporta cobertura de pares", lambda a: ", ".join("sí" if r["reporta_cobertura_pares"] else "no" for r in a["runs"]))
        lines.append("")
        for arm, a in arms.items():
            for r in a["runs"]:
                missed = [g for g in (_golden_ids(hu)) if g not in r["gap_hits"]]
                lines.append(f"- `{r['path']}` ({arm}): tipos {r['tipos']}, prioridades {r['prioridades']}"
                             + (f", lagunas NO detectadas: {', '.join(missed)}" if missed else "")
                             + (f", gate {r['gate']}" if "gate" in r else ""))
        lines.append("")
    return "\n".join(lines)


def _golden_ids(hu: str) -> list[str]:
    g = GOLDEN / f"{hu.lower()}.gaps.yaml"
    return [x["id"] for x in yaml.safe_load(g.read_text(encoding="utf-8"))["gaps"]] if g.exists() else []


if __name__ == "__main__":
    main()
