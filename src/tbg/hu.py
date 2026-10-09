"""Parser determinista de historias de usuario.

Acepta los formatos que escriben los equipos en la práctica:
- Encabezado con ID (`## HU-101 — Título`) o un ID suelto en las primeras líneas (`HU-101`, `PROJ-42`); si no hay,
  queda `HU-000` y la app le asigna uno.
- Enunciado en una frase (`Como … quiero … para …`) o con etiquetas (`Como:` / `Quiero:` / `Para:`, `As a:` …).
- Criterios bajo "Criterios de aceptación", "Criterios", "AC" o "Acceptance criteria", como lista numerada, viñetas,
  párrafos separados por línea en blanco, o escenarios Gherkin (Dado/Cuando/Entonces).
- La sección de criterios termina en un encabezado, `---` o una etiqueta de metadatos ("Notas:", "Link de…:",
  "Fuera de alcance:", …). Con encabezado de ID, solo se toma ese bloque (no se leen notas de calibración de abajo).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_ID_RE = re.compile(r"^(#{1,6})\s*([A-Z][A-Z0-9]{0,9}-[A-Z]?\d+)\s*[—–:-]\s*(.+?)\s*$")
_LOOSE_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-[A-Z]?\d+)\b")
_AC_HEADER_RE = re.compile(r"^(criterios de aceptaci[oó]n\b.*|criterios|acceptance criteria|ac)\s*:?$", re.I)
_ITEM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*•]|CA-?\d+[.:)-]?)\s+(.+)$", re.I)
_GHERKIN_START = re.compile(r"^\s*(escenario|scenario)\b\s*:?\s*(.*)$", re.I)
_GHERKIN_STEP = re.compile(r"^\s*(dado|cuando|entonces|y|pero|given|when|then|and|but)\b\s+\S", re.I)
_META_RE = re.compile(r"^(link|links|notas?|contexto|fuera de alcance|dependencias|referencias|observaciones|supuestos|"
                      r"preguntas|definition of done|dod|dise[nñ]o|figma|fathom|prioridad|estimaci[oó]n|out of scope|notes)"
                      r"\b[^:]{0,40}:", re.I)
_LABELS = {
    "role": re.compile(r"^(?:yo\s+)?(?:como|as an?)\s*:\s*(.*)$", re.I),
    "want": re.compile(r"^(?:quiero|i want(?: to)?)\s*:\s*(.*)$", re.I),
    "so_that": re.compile(r"^(?:para(?: poder)?|so that)\s*:\s*(.*)$", re.I),
}


@dataclass
class UserStory:
    id: str
    title: str
    text: str  # bloque completo de la HU (fuente para verificar citas)
    role: str | None = None
    want: str | None = None
    so_that: str | None = None
    acceptance_criteria: list[tuple[str, str]] = field(default_factory=list)
    notes: str = ""


def _strip_md(s: str) -> str:
    return re.sub(r"[*_`]", "", s).strip()


def _block(lines: list[str]) -> tuple[list[str], str | None, str | None]:
    for i, line in enumerate(lines):
        m = _ID_RE.match(line.strip())
        if m:
            level = len(m.group(1))
            block = [lines[i]]
            for nxt in lines[i + 1:]:
                s = nxt.strip()
                if s == "---" or re.match(rf"^#{{1,{level}}}\s", s):
                    break
                block.append(nxt)
            return block, m.group(2), _strip_md(m.group(3))
    return [ln for ln in lines if not ln.lstrip().startswith(">")], None, None


def _criteria(block: list[str]) -> tuple[list[str], list[str]]:
    """Devuelve (criterios, líneas de notas fuera de la sección)."""
    items: list[str] = []
    notes: list[str] = []
    in_ac, gherkin, prev_blank = False, False, True
    for raw in block:
        line = _strip_md(raw)
        if not in_ac:
            if _AC_HEADER_RE.match(line):
                in_ac, prev_blank = True, True
            elif _META_RE.match(line):
                notes.append(line)
            continue
        if not line:
            prev_blank = True
            continue
        if raw.lstrip().startswith("#") or line == "---" or _META_RE.match(line):
            in_ac = False
            if _META_RE.match(line):
                notes.append(line)
            continue
        if m := _GHERKIN_START.match(line):
            items.append(m.group(2).strip() or line)
            gherkin = True
        elif _GHERKIN_STEP.match(line) and gherkin and items:
            items[-1] = f"{items[-1]} {line}".strip()
        elif m := _ITEM_RE.match(raw):
            items.append(_strip_md(m.group(1)))
            gherkin = False
        elif prev_blank or not items:
            items.append(line)
            gherkin = bool(_GHERKIN_STEP.match(line))
        else:  # continuación del criterio anterior
            items[-1] = f"{items[-1]} {line}"
        prev_blank = False
    return [i for i in items if i], notes


def parse_story(raw: str) -> UserStory:
    lines = raw.splitlines()
    block, sid, title = _block(lines)
    if sid is None:
        head = " ".join(lines[:5])
        m = _LOOSE_ID_RE.search(head)
        sid = m.group(1) if m else "HU-000"
    text = "\n".join(block).strip()
    story = UserStory(id=sid, title=title or "Sin título", text=text)

    # enunciado con etiquetas
    for raw_line in block:
        line = _strip_md(raw_line)
        for key, rx in _LABELS.items():
            m = rx.match(line)
            if m and m.group(1).strip() and getattr(story, key) is None:
                setattr(story, key, m.group(1).strip(" ,."))
    # enunciado en una frase
    if not (story.role and story.want):
        plain = _strip_md(" ".join(ln.strip() for ln in block if ln.strip() and not _ID_RE.match(ln.strip())))
        m = re.search(r"\bcomo\s+(.+?),?\s+quiero\s+(.+?)(?:,?\s+para(?:\s+poder)?\s+(.+?)\.)", plain, re.I)
        if m:
            story.role, story.want, story.so_that = (g.strip(" ,.") for g in m.groups())
        else:
            m = re.search(r"\bcomo\s+(.+?),?\s+quiero\s+(.+?)[.\n]", plain, re.I)
            if m:
                story.role, story.want = (g.strip(" ,.") for g in m.groups())

    criteria, notes = _criteria(block)
    story.acceptance_criteria = [(f"CA-{i}", c) for i, c in enumerate(criteria, 1)]
    story.notes = "\n".join(notes)
    if story.title == "Sin título" and story.want:
        words = story.want.split()
        story.title = " ".join(words[:9]).rstrip(",;") + ("…" if len(words) > 9 else "")
        story.title = story.title[:1].upper() + story.title[1:]
    return story


def load_story(path: str | Path) -> UserStory:
    return parse_story(Path(path).read_text(encoding="utf-8"))
