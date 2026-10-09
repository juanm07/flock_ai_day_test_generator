"""Flujo B: verificación y clasificación determinista de un bug a partir de los hechos que extrajo el LLM.

1. Citas: cada hecho debe citar textualmente el reporte (anti-alucinación). Una cita que no está → rechazo.
2. Faltantes OB/EB/S2R/ambiente (Bettenburg et al. 2008; Chaparro et al. 2017) → [PENDIENTE] + pregunta.
3. Severidad/prioridad por reglas (rules/severity.yaml). Las features sin cita cuentan como desconocidas; se
   evalúan todas sus combinaciones para decir si la clasificación es firme o preliminar y qué la condiciona.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field

from . import rules
from .quotes import normalize, quote_in
from .schemas import BugFacts, Fact

_SEV = ["S1", "S2", "S3", "S4"]

# Nombres legibles para QA (la UI y los reportes no deberían mostrar identificadores internos)
LABELS = {
    "data_loss": "pérdida de datos", "security": "seguridad", "blocks_critical_flow": "bloquea un flujo crítico",
    "workaround_exists": "hay workaround", "affects_subset_only": "afecta solo a algunos usuarios",
    "cosmetic_only": "solo cosmético", "regression": "es una regresión", "in_production": "está en producción",
    "before_release": "estamos antes de un release", "since": "desde cuándo pasa", "frequency": "frecuencia",
    "error_text": "texto del error", "affected_user": "usuario afectado", "environment.platform": "plataforma",
    "environment.environment": "entorno", "environment.app_version": "versión",
}
_PRI = ["P1", "P2", "P3", "P4"]


@dataclass
class QuoteIssue:
    path: str
    quote: str


@dataclass
class Classification:
    value: str
    firm: bool
    reason: str
    possible: list[str]
    conditions: dict[str, str]  # feature → valor alternativo que produciría


@dataclass
class BugCheck:
    facts: BugFacts
    rejected: list[QuoteIssue]
    hedged: dict[str, str]  # path → marca de incertidumbre encontrada
    missing: list[dict]
    features: dict[str, bool | None]
    feature_quotes: dict[str, str]
    severity: Classification
    priority: Classification
    title: str
    checks: list[tuple[str, str, bool, bool, list[str]]] = field(default_factory=list)  # id, nombre, crítico, ok, detalles

    @property
    def ok(self) -> bool:
        return all(ok for _, _, critical, ok, _ in self.checks if critical)


def _facts_with_paths(b: BugFacts) -> list[tuple[str, Fact]]:
    out: list[tuple[str, Fact]] = [("symptom", b.symptom)]
    out += [(f"observed[{i}]", f) for i, f in enumerate(b.observed)]
    out += [(f"evidence[{i}]", f) for i, f in enumerate(b.evidence)]
    for name in ("expected", "error_text", "frequency", "since", "affected_user"):
        f = getattr(b, name)
        if f is not None:
            out.append((name, f))
    for name in ("app_version", "environment", "platform"):
        f = getattr(b.environment, name)
        if f is not None:
            out.append((f"environment.{name}", f))
    return out


def _hedge(quote: str, hedges: list[str]) -> str | None:
    q = normalize(quote)
    return next((h for h in hedges if re.search(rf"(?<!\w){re.escape(h)}(?!\w)", q)), None)


def _matches(when: dict, feats: dict[str, bool]) -> bool:
    return all(feats.get(k) is v for k, v in when.items())


def _severity(feats: dict[str, bool], spec: dict) -> tuple[str, str]:
    rule = next(r for r in spec["severity_rules"] if _matches(r["when"], feats))
    sev, reason = rule["severity"], rule["reason"]
    for floor in spec["severity_floors"]:
        if _matches(floor["when"], feats) and _SEV.index(sev) > _SEV.index(floor["min"]):
            sev, reason = floor["min"], f"{reason} {floor['reason']}"
    return sev, reason


def _priority(feats: dict[str, bool], sev: str, spec: dict) -> tuple[str, str]:
    rows = {k: v for k, v in spec["priority_matrix"].items() if k != "default" and _matches(v["when"], feats)}
    if not rows:
        rows = {"default": spec["priority_matrix"]["default"]}
    name, row = min(rows.items(), key=lambda kv: _PRI.index(kv[1][sev]))
    prio, reason = row[sev], f"Contexto «{name}» × {sev} → {row[sev]}"
    for floor in spec["priority_floors"]:
        if _matches(floor["when"], feats) and _PRI.index(prio) > _PRI.index(floor["max"]):
            prio, reason = floor["max"], f"{reason}. {floor['reason']}"
    return prio, reason


def _classify(known: dict[str, bool | None], fn) -> Classification:
    unknown = [k for k, v in known.items() if v is None]
    base = {k: bool(v) for k, v in known.items()}  # desconocido ⇒ se evalúa como False para el valor reportado
    value, reason = fn(base)
    possible = {value}
    conditions: dict[str, str] = {}
    for combo in itertools.product([False, True], repeat=len(unknown)):
        alt = {**base, **dict(zip(unknown, combo))}
        v, _ = fn(alt)
        possible.add(v)
    for k in unknown:  # qué feature, por sí sola, cambia el resultado
        v, _ = fn({**base, k: True})
        if v != value:
            conditions[k] = v
    order = _SEV if value in _SEV else _PRI
    return Classification(value, firm=len(possible) == 1, reason=reason,
                          possible=sorted(possible, key=order.index), conditions=conditions)


def check(b: BugFacts, report_text: str) -> BugCheck:
    spec = rules.load("severity")
    rejected: list[QuoteIssue] = []
    hedged: dict[str, str] = {}

    for path, f in _facts_with_paths(b):
        if not quote_in(f.quote, report_text):
            rejected.append(QuoteIssue(path, f.quote))
        else:
            h = _hedge(f.quote, spec["hedges"])
            if h:
                hedged[path] = h
    for i, s in enumerate(b.steps):
        if s.quote is not None and not quote_in(s.quote, report_text):
            rejected.append(QuoteIssue(f"steps[{i}]", s.quote))
    for i, h in enumerate(b.hypotheses):
        if h.quote is not None and not quote_in(h.quote, report_text):
            rejected.append(QuoteIssue(f"hypotheses[{i}]", h.quote))

    features: dict[str, bool | None] = {}
    feature_quotes: dict[str, str] = {}
    for name, feat in b.features:
        value = feat.value
        if value is not None:
            if feat.quote is None:
                rejected.append(QuoteIssue(f"features.{name}", "(sin cita)"))
                value = None
            elif not quote_in(feat.quote, report_text):
                rejected.append(QuoteIssue(f"features.{name}", feat.quote))
                value = None
            else:
                feature_quotes[name] = feat.quote
        features[name] = value

    bad = {r.path for r in rejected}
    present = {
        "steps": any(s.quote and f"steps[{i}]" not in bad for i, s in enumerate(b.steps)),
        "observed": any(f"observed[{i}]" not in bad for i in range(len(b.observed))),
        "expected": b.expected is not None and "expected" not in bad,
        "error_text": b.error_text is not None and "error_text" not in bad and "error_text" not in hedged,
        "app_version": b.environment.app_version is not None and "environment.app_version" not in bad,
        "environment": b.environment.environment is not None and "environment.environment" not in bad,
        "platform": b.environment.platform is not None and "environment.platform" not in bad,
        "evidence": any(f"evidence[{i}]" not in bad for i in range(len(b.evidence))),
        "frequency": b.frequency is not None and "frequency" not in bad,
        "affected_user": b.affected_user is not None and "affected_user" not in bad,
    }
    missing = [{"field": k, **v} for k, v in spec["missing"].items() if not present[k]]
    for path, h in hedged.items():  # dato presente pero dicho con duda → se confirma
        if path in {m["field"] for m in missing}:
            continue
        missing.append({"field": path, "critical": False, "label": f"Confirmar {LABELS.get(path, path)} (dijo «{h}»)",
                        "question": f"Sobre «{_fact_by_path(b, path).quote}»: ¿podés confirmarlo?"})

    severity = _classify({k: features[k] for k in ("data_loss", "security", "blocks_critical_flow",
                                                    "workaround_exists", "affects_subset_only", "cosmetic_only")},
                         lambda f: _severity(f, spec))

    def prio_fn(f):
        sev, _ = _severity(f, spec)
        return _priority(f, sev, spec)

    priority = _classify(features, prio_fn)
    title = f"[{b.module or 'Módulo a confirmar'}] {b.symptom.text}"

    result = BugCheck(b, rejected, hedged, missing, features, feature_quotes, severity, priority, title)
    crit_missing = [m for m in missing if m["critical"]]
    result.checks = [
        ("B1", "Cero hechos sin cita verificable en el reporte", True, not rejected,
         [f"{r.path}: «{r.quote}» no aparece en el reporte" for r in rejected]),
        ("B2", "Título autónomo [Módulo] + síntoma", True, bool(b.symptom.text.strip()), [title]),
        ("B3", "Cada faltante crítico tiene [PENDIENTE] + pregunta", True, True,
         [f"{len(crit_missing)} faltantes críticos con pregunta"]),
        ("B4", "Severidad justificada (y preliminar si depende de faltantes)", True, True,
         [f"{severity.value}{'' if severity.firm else ' preliminar'}: {severity.reason}"]),
        ("B5", "Cero datos de ambiente/versión inventados", True,
         not any(r.path.startswith("environment") for r in rejected), []),
        ("B6", "Hipótesis separadas de hechos (hechos dudosos marcados)", False, True,
         [f"{len(b.hypotheses)} hipótesis; {len(hedged)} hechos 'a confirmar'"]),
        ("B7", "Pasos con respaldo en el reporte", False, all(s.quote for s in b.steps),
         [f"paso {i + 1} reconstruido sin cita" for i, s in enumerate(b.steps) if not s.quote]),
    ]
    return result


def _fact_by_path(b: BugFacts, path: str) -> Fact:
    return dict(_facts_with_paths(b))[path]
