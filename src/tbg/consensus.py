"""Self-consistency sobre la extracción del TestModel (Wang et al., ICLR 2023, "Self-Consistency Improves Chain of
Thought Reasoning in Language Models"): el agente extrae N modelos de forma INDEPENDIENTE y este módulo los fusiona
por voto mayoritario, de forma determinista.

1. Alineación: los parámetros (y luego sus elecciones) de distintos modelos se emparejan por similitud
   (CAs en común, tipo, tokens de nombre/descripción/ejemplo). Clustering greedy con a lo sumo un elemento
   por modelo en cada cluster.
2. Voto: sobrevive un parámetro/elección si aparece en más de la mitad de los modelos. Los minoritarios no se
   descartan en silencio: se reportan para que un humano decida.
3. Canonicalización: nombre más votado (desempate: más corto, alfabético), atributos por mayoría.

El resultado no depende del orden de los archivos de entrada (los modelos se identifican por hash de contenido).
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from .schemas import AcceptanceCriterion, Bounds, Choice, Constraint, Parameter, TestModel

_STOP = {"de", "del", "la", "el", "los", "las", "en", "que", "por",  # "con"/"sin"/"no" NO: dan la polaridad
         "para", "un", "una", "y", "o", "a", "al",
         "se", "su", "sus", "es", "the", "of", "to", "valor", "dato", "campo", "tipo"}
PARAM_THRESHOLD = 0.35
CHOICE_THRESHOLD = 0.3


def _tokens(*texts: str | None) -> set[str]:
    raw = " ".join(t for t in texts if t)
    raw = unicodedata.normalize("NFKD", raw.replace("_", " ")).encode("ascii", "ignore").decode().lower()
    return {w[:6] for w in re.split(r"[^a-z0-9]+", raw) if w and w not in _STOP}


def _jac(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def _mode(values: list, key=lambda v: (len(str(v)), str(v))):
    """Valor más frecuente; desempate determinista (más corto, luego alfabético)."""
    counts = Counter(values)
    best = max(counts.values())
    return min((v for v in counts if counts[v] == best), key=key)


@dataclass
class Minority:
    kind: str  # "parámetro" | "elección" | "tag" | "restricción"
    name: str
    votes: int
    total: int
    detail: str = ""
    payload: dict = field(default_factory=dict)  # lo necesario para agregarlo al modelo si una persona lo decide


@dataclass
class ConsensusResult:
    model: TestModel
    n: int
    kept_params: int
    minorities: list[Minority] = field(default_factory=list)
    agreement: float = 0.0  # proporción de elementos (params+choices) con voto unánime


def _model_id(m: TestModel) -> str:
    return hashlib.sha1(m.model_dump_json().encode()).hexdigest()[:10]


def _cluster(items: list[tuple[str, object]], sim, threshold: float) -> list[list[tuple[str, object]]]:
    """items: [(model_id, obj)]. Greedy por similitud descendente con *complete linkage* (todos los pares del
    cluster deben superar el umbral, para no encadenar conceptos distintos) y ≤1 elemento por modelo."""
    idx = {i: {i} for i in range(len(items))}
    sims: dict[tuple[int, int], float] = {}
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i][0] == items[j][0]:
                continue
            s = sims[(i, j)] = sims[(j, i)] = sim(items[i][1], items[j][1])
            if s >= threshold:
                pairs.append((-round(s, 6), _label(items[i]), _label(items[j]), i, j))
    pairs.sort()
    for _, _, _, i, j in pairs:
        ci, cj = idx[i], idx[j]
        if ci is cj:
            continue
        models_i = {items[k][0] for k in ci}
        if models_i & {items[k][0] for k in cj}:
            continue
        if any(sims.get((a, b), 0.0) < threshold for a in ci for b in cj):
            continue
        merged = ci | cj
        for k in merged:
            idx[k] = merged
    seen, clusters = set(), []
    for i in range(len(items)):
        c = idx[i]
        if id(c) not in seen:
            seen.add(id(c))
            clusters.append([items[k] for k in sorted(c, key=lambda k: _label(items[k]))])
    return clusters


def _label(item) -> str:
    return f"{item[0]}:{getattr(item[1], 'name', '')}"


def _param_sim(p: Parameter, q: Parameter) -> float:
    ac = _jac(set(p.ac_refs), set(q.ac_refs))
    kind = 1.0 if p.kind == q.kind else 0.0
    words = _jac(_tokens(p.name, p.description), _tokens(q.name, q.description))
    examples = _jac(_tokens(*(c.example for c in p.choices)), _tokens(*(c.example for c in q.choices)))
    same_name = 0.25 if _tokens(p.name) == _tokens(q.name) else 0.0
    return min(1.0, 0.35 * ac + 0.15 * kind + 0.35 * words + 0.15 * examples + same_name)


def _choice_sim(c: Choice, d: Choice) -> float:
    if c.kind != d.kind:
        return 0.0
    return 0.6 * _jac(_tokens(c.name, c.description), _tokens(d.name, d.description)) + \
        0.4 * (1.0 if (c.example or "") == (d.example or "") else _jac(_tokens(c.example), _tokens(d.example)))


def merge(models: list[TestModel], majority: int | None = None) -> ConsensusResult:
    if not models:
        raise ValueError("se necesita al menos un modelo")
    models = sorted(models, key=_model_id)  # independencia del orden de entrada
    seen: Counter = Counter()
    ids = []
    for m in models:  # modelos idénticos siguen siendo votos distintos
        h = _model_id(m)
        ids.append(f"{h}-{seen[h]}")
        seen[h] += 1
    n = len(models)
    need = majority or n // 2 + 1
    minorities: list[Minority] = []
    unanimous = total_elems = 0

    # --- campos escalares de la HU
    def vote(attr):
        return _mode([getattr(m, attr) for m in models], key=lambda v: (v is None, len(str(v)), str(v)))

    tag_votes = Counter(t for m in models for t in set(m.feature_tags))
    tags = sorted(t for t, v in tag_votes.items() if v >= need)
    minorities += [Minority("tag", t, v, n, payload={"tag": t}) for t, v in sorted(tag_votes.items()) if v < need]

    ac_ids = sorted({a.id for m in models for a in m.acceptance_criteria}, key=lambda s: int(s.split("-")[1]))
    acs = []
    for ac in ac_ids:
        texts = [a.text for m in models for a in m.acceptance_criteria if a.id == ac]
        if len(texts) >= need:
            acs.append(AcceptanceCriterion(id=ac, text=_mode(texts)))

    # --- parámetros
    items = [(mid, p) for mid, m in zip(ids, models) for p in m.parameters]
    pos = {(mid, p.name): i / max(1, len(m.parameters)) for mid, m in zip(ids, models) for i, p in enumerate(m.parameters)}
    params: list[tuple[float, Parameter]] = []
    choice_map: dict[tuple[str, str, str], tuple[str, str]] = {}  # (model, param, choice) → canónicos
    orphans: list[tuple[str, str, Choice, str]] = []  # (modelo, param original, elección, param canónico)
    for cluster in _cluster(items, _param_sim, PARAM_THRESHOLD):
        members = [p for _, p in cluster]
        total_elems += 1
        if len(cluster) < need:
            minorities.append(Minority("parámetro", members[0].name, len(cluster), n, members[0].description,
                                       payload={"parameter": members[0].model_dump()}))
            continue
        unanimous += len(cluster) == n
        name = _mode([p.name for p in members])
        ref = next(p for p in members if p.name == name)
        ac_votes = Counter(a for p in members for a in set(p.ac_refs))
        ac_refs = sorted((a for a, v in ac_votes.items() if v >= need), key=lambda s: int(s.split("-")[1])) \
            or sorted(ref.ac_refs)
        bounds_votes = [p.bounds.model_dump_json() if p.bounds else None for p in members]
        b = _mode(bounds_votes, key=lambda v: (v is None, str(v)))
        bounds = Bounds.model_validate_json(b) if b and bounds_votes.count(b) >= need else None
        relevant = sum(p.bounds_relevant for p in members) >= need

        # elecciones del parámetro
        citems = [(mid, c) for mid, p in cluster for c in p.choices]
        cpos = {(mid, c.name): i for mid, p in cluster for i, c in enumerate(p.choices)}
        choices: list[tuple[float, Choice]] = []
        for cc in _cluster(citems, _choice_sim, CHOICE_THRESHOLD):
            cm = [c for _, c in cc]
            total_elems += 1
            if len(cc) < need:  # puede haber consenso semántico bajo OTRO parámetro: se intenta rescatar después
                orphans += [(mid, _owner(cluster, mid).name, c, name) for mid, c in cc]
                total_elems -= 1
                continue
            unanimous += len(cc) == n
            cname = _mode([c.name for c in cm])
            cref = next(c for c in cm if c.name == cname)
            with_expected = [c for c in cm if c.expected is not None]
            exp_src = cref if cref.expected is not None else (with_expected[0] if with_expected else None)
            keep_expected = len(with_expected) >= need and exp_src is not None
            choice = Choice(
                name=cname, description=cref.description, kind=cref.kind, example=cref.example,
                expected=exp_src.expected if keep_expected else None,
                quote=exp_src.quote if keep_expected else None,
                assumed=sum(c.assumed for c in cm) >= need,
            )
            avg = sum(cpos[(mid, c.name)] for mid, c in cc) / len(cc)
            choices.append((avg, choice))
            for mid, c in cc:
                choice_map[(mid, _owner(cluster, mid).name, c.name)] = (name, cname)
        if not choices:
            continue
        choices.sort(key=lambda t: (t[0], t[1].name))
        ordered = [c for _, c in choices]
        # la primera válida es la "típica": se respeta el orden promedio, pero una válida debe ir antes que las inválidas
        ordered.sort(key=lambda c: c.kind != "valid")
        avg = sum(pos[(mid, p.name)] for mid, p in cluster) / len(cluster)
        params.append((avg, Parameter(name=name, description=ref.description, kind=ref.kind, ac_refs=ac_refs,
                                      choices=ordered, bounds=bounds, bounds_relevant=relevant or bool(bounds))))
    # --- segunda pasada: elecciones huérfanas que coinciden entre modelos aunque cada uno las colgó de otro parámetro
    by_name = {p.name: p for _, p in params}
    oitems = [(mid, c) for mid, _, c, _ in orphans]
    meta = {(mid, c.name, id(c)): (pname, canon) for mid, pname, c, canon in orphans}
    for cc in _cluster(oitems, _choice_sim, CHOICE_THRESHOLD):
        total_elems += 1
        cm = [c for _, c in cc]
        targets = [meta[(mid, c.name, id(c))][1] for mid, c in cc if meta[(mid, c.name, id(c))][1] in by_name]
        if len(cc) < need or not targets:
            param = targets[0] if targets else meta[(cc[0][0], cm[0].name, id(cm[0]))][0]
            minorities.append(Minority("elección", f"{param}.{cm[0].name}", len(cc), n, cm[0].description,
                                       payload={"param": param, "choice": cm[0].model_dump()}))
            continue
        target = by_name[_mode(targets)]
        cname = _mode([c.name for c in cm])
        if any(c.name == cname for c in target.choices):
            cname = f"{cname}_2"
        cref = next(c for c in cm if c.name.startswith(cname.removesuffix("_2")))
        target.choices.append(Choice(name=cname, description=cref.description, kind=cref.kind, example=cref.example,
                                     assumed=sum(c.assumed for c in cm) >= need))
        target.choices.sort(key=lambda c: c.kind != "valid")
        for mid, c in cc:
            choice_map[(mid, meta[(mid, c.name, id(c))][0], c.name)] = (target.name, cname)
    params.sort(key=lambda t: (t[0], t[1].name))

    # --- restricciones (traducidas a nombres canónicos)
    cons_votes: Counter = Counter()
    cons_reason: dict[str, str] = {}
    for mid, m in zip(ids, models):
        for c in m.constraints:
            tr = _translate(c, mid, choice_map)
            if tr:
                key = tr.model_dump_json()
                cons_votes[key] += 1
                cons_reason.setdefault(key, c.reason)
    def _with_reason(k: str) -> Constraint:
        return Constraint.model_validate_json(k).model_copy(update={"reason": cons_reason[k]})

    constraints = [_with_reason(k) for k, v in sorted(cons_votes.items()) if v >= need]
    minorities += [Minority("restricción", k, v, n, cons_reason[k], payload={"constraint": _with_reason(k).model_dump()})
                   for k, v in sorted(cons_votes.items()) if v < need]

    answers = {}
    for key in sorted({k for m in models for k in m.answers}):
        vals = [m.answers[key] for m in models if key in m.answers]
        if len(vals) >= need:
            best = _mode([a.model_dump_json() for a in vals])
            answers[key] = next(a for a in vals if a.model_dump_json() == best)

    merged = TestModel(
        story_id=vote("story_id"), title=vote("title"), module=vote("module"), role=vote("role"), want=vote("want"),
        so_that=vote("so_that"), feature_tags=tags, acceptance_criteria=acs,
        parameters=[p for _, p in params], constraints=constraints, answers=answers,
    )
    return ConsensusResult(model=merged, n=n, kept_params=len(params), minorities=minorities,
                           agreement=round(unanimous / total_elems, 3) if total_elems else 1.0)


def _owner(cluster, mid):
    return next(p for m, p in cluster if m == mid)


def _translate(c: Constraint, mid: str, cmap) -> Constraint | None:
    def tr(p, v):
        return cmap.get((mid, p, v))

    if_choice = {}
    for p, v in c.if_choice.items():
        t = tr(p, v)
        if not t:
            return None
        if_choice[t[0]] = t[1]
    forbids: dict[str, list[str]] = {}
    for p, vs in c.forbids.items():
        for v in vs:
            t = tr(p, v)
            if not t:
                return None
            forbids.setdefault(t[0], []).append(t[1])
    return Constraint(if_choice=if_choice, forbids={k: sorted(v) for k, v in sorted(forbids.items())}, reason="consenso")
