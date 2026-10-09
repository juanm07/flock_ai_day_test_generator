"""Análisis de valores límite (Myers, *The Art of Software Testing*): mín-1, mín, mín+1, máx-1, máx, máx+1.

Los valores concretos se calculan, no se "imaginan": para longitudes se genera un string determinista.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import Bounds

_PATTERN = "Abcdefgh12"


@dataclass(frozen=True)
class BoundaryValue:
    label: str  # "mín-1", "mín", …
    value: float
    valid: bool
    side: str  # "inferior" | "superior"


def _fmt(v: float) -> str:
    return f"{v:g}"


def boundary_values(b: Bounds) -> list[BoundaryValue]:
    step = 1 if b.integer else 0.01
    non_negative = b.unit in ("chars", "bytes", "items")
    out: list[BoundaryValue] = []
    seen: set[float] = set()

    def add(label: str, v: float, valid: bool, side: str) -> None:
        v = round(v, 2)
        if (non_negative and v < 0) or v in seen:
            return
        seen.add(v)
        out.append(BoundaryValue(label, v, valid, side))

    if b.min is not None:
        add("mín-1", b.min - step, False, "inferior")
        add("mín", b.min, True, "inferior")
        add("mín+1", b.min + step, True, "inferior")
    if b.max is not None:
        add("máx-1", b.max - step, True, "superior")
        add("máx", b.max, True, "superior")
        add("máx+1", b.max + step, False, "superior")
    return out


def literal(bv: BoundaryValue, unit: str) -> str:
    """Valor completo para tests automatizados (sin abreviar)."""
    n = int(bv.value)
    if unit == "chars":
        return (_PATTERN * (n // len(_PATTERN) + 1))[:n]
    return _fmt(bv.value)


def concrete(bv: BoundaryValue, unit: str) -> str:
    """Dato de prueba concreto y reproducible para el valor límite."""
    n = int(bv.value)
    if unit == "chars":
        if n == 0:
            return "'' (vacío)"
        s = (_PATTERN * (n // len(_PATTERN) + 1))[:n]
        return f"'{s}' ({n} caracteres)" if n <= 40 else f"'{_PATTERN}' repetido hasta {n} caracteres ({s[:12]}…)"
    if unit == "bytes":
        return f"archivo de {n} bytes"
    if unit == "items":
        return f"{n} elementos"
    if unit == "days":
        return f"{_fmt(bv.value)} días"
    return _fmt(bv.value)
