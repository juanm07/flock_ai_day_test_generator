"""Verificación de citas: la defensa anti-alucinación compartida por ambos flujos.

Todo hecho que el LLM extrae lleva una `quote`; acá se comprueba que esa cita exista en el texto fuente.
La normalización es deliberadamente conservadora (mayúsculas, espacios, comillas tipográficas): una
paráfrasis NO pasa.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_QUOTE_CHARS = str.maketrans({"“": '"', "”": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "´": "'", "…": "..."})


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(_QUOTE_CHARS).casefold()
    text = re.sub(r"[*_`>]", " ", text)  # marcas de markdown que el LLM suele omitir
    return re.sub(r"\s+", " ", text).strip()


def quote_in(quote: str, source: str) -> bool:
    q = normalize(quote).strip(" .,;:\"'")
    return bool(q) and q in normalize(source)


@dataclass(frozen=True)
class QuoteCheck:
    path: str
    quote: str
    found: bool


def check_quotes(items: list[tuple[str, str | None]], source: str) -> list[QuoteCheck]:
    """items: [(ruta del campo, cita)]. Las citas None se ignoran (el schema decide si son obligatorias)."""
    return [QuoteCheck(path, q, quote_in(q, source)) for path, q in items if q is not None]
