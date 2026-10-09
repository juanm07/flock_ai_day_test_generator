"""Cobertura combinatoria 2-wise.

Kuhn, Wallace & Gallo (2004), "Software Fault Interactions and Implications for Software Testing" (IEEE TSE):
la gran mayoría de las fallas se disparan por la interacción de 1 o 2 parámetros → cubrir todos los pares
de valores da una detección alta con muchos menos casos que el producto cartesiano.
Generación con allpairspy (estilo PICT, Czerwonka 2006). La cobertura NO se le cree al generador:
`pair_coverage` la recalcula de forma independiente.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from itertools import combinations, product

from allpairspy import AllPairs

Row = dict[str, str]
Forbidden = Callable[[str, str, str, str], bool]  # (p1, v1, p2, v2) -> par prohibido


def _row_ok(row: Row, forbidden: Forbidden) -> bool:
    return not any(forbidden(a, row[a], b, row[b]) for a, b in combinations(row, 2))


def generate(params: list[tuple[str, list[str]]], forbidden: Forbidden) -> list[Row]:
    if not params:
        return [{}]
    if len(params) == 1:
        name, values = params[0]
        return [{name: v} for v in values]
    names = [n for n, _ in params]

    def filter_func(values: list[str]) -> bool:
        return _row_ok(dict(zip(names, values)), forbidden)

    rows = [dict(zip(names, r)) for r in AllPairs(OrderedDict(params), filter_func=filter_func)]
    return complete(rows, params, forbidden)


def complete(rows: list[Row], params: list[tuple[str, list[str]]], forbidden: Forbidden) -> list[Row]:
    """Agrega filas (greedy, determinista) hasta cubrir todos los pares requeridos.

    Necesario porque allpairspy, con restricciones, puede dejar pares sin cubrir: el verificador
    independiente lo detectó (ver tests/test_generate.py)."""
    rows = list(rows)
    missing = sorted(required_pairs(params, forbidden) - covered_pairs(rows, params))
    while missing:
        p1, v1, p2, v2 = missing[0]
        row: Row = {p1: v1, p2: v2}
        for name, values in params:
            if name in row:
                continue
            best, best_gain = None, -1
            for v in values:
                cand = {**row, name: v}
                if not _row_ok(cand, forbidden):
                    continue
                gain = sum(1 for (a, x, b, y) in missing if cand.get(a) == x and cand.get(b) == y)
                if gain > best_gain:
                    best, best_gain = v, gain
            if best is None:
                break
            row[name] = best
        if len(row) == len(params):
            rows.append({n: row[n] for n, _ in params})
        missing = [m for m in missing if not (row.get(m[0]) == m[1] and row.get(m[2]) == m[3])]
        if len(row) != len(params):  # restricciones insatisfacibles para este par: se descarta
            missing = [m for m in missing if m != (p1, v1, p2, v2)]
    return rows


def required_pairs(params: list[tuple[str, list[str]]], forbidden: Forbidden) -> set[tuple[str, str, str, str]]:
    req = set()
    for (p1, vs1), (p2, vs2) in combinations(params, 2):
        for v1, v2 in product(vs1, vs2):
            if not forbidden(p1, v1, p2, v2):
                req.add((p1, v1, p2, v2))
    return req


def covered_pairs(rows: list[Row], params: list[tuple[str, list[str]]]) -> set[tuple[str, str, str, str]]:
    names = [n for n, _ in params]
    got = set()
    for row in rows:
        for p1, p2 in combinations(names, 2):
            if p1 in row and p2 in row:
                got.add((p1, row[p1], p2, row[p2]))
    return got


def pair_coverage(rows: list[Row], params: list[tuple[str, list[str]]], forbidden: Forbidden) -> tuple[int, int]:
    req = required_pairs(params, forbidden)
    return len(req & covered_pairs(rows, params)), len(req)
