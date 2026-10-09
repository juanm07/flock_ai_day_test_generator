"""Export de la suite a tests concretos, de forma determinista.

- Gherkin (`.feature`, en español: `# language: es`) para Cucumber / Behave / SpecFlow / playwright-bdd.
  Cada caso es un Escenario con tags de trazabilidad (@CP-001 @CA-1 @humo @prioridad-alta @supuesto).
  Los casos de valores límite son un "Esquema del escenario" con la tabla de Ejemplos (valor, resultado).
- Esqueleto de steps para Playwright (TypeScript, playwright-bdd): un step por texto único, con los
  literales entre comillas parametrizados como {string}. El equipo implementa el cuerpo de cada step.
"""

from __future__ import annotations

import re
import unicodedata

from .schemas import CaseDraft, Frame, FrameSet, SuiteDraft

_FID = re.compile(r"\bF-[0-9a-f]{8}\b")


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _line(s: str, ids: dict[str, str]) -> str:
    s = _FID.sub(lambda m: ids.get(m.group(0), m.group(0)), s)
    s = re.sub(r"\s*`?\[SUPUESTO:[^\]]*\]`?", "", s)  # los supuestos van como comentario + tag @supuesto
    return re.sub(r"\s+", " ", s).strip()


def _tags(f: Frame, story_id: str) -> str:
    tags = [f"@{f.case_id}", f"@{story_id}", *(f"@{a}" for a in f.ac_refs), f"@{_slug(f.type)}",
            f"@prioridad-{_slug(f.priority)}"]
    if f.smoke:
        tags.append("@humo")
    if f.supuestos:
        tags.append("@supuesto")
    if f.exploratory:
        tags.append("@exploratorio")
    return " ".join(tags)


def to_gherkin(fs: FrameSet, suite: SuiteDraft) -> str:
    drafts = {c.frame_id: c for c in suite.cases}
    ids = {f.frame_id: f.case_id for f in fs.frames}
    lines = ["# language: es", f"# Generado por tbg desde {fs.story_id} (modelo {fs.model_hash}). No editar a mano:",
             "# regenerar con `tbg export`.",
             f"@{fs.story_id}", f"Característica: {fs.story_id} — {fs.title}", ""]
    for f in fs.frames:
        d = drafts.get(f.frame_id)
        if d is None:
            continue
        lines.append(f"  {_tags(f, fs.story_id)}")
        for s in f.supuestos:
            lines.append(f"  # [SUPUESTO: {_line(s, ids)}]")
        if f.examples:
            lines += _outline(f, d, ids)
        else:
            lines.append(f"  Escenario: {f.case_id} — {_line(d.title, ids)}")
            lines.append(f"    Dado {_lower_first(_line(d.preconditions, ids))}")
            for s in d.steps:
                lines.append(f"    Cuando {_lower_first(_line(s.action, ids))}")
                lines.append(f"    Entonces {_lower_first(_line(s.expected, ids))}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _outline(f: Frame, d: CaseDraft, ids: dict[str, str]) -> list[str]:
    param = next((k for k, v in f.bindings.items() if v.startswith("bva:")), "valor")
    out = [f"  Esquema del escenario: {f.case_id} — {_line(d.title, ids)}",
           f"    Dado {_lower_first(_line(d.preconditions, ids))}",
           f'    Cuando ingreso "<valor>" en {param}',
           "    Entonces el valor es <resultado>",
           "",
           "    Ejemplos:",
           "      | etiqueta | medida | valor | resultado |"]
    for e in f.examples:
        out.append(f"      | {e['etiqueta']} | {e['medida']} | {e['valor']} | {e['resultado']} |")
    return out


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s and not s[:2].isupper() else s


# ---------------------------------------------------------------------------- Playwright (playwright-bdd)

_STEP = re.compile(r"^\s*(Dado|Cuando|Entonces|Y|Pero)\s+(.*)$")


def _expression(text: str) -> tuple[str, list[str]]:
    """Texto del step → Cucumber Expression: literales "..." y <placeholders> pasan a {string}."""
    params: list[str] = []

    def take(m: re.Match) -> str:
        params.append("string")
        return "{string}"

    expr = re.sub(r'"[^"]*"|<[^>]+>', take, text)
    expr = re.sub(r"[()/\\]", lambda m: "\\" + m.group(0), expr)  # caracteres especiales de Cucumber Expressions
    return expr, params


def to_playwright_steps(feature: str) -> str:
    keyword_fn = {"Dado": "Given", "Cuando": "When", "Entonces": "Then"}
    seen: dict[str, tuple[str, int]] = {}
    current = "Given"
    for line in feature.splitlines():
        m = _STEP.match(line)
        if not m or line.strip().startswith("#"):
            continue
        kw, text = m.groups()
        current = keyword_fn.get(kw, current)
        expr, params = _expression(text)
        seen.setdefault(expr, (current, len(params)))
    out = ["// Generado por tbg (`tbg export --format playwright`). Esqueleto de steps para playwright-bdd:",
           "// https://vitalets.github.io/playwright-bdd — implementar cada TODO con acciones de Playwright.",
           "import { createBdd } from 'playwright-bdd';", "", "const { Given, When, Then } = createBdd();", ""]
    for expr, (fn, n) in seen.items():
        args = ", ".join(f"arg{i + 1}: string" for i in range(n))
        sig = "{ page }" + (f", {args}" if args else "")
        lit = expr.replace("\\", "\\\\").replace("'", "\\'")
        out += [f"{fn}('{lit}', async ({sig}) => {{", "  // TODO: implementar", "  throw new Error('Step pendiente');",
                "});", ""]
    return "\n".join(out)


# ---------------------------------------------------------------------------- para leer / redactar con otra IA


def frames_markdown(fs: FrameSet) -> str:
    """Los casos tal como los diseñó tbg (qué probar, datos, esperado, supuestos), sin redacción de pasos."""
    out = [f"# Casos diseñados — {fs.story_id}: {fs.title}", "",
           f"{len(fs.frames)} casos · criterios cubiertos {fs.coverage.ac_percent:g}% · generados por tbg (modelo {fs.model_hash})", "",
           "| Caso | Tipo | Prioridad | Criterios | Qué probar |", "|---|---|---|---|---|"]
    out += [f"| {f.case_id} | {f.type} | {f.priority} | {', '.join(f.ac_refs) or 'exploratorio'} | {f.title_hint} |"
            for f in fs.frames]
    for f in fs.frames:
        out += ["", f"## {f.case_id} — {f.title_hint}", "",
                f"- **Tipo / prioridad**: {f.type} · {f.priority}{' · humo' if f.smoke else ''}{' · exploratorio' if f.exploratory else ''}",
                f"- **Criterios**: {', '.join(f.ac_refs) or '—'}",
                f"- **Por qué esta prioridad**: {f.risk_reason}"]
        if f.data:
            out.append("- **Datos de prueba**: " + " · ".join(f"`{k}`: {v}" for k, v in f.data.items()))
        if f.examples:
            out.append("- **Valores límite**: " + " · ".join(f"{e['etiqueta']} ({e['medida']}) → {e['resultado']}" for e in f.examples))
        out += [f"- **Se espera**: {e}" for e in f.expected_hints]
        out += [f"- **[SUPUESTO]** {s}" for s in f.supuestos]
    return "\n".join(out) + "\n"


def drafting_brief(story_text: str, fs: FrameSet, existing: SuiteDraft | None = None) -> str:
    """Paquete autocontenido para que CUALQUIER IA redacte los casos pendientes; la respuesta se importa y valida."""
    import json

    from .ai import DRAFT_SYSTEM

    done = {c.frame_id for c in existing.cases} if existing else set()
    keep = ("frame_id", "case_id", "type", "title_hint", "ac_refs", "data", "expected_hints", "supuestos", "exploratory")
    pending = [{k: getattr(f, k) for k in keep} for f in fs.frames if f.frame_id not in done]
    return "\n".join([
        f"# Redactar casos de prueba — {fs.story_id}", "",
        "Copiá TODO este archivo en tu IA (ChatGPT, Gemini, Claude, Copilot…) y pegá su respuesta en la app",
        "(paso 4 → «Importar redacción») o guardala como JSON y usá `tbg import-suite`.", "",
        "## Instrucciones", "", DRAFT_SYSTEM, "",
        "## Historia de usuario", "", story_text.strip(), "",
        f"## Casos a redactar ({len(pending)})", "", "```json", json.dumps(pending, ensure_ascii=False, indent=1), "```", "",
        "## Formato de la respuesta", "",
        'Respondé SOLO con un bloque JSON: {"cases": [{"frame_id": "...", "title": "Verificar que …", "preconditions": "...", '
        '"steps": [{"action": "...", "expected": "..."}], "evidence": "...", "notes": ""}]} — un elemento por caso de la lista, '
        "con el mismo frame_id.", ""])


def import_drafts(text: str, fs: FrameSet, existing: SuiteDraft | None = None) -> tuple[SuiteDraft, list[str]]:
    """Incorpora la redacción que devolvió otra IA. Tolera texto alrededor y ```json```; descarta casos de frames
    que no existen; lo ya redactado se conserva salvo que la respuesta traiga ese mismo frame."""
    import json

    from pydantic import ValidationError

    from .ai import _json

    try:
        data = _json(text)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"La respuesta no contiene un JSON válido ({e}).") from e
    raw_cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(raw_cases, list):
        raise ValueError('El JSON no tiene la lista "cases".')
    known = {f.frame_id for f in fs.frames}
    merged = {c.frame_id: c for c in (existing.cases if existing else [])}
    notes: list[str] = []
    added = 0
    for i, rc in enumerate(raw_cases, 1):
        try:
            case = CaseDraft.model_validate(rc)
        except ValidationError as e:
            notes.append(f"Caso {i} descartado: formato inválido ({e.errors()[0]['msg']}).")
            continue
        if case.frame_id not in known:
            notes.append(f"Caso {i} descartado: el frame {case.frame_id} no existe en el diseño actual.")
            continue
        merged[case.frame_id] = case
        added += 1
    order = {f.frame_id: i for i, f in enumerate(fs.frames)}
    suite = SuiteDraft(story_id=fs.story_id, cases=sorted(merged.values(), key=lambda c: order[c.frame_id]))
    return suite, [f"{added} casos importados."] + notes
