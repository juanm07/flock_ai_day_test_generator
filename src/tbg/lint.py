"""Lint determinista de la HU, antes de que intervenga ningún LLM.

- Requirements Smells (Femmer et al., JSS 2017): léxico en rules/smells_es.yaml.
- Quality User Story (Lucassen et al., REJ 2016): subset sintáctico de los criterios de AQUSA
  (well-formed, has-benefit, atomic, has-acceptance-criteria) + verificabilidad de cada CA.
- Sugerencia de feature_tags por léxico (rules/tags.yaml).
"""

from __future__ import annotations

import re

from . import rules
from .hu import UserStory
from .schemas import Finding


def _rx(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){term}", re.I)


def match_any(terms: list[str], text: str) -> str | None:
    for t in terms:
        m = _rx(t).search(text)
        if m:
            return m.group(0)
    return None


def _segments(story: UserStory) -> list[tuple[str, str]]:
    segs: list[tuple[str, str]] = []
    if story.want:
        segs.append(("enunciado", f"Como {story.role}, quiero {story.want}" + (f", para {story.so_that}" if story.so_that else "")))
    segs += [(ac_id, txt) for ac_id, txt in story.acceptance_criteria]
    return segs


def smells(story: UserStory) -> list[Finding]:
    out: list[Finding] = []
    for category, spec in rules.load("smells_es").items():
        for loc, text in _segments(story):
            for pattern in spec["patterns"]:
                for m in re.finditer(rf"(?<!\w){pattern}(?!\w)", text, re.I):
                    out.append(
                        Finding(rule=f"smell.{category}", category="Requirements Smell", message=spec["description"],
                                text=m.group(0), location=loc)
                    )
    return out


_OBSERVABLE = re.compile(
    r"\b(muestra|mostrar|envía|enviar|redirige|confirma|puede|pueda|recibe|ve\b|visualiza|descarga|genera|"
    r"rechaza|bloquea|habilita|deshabilita|actualiza|guarda|registra|notifica|informa|devuelve|lista|exporta|"
    r"crea|queda|usa|dispara|abre|marca|elimina|borra|calcula|asigna|aparece|cambia|permite|impide|contiene|llega)",
    re.I,
)


def qus(story: UserStory) -> list[Finding]:
    out: list[Finding] = []

    def add(rule: str, msg: str, text: str = "", loc: str = "enunciado") -> None:
        out.append(Finding(rule=f"qus.{rule}", category="Quality User Story", message=msg, text=text, location=loc))

    if not (story.role and story.want):
        add("well_formed", "La HU no sigue el formato 'Como <rol>, quiero <acción>': falta rol o acción.")
    if story.want and not story.so_that:
        add("has_benefit", "Falta el 'para …': sin objetivo no se puede validar si los CAs cubren el propósito.")
    if story.want and re.search(r"\b(y|o|e|u)\b\s+(?:\w+\s+){0,2}(?:quiero|poder|\w+ar|\w+er|\w+ir)\b", story.want, re.I):
        add("atomic", "El 'quiero' parece pedir más de una funcionalidad (conjunción entre acciones): considerar dividir la HU.",
            story.want)
    if not story.acceptance_criteria:
        add("has_acceptance_criteria", "La HU no tiene criterios de aceptación: es BLOQUEANTE para diseñar casos.")
    for ac_id, text in story.acceptance_criteria:
        if not _OBSERVABLE.search(text):
            add("ac_observable", "El CA no describe un resultado observable (qué se ve, qué se envía, qué cambia).", text, ac_id)
    return out


def suggest_tags(story: UserStory) -> dict[str, str]:
    """{tag: término que lo disparó}"""
    out: dict[str, str] = {}
    for tag, spec in rules.load("tags").items():
        hit = match_any(spec["terms"], story.text)
        if hit:
            out[tag] = hit
    return out


def lint(story: UserStory) -> list[Finding]:
    return qus(story) + smells(story)
