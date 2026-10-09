"""Gate de calidad de la suite como código (reemplaza la "auto-revisión" que hacía el propio LLM).

Un ítem CRÍTICO fallado → exit code ≠ 0: el agente debe corregir la redacción y volver a correr.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import rules
from .quotes import normalize
from .schemas import CaseDraft, FrameSet, SuiteDraft


@dataclass
class CheckResult:
    id: str
    name: str
    critical: bool
    passed: bool
    details: list[str] = field(default_factory=list)


@dataclass
class Report:
    checks: list[CheckResult]

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks if c.critical)


def _case_text(c: CaseDraft) -> str:
    return " ".join([c.title, c.preconditions, *(s.action + " " + s.expected for s in c.steps), c.evidence, c.notes])


def _compound_re(spec: dict) -> re.Pattern[str]:
    conn = "|".join(sorted((re.escape(x) for x in spec["action_connectors"]), key=len, reverse=True))
    verbs = "|".join(re.escape(v) for v in spec["action_verb_stems"])
    return re.compile(rf"(?<!\w)(?:{conn})\s+(?:{verbs})\w*", re.I)


def validate(fs: FrameSet, suite: SuiteDraft) -> Report:
    spec = rules.load("quality")
    frames = {f.frame_id: f for f in fs.frames}
    cases: dict[str, CaseDraft] = {}
    checks: list[CheckResult] = []

    # C1 — cada frame redactado exactamente una vez
    c1 = CheckResult("C1", "Cada frame tiene exactamente un caso redactado (sin casos inventados)", True, True)
    for c in suite.cases:
        if c.frame_id not in frames:
            c1.details.append(f"{c.frame_id}: no existe en frames.json (caso inventado fuera del diseño)")
        elif c.frame_id in cases:
            c1.details.append(f"{c.frame_id}: redactado más de una vez")
        else:
            cases[c.frame_id] = c
    for fid, f in frames.items():
        if fid not in cases:
            c1.details.append(f"{f.case_id} ({fid}): sin redactar")
    c1.passed = not c1.details
    checks.append(c1)

    def label(fid: str) -> str:
        return frames[fid].case_id

    # C2 — cero comportamiento inventado
    c2 = CheckResult("C2", "Cero comportamiento inventado: los frames con supuestos llevan [SUPUESTO] en el caso", True, True)
    for fid, c in cases.items():
        if frames[fid].supuestos and "[SUPUESTO" not in _case_text(c):
            c2.details.append(f"{label(fid)}: el frame depende de {len(frames[fid].supuestos)} supuesto(s) y el caso no marca [SUPUESTO: …]")
    c2.passed = not c2.details
    checks.append(c2)

    # C3 — pasos atómicos
    compound = _compound_re(spec)
    c3 = CheckResult("C3", "Pasos atómicos: una acción por paso", True, True)
    for fid, c in cases.items():
        for i, s in enumerate(c.steps, 1):
            m = compound.search(s.action)
            if m:
                c3.details.append(f"{label(fid)} paso {i}: «{s.action}» encadena acciones («{m.group(0)}»)")
    c3.passed = not c3.details
    checks.append(c3)

    # C4 — resultados esperados observables
    vague = [re.compile(rf"(?<!\w){re.escape(v)}(?!\w)", re.I) for v in spec["vague_expected"]]
    c4 = CheckResult("C4", "Resultados esperados observables (sin 'correctamente', 'se ve bien', …)", True, True)
    for fid, c in cases.items():
        for i, s in enumerate(c.steps, 1):
            if not s.expected.strip():
                c4.details.append(f"{label(fid)} paso {i}: resultado esperado vacío")
            for rx in vague:
                m = rx.search(s.expected)
                if m:
                    c4.details.append(f"{label(fid)} paso {i}: «{m.group(0)}» no es observable")
    c4.passed = not c4.details
    checks.append(c4)

    # C5 — datos concretos y fieles al diseño
    abstract = [re.compile(rf"(?<!\w){re.escape(v)}(?!\w)", re.I) for v in spec["abstract_data"]]
    c5 = CheckResult("C5", "Datos concretos y fieles a los frames (el LLM no cambia ni abstrae los datos)", True, True)
    for fid, c in cases.items():
        text = _case_text(c)
        for rx in abstract:
            m = rx.search(text)
            if m:
                c5.details.append(f"{label(fid)}: dato abstracto «{m.group(0)}»")
        for k, v in frames[fid].data.items():
            if "[" in k or v.startswith(("''", "(")):  # límites, vacíos y referencias '(…)' se renderizan desde el frame
                continue
            if normalize(v) not in normalize(text):
                c5.details.append(f"{label(fid)}: el dato de prueba «{v}» ({k}) no aparece en el caso")
    c5.passed = not c5.details
    checks.append(c5)

    # C6/C7/C8 — garantizados por construcción, se reportan igual (auditables)
    checks.append(CheckResult("C6", "IDs únicos y secuenciales", True, True, ["Asignados por código (CP-001…), no por el LLM"]))
    cov = fs.coverage
    uncovered = [r for r in cov.acceptance if not r.covered]
    checks.append(CheckResult("C7", "Cada CA cubierta o con motivo explícito", True, all(r.reason for r in uncovered),
                              [f"{cov.ac_percent:g}% de CAs ({sum(r.covered for r in cov.acceptance)}/{len(cov.acceptance)}) — calculado por código"]
                              + [f"{r.ac_id}: {r.reason}" for r in uncovered]))
    asked = [g for g in fs.gaps if g.asked]
    max_q = rules.load("gaps").get("max_questions", 8)
    checks.append(CheckResult("C8", f"Preguntas al PO ≤ {max_q}, todas con default", True,
                              len(asked) <= max_q and all(g.default for g in asked), [f"{len(asked)} preguntas"]))

    # Observaciones
    prefixes = tuple(spec["title_prefixes"])
    o1 = CheckResult("O1", f"Títulos con formato '{' / '.join(prefixes)} …'", False, True)
    o1.details = [f"{label(fid)}: «{c.title}»" for fid, c in cases.items() if not c.title.startswith(prefixes)]
    o1.passed = not o1.details
    checks.append(o1)

    pos = sum(1 for f in fs.frames if f.type == "Funcional")
    neg = sum(1 for f in fs.frames if f.type in ("Negativo", "Borde"))
    ratio = neg / pos if pos else 1.0
    checks.append(CheckResult("O2", "≥1 negativo/borde cada 2 positivos", False, ratio >= spec["min_negative_ratio"],
                              [f"{neg} negativos/bordes vs {pos} funcionales (ratio {ratio:.2f})"]))

    smoke = [f.case_id for f in fs.frames if f.smoke]
    checks.append(CheckResult("O3", "Subset de humo marcado", False, bool(smoke), [", ".join(smoke) or "ninguno"]))

    titles: dict[str, str] = {}
    o4 = CheckResult("O4", "Sin casos duplicados (mismo título)", False, True)
    for fid, c in cases.items():
        key = normalize(c.title)
        if key in titles:
            o4.details.append(f"{label(fid)} repite el título de {titles[key]}")
        titles[key] = label(fid)
    o4.passed = not o4.details
    checks.append(o4)

    ids = {f.case_id for f in fs.frames} | set(frames)
    o5 = CheckResult("O5", "Dependencias entre casos apuntan a casos existentes (referenciar por frame_id F-…)", False, True)
    for fid, c in cases.items():
        for ref in re.findall(r"\b(?:CP-\d{3}|F-[0-9a-f]{8})\b", _case_text(c)):
            if ref not in ids:
                o5.details.append(f"{label(fid)}: referencia {ref}, que no existe")
            elif ref.startswith("CP-"):
                o5.details.append(f"{label(fid)}: referencia {ref} por número; usar el frame_id (los CP-NNN cambian al regenerar)")
    o5.passed = not o5.details
    checks.append(o5)
    return Report(checks)
