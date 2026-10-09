"""Las tareas del LLM cuando la app lo llama directo. Mismo contrato que el modo agente (AGENTS.md), con el patrón
"assured": cada salida se valida con los chequeos deterministas de tbg y, si falla, se reintenta mostrándole al
modelo los errores concretos. Nunca se acepta una salida que no pase los filtros.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor

from pydantic import ValidationError

from . import bug, llm, modelcheck, rules
from .consensus import ConsensusResult, merge
from .hu import UserStory, parse_story
from .quotes import quote_in
from .schemas import BugFacts, CaseDraft, FrameSet, SuiteDraft, TestModel
from .validate import validate

MAX_RETRIES = 2


def _json(text: str) -> dict:
    """Extrae el primer objeto JSON de la respuesta (tolera ```json … ``` y texto alrededor)."""
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(raw)


def _loop(system: str, user: str, check, max_tokens: int = 32000):
    """Llama al LLM, parsea y valida con `check(dict) -> (resultado, errores)`; reintenta con los errores."""
    prompt, last = user, []
    for _ in range(MAX_RETRIES + 1):
        text = llm.complete(system, prompt, max_tokens)
        try:
            data = _json(text)
        except (json.JSONDecodeError, ValueError) as e:
            last = [f"La respuesta no es JSON válido: {e}"]
        else:
            try:
                result, last = check(data if isinstance(data, dict) else {})
            except (TypeError, AttributeError, KeyError, ValueError) as e:  # forma inesperada: se le explica y reintenta
                result, last = None, [f"La estructura del JSON no es la pedida ({type(e).__name__}: {e})"]
            if not last:
                return result
        prompt = (user + "\n\n## Tu respuesta anterior fue rechazada por los validadores de tbg\n"
                  + "\n".join(f"- {e}" for e in last[:30]) + "\n\nCorregí esos puntos y devolvé el JSON completo de nuevo.")
    raise llm.LLMError("La salida del LLM no pasó la validación tras reintentos: " + "; ".join(last[:5]))


# ---------------------------------------------------------------------------- HU en cualquier formato


NORMALIZE_SYSTEM = """Reformateás historias de usuario al formato de un equipo de QA SIN cambiar sus palabras.
Devolvé SOLO un JSON: {"id": "...", "titulo": "...", "como": "...", "quiero": "...", "para": "... o null",
"criterios": ["texto literal del criterio 1", ...], "notas": "texto literal o null"}.
Reglas: copiá los textos literalmente del original (podés recortar viñetas o numeración, nunca reformular).
Si no hay ID, usá null. Si un criterio está en formato Dado/Cuando/Entonces, copialo en una sola línea.
Si el texto no tiene criterios de aceptación, devolvé "criterios": [] (no los inventes)."""


def with_heading(raw: str, parsed: UserStory, fallback_id: str) -> str:
    """Si la HU no trae encabezado `## ID — Título`, se lo agrega (con su ID si lo tenía, si no uno nuevo)."""
    if re.search(r"^#{1,6}\s*[A-Z][A-Z0-9]{0,9}-[A-Z]?\d+\s*[—–:-]", raw, re.M):
        return raw
    sid = parsed.id if parsed.id != "HU-000" else fallback_id
    title = parsed.title if parsed.title != "Sin título" else "Historia sin título"
    return f"## {sid} — {title}\n\n{raw.strip()}\n"


def to_markdown(d: dict, fallback_id: str) -> str:
    sid = d.get("id") if isinstance(d.get("id"), str) and re.fullmatch(r"[A-Z][A-Z0-9]{0,9}-[A-Z]?\d+", d["id"]) else fallback_id
    lines = [f"## {sid} — {d.get('titulo') or 'Sin título'}", ""]
    enun = f"**Como** {d.get('como') or '[PENDIENTE: rol]'},\n**quiero** {d.get('quiero') or '[PENDIENTE]'}"
    lines.append(enun + (f",\n**para** {d['para']}." if d.get("para") else "."))
    lines += ["", "**Criterios de aceptación:**", ""]
    lines += [f"{i}. {c}" for i, c in enumerate(d.get("criterios") or [], 1)]
    if d.get("notas"):
        lines += ["", f"**Notas del equipo:** {d['notas']}"]
    return "\n".join(lines) + "\n"


def normalize_hu(raw: str, fallback_id: str) -> tuple[str, list[str]]:
    """Texto libre → markdown estándar. Devuelve (markdown, avisos). Sin LLM, intenta con el parser determinista."""
    parsed = parse_story(raw)
    if parsed.acceptance_criteria and parsed.want:  # el parser determinista la entiende: no hace falta IA
        return with_heading(raw, parsed, fallback_id), []
    if not llm.available():
        missing = [x for x, ok in (("criterios de aceptación", parsed.acceptance_criteria),
                                   ("el «quiero» (qué necesita el usuario)", parsed.want)) if not ok]
        warn = [f"No se detectaron {' ni '.join(missing)}. Revisá el texto (editalo en el paso 1) o configurá una IA "
                "para que lo ordene."]
        return with_heading(raw, parsed, fallback_id), warn

    def check(d: dict):
        crit = d.get("criterios") or []
        if not isinstance(crit, list) or not all(isinstance(c, str) for c in crit):
            return d, ["«criterios» debe ser una lista de textos"]
        errs = [f"El criterio «{c}» no aparece literalmente en el texto original" for c in crit if not quote_in(c, raw)]
        for k in ("como", "quiero"):
            if d.get(k) and not quote_in(d[k], raw):
                errs.append(f"«{k}» no es literal del original")
        return d, errs

    d = _loop(NORMALIZE_SYSTEM, f"Historia de usuario original:\n\n{raw}", check, max_tokens=8000)
    warns = [] if d.get("criterios") else ["La HU no tiene criterios de aceptación: se van a generar solo preguntas."]
    return to_markdown(d, fallback_id), warns


# ---------------------------------------------------------------------------- extracción del TestModel


def _extract_system() -> str:
    vocab = ", ".join(rules.load("tags"))
    return f"""Sos un analista de QA. Extraés de una historia de usuario un TestModel (Category-Partition Method) en JSON.

Reglas de contenido:
- acceptance_criteria[].text: cada criterio copiado LITERAL de la HU, ids CA-1, CA-2… en orden.
- parameters: uno por cada dato que ingresa o elige el usuario y por cada condición del sistema mencionada
  explícitamente (estado de datos, disponibilidad de un servicio nombrado). NO modeles seguridad, expiración,
  sesiones, rate limit, permisos ni navegadores: las reglas de tbg ya los cubren.
- choices: particiones de equivalencia; la primera "valid" es la típica; "invalid" = el sistema debe rechazarla;
  "exception" = condición adversa del entorno. example: valor concreto y realista ("" = vacío).
- expected + quote: solo si la HU dice qué pasa (quote = cita textual). Si no lo dice: expected null.
- assumed: true si que sea válida/inválida es suposición tuya.
- bounds solo si la HU da números; si deberían existir y no están: bounds null y bounds_relevant true.
- feature_tags solo de este vocabulario: {vocab}.
Convenciones de nombres (snake_case, sin tildes): parámetro = nombre del campo como lo nombra la HU, uno por campo
(desde y hasta separados); servicio → <servicio>_estado con disponible/caido; elección inválida = el problema
(vacio, formato_invalido); validación entre dos campos va en el segundo campo como anterior_a_<primer_campo>.
Devolvé SOLO el JSON del TestModel, que debe cumplir este JSON Schema:
{json.dumps(TestModel.model_json_schema(), ensure_ascii=False)}"""


def extract_model(story: UserStory) -> TestModel:
    def check(d: dict):
        try:
            m = TestModel.model_validate(d)
        except ValidationError as e:
            return None, [f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()]
        return m, [f"{i.path}: {i.message}" for i in modelcheck.check(m, story) if i.level == "error"]

    return _loop(_extract_system(), f"Historia de usuario:\n\n{story.text}", check)


def extract_with_consensus(story: UserStory, n: int = 3) -> tuple[list[TestModel], ConsensusResult]:
    """n extracciones independientes (en paralelo, sin compartir contexto) + voto mayoritario."""
    with ThreadPoolExecutor(max_workers=n) as pool:
        models = list(pool.map(lambda _: extract_model(story), range(n)))
    return models, merge(models)


# ---------------------------------------------------------------------------- redacción de casos


DRAFT_SYSTEM = """Sos un QA senior. Redactás casos de prueba a partir de "frames" que diseñó una herramienta
determinista. Exactamente un caso por frame recibido, sin agregar ni quitar.
Reglas (las verifica un validador; si no se cumplen, tu respuesta se rechaza):
- title: "Verificar que …" (o "Explorar …" si el frame es exploratorio). Se entiende solo.
- steps: lista de {action, expected}. UNA acción por paso: nunca "ingresar X y confirmar".
- expected: observable (qué se ve, qué mensaje exacto, a dónde navega). Prohibido: "correctamente", "se ve bien",
  "funciona bien", "como corresponde", "adecuadamente", "sin problemas", "exitosamente".
- Usá los valores de `data` LITERALES en precondiciones o pasos (salvo los que están entre paréntesis o son ''); nunca
  "un email válido" ni datos abstractos.
- Si el frame trae `supuestos`, el resultado esperado afectado lleva "[SUPUESTO: …]".
- Para dependencias entre casos usá el frame_id (F-xxxxxxxx), nunca CP-NNN.
Devolvé SOLO un JSON: {"cases": [{"frame_id", "title", "preconditions", "steps": [{"action","expected"}],
"evidence", "notes"}]}"""


def _frame_brief(fs: FrameSet, frame_ids: list[str]) -> str:
    keep = ("frame_id", "type", "title_hint", "ac_refs", "data", "expected_hints", "supuestos", "exploratory")
    frames = [{k: getattr(f, k) for k in keep} for f in fs.frames if f.frame_id in frame_ids]
    return json.dumps(frames, ensure_ascii=False, indent=1)


def draft_cases(story: UserStory, fs: FrameSet, existing: SuiteDraft | None = None, batch: int = 8) -> SuiteDraft:
    """Redacta los frames que no tienen caso (los existentes se conservan) y valida con el gate de tbg."""
    done = {c.frame_id: c for c in (existing.cases if existing else [])}
    todo = [f.frame_id for f in fs.frames if f.frame_id not in done]
    batches = [todo[i:i + batch] for i in range(0, len(todo), batch)]
    known = {f.frame_id for f in fs.frames}

    def run(ids: list[str]) -> list[CaseDraft]:
        others = SuiteDraft(story_id=fs.story_id, cases=[c for c in done.values()])

        def check(d: dict):
            try:
                cases = [CaseDraft.model_validate(c) for c in d.get("cases", [])]
            except ValidationError as e:
                return None, [str(e)]
            got = {c.frame_id for c in cases}
            errs = [f"Falta el caso del frame {i}" for i in ids if i not in got]
            errs += [f"Frame desconocido o no pedido: {c.frame_id}" for c in cases if c.frame_id not in ids]
            if errs:
                return None, errs
            report = validate(fs.model_copy(update={"frames": [f for f in fs.frames if f.frame_id in ids or f.frame_id in done]}),
                              SuiteDraft(story_id=fs.story_id, cases=others.cases + cases))
            label = {f.frame_id: f.case_id for f in fs.frames}
            mine = {label[i] for i in ids}
            errs = [f"{c.id}: {d_}" for c in report.checks if c.critical and not c.passed for d_ in c.details
                    if any(d_.startswith(x) for x in mine) or c.id == "C1"]
            return cases, errs

        user = (f"Historia de usuario:\n{story.text}\n\nFrames a redactar (con su case_id para referencia):\n"
                + _frame_brief(fs, ids)
                + "\n\ncase_id de cada frame: " + json.dumps({f.frame_id: f.case_id for f in fs.frames if f.frame_id in known}))
        return _loop(DRAFT_SYSTEM, user, check)

    with ThreadPoolExecutor(max_workers=max(1, min(4, len(batches)))) as pool:
        for cases in pool.map(run, batches):
            for c in cases:
                done[c.frame_id] = c
    order = {f.frame_id: i for i, f in enumerate(fs.frames)}
    return SuiteDraft(story_id=fs.story_id, cases=sorted((c for c in done.values() if c.frame_id in order),
                                                         key=lambda c: order[c.frame_id]))


# ---------------------------------------------------------------------------- bugs


def _bug_system() -> str:
    return f"""Sos un QA senior haciendo triage. Extraés los HECHOS de un reporte de bug informal en JSON.
Reglas: cada hecho lleva `quote`, una cita TEXTUAL del reporte (se verifica; una paráfrasis se rechaza). Lo que el
reporte no dice va null (nunca inventes versión, ambiente ni texto de error). error_text solo si el reporte da el
texto; si lo parafrasea, citá su frase igual. features (data_loss, security, blocks_critical_flow, …): true/false
CON cita, o null si el reporte no lo dice. Conjeturas → hypotheses (by: reporter|agent), nunca observed. Pasos sin
respaldo textual (navegación obvia) van con quote null. Devolvé SOLO el JSON, que debe cumplir este JSON Schema:
{json.dumps(BugFacts.model_json_schema(), ensure_ascii=False)}"""


def extract_bug(report: str, bug_id: str) -> BugFacts:
    def check(d: dict):
        d["bug_id"] = bug_id
        try:
            facts = BugFacts.model_validate(d)
        except ValidationError as e:
            return None, [f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()]
        bc = bug.check(facts, report)
        return facts, [f"{r.path}: la cita «{r.quote}» no está en el reporte; corregila o quitá el dato" for r in bc.rejected]

    return _loop(_bug_system(), f"Reporte original:\n\n{report}", check, max_tokens=16000)

