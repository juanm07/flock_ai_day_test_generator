"""App web local (`tbg ui`) para QA y PO: pegar una HU o un bug, ver cómo se interpretó, responder las preguntas,
revisar y editar los casos, y exportar a Gherkin / Playwright.

Todo el estado vive en work/<ID>/ (mismo formato que el CLI y los agentes): si hay un LLM configurado la app lo llama;
si no, muestra el comando para que lo haga el agente (Claude Code / Pi) y lee lo que deja en la carpeta.
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import ai, bug, export, flows, llm, minorities, pipeline, po, workspace
from ..render import render_bug, render_suite
from ..schemas import CaseDraft, Step, SuiteDraft
from ..validate import validate

app = FastAPI(title="tbg — Test & Bug Generator")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
templates.env.globals["L"] = bug.LABELS
templates.env.globals["PRESETS"] = llm.PRESETS

# ---------------------------------------------------------------------------- protecciones para un deploy
# TBG_UI_PASSWORD: si está, toda la app pide usuario/contraseña (HTTP Basic; usar siempre detrás de HTTPS).
# Con contraseña (o TBG_LOCK_SETTINGS=1) la configuración de IA no se puede cambiar desde la UI: la key vive solo en
# las variables de entorno del servidor y nunca se manda al navegador.
# TBG_AI_LIMIT_PER_HOUR: tope de operaciones con IA por persona/IP y por hora (default 30).
# TBG_MAX_INPUT: largo máximo de una HU o reporte pegado (default 20000 caracteres).

PASSWORD = os.environ.get("TBG_UI_PASSWORD", "")
SETTINGS_LOCKED = bool(PASSWORD) or os.environ.get("TBG_LOCK_SETTINGS") == "1"
AI_LIMIT = int(os.environ.get("TBG_AI_LIMIT_PER_HOUR", "30"))
MAX_INPUT = int(os.environ.get("TBG_MAX_INPUT", "20000"))
_AI_ROUTES = ("/analizar", "/redactar", "/bug/nuevo", "/hu/nueva")
_usage: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def guard(request: Request, call_next):
    if PASSWORD:
        auth = request.headers.get("authorization", "")
        ok = False
        if auth.startswith("Basic "):
            try:
                _, _, pwd = base64.b64decode(auth[6:]).decode().partition(":")
                ok = secrets.compare_digest(pwd.encode(), PASSWORD.encode())
            except (ValueError, UnicodeDecodeError):
                ok = False
        if not ok:
            return PlainTextResponse("Acceso restringido", status_code=401,
                                     headers={"WWW-Authenticate": 'Basic realm="tbg"'})
    if request.method == "POST" and request.url.path.endswith(_AI_ROUTES) and llm.available():
        who = request.headers.get("x-forwarded-for", request.client.host if request.client else "?").split(",")[0].strip()
        q, now = _usage[who], time.time()
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= AI_LIMIT:
            return PlainTextResponse(f"Límite de {AI_LIMIT} operaciones con IA por hora alcanzado. Probá más tarde.",
                                     status_code=429)
        q.append(now)
    return await call_next(request)


def _too_long(text: str) -> str | None:
    return f"El texto supera el máximo de {MAX_INPUT} caracteres." if len(text) > MAX_INPUT else None


def _page(request: Request, name: str, **ctx) -> HTMLResponse:
    ctx.update(request=request, llm=llm.config() if _llm_ok() else None, llm_label=_llm_label(), locked=SETTINGS_LOCKED,
               error=request.query_params.get("error"), ok=request.query_params.get("ok"))
    return templates.TemplateResponse(request, name, ctx)


def _llm_ok() -> bool:
    return llm.available()


def _llm_label() -> str:
    try:
        return llm.config().label
    except llm.LLMError as e:
        return f"configuración inválida: {e}"


def _back(url: str, error: str | None = None, ok: str | None = None) -> RedirectResponse:
    """Redirige con un mensaje. El mensaje va en la query, ANTES del #ancla (si va después el navegador lo descarta)."""
    path, _, anchor = url.partition("#")
    sep = "&" if "?" in path else "?"
    if error:
        path += f"{sep}error={quote(error)}"
    elif ok:
        path += f"{sep}ok={quote(ok)}"
    return RedirectResponse(path + (f"#{anchor}" if anchor else ""), status_code=303)


@app.exception_handler(Exception)
async def unexpected(request: Request, exc: Exception):
    """Cualquier error no previsto se muestra legible (y queda en work/_errores.log) en vez de un 500 en blanco."""
    import traceback

    log = workspace.root() / "_errores.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} {request.method} {request.url.path}\n{traceback.format_exc()}\n")
    except OSError:
        pass
    back = request.headers.get("referer") or "/"
    return _page(request, "error.html", detail=f"{type(exc).__name__}: {exc}", back=back, log=str(log))


# ---------------------------------------------------------------------------- inicio


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    hus = [{"id": h.id, "title": _safe_title(h), "stage": h.stage()} for h in workspace.list_hus()]
    bugs = []
    for b in workspace.list_bugs():
        f = b.facts()
        bugs.append({"id": b.id, "title": f.symptom.text if f else b.report()[:90], "ready": f is not None})
    return _page(request, "index.html", hus=hus, bugs=bugs)


def _safe_title(h: workspace.HUSpace) -> str:
    try:
        return h.story().title
    except OSError:
        return "—"


# ---------------------------------------------------------------------------- HU


@app.get("/hu/nueva", response_class=HTMLResponse)
def hu_new_form(request: Request):
    return _page(request, "hu_new.html")


@app.post("/hu/nueva")
def hu_new(texto: str = Form(...)):
    if err := _too_long(texto):
        return _back("/hu/nueva", error=err)
    sid, warns = flows.create_hu(texto)
    return _back(f"/hu/{sid}", ok="Historia guardada. " + " ".join(warns))


def _hu_context(sid: str) -> dict:
    space = workspace.HUSpace(sid)
    story = space.story()
    model = space.model()
    frames = space.frames()
    suite = space.suite()
    if model:
        model_t = pipeline.with_suggested_tags(story, model)
        findings, tags, gaps = pipeline.analyze(story, model_t)
    else:
        findings, tags, gaps = pipeline.analyze(story)
    report = validate(frames, suite) if frames and suite else None
    drafts = {c.frame_id: c for c in suite.cases} if suite else {}
    cons_path = space.dir / "consensus.json"
    consensus = json.loads(cons_path.read_text(encoding="utf-8")) if cons_path.exists() else None
    if consensus and model:
        consensus["items"] = [{"i": i, "text": minorities.describe(m, model), "votes": m["votes"], "total": m["total"],
                               "present": minorities.present(m, model), "kind": m["kind"]}
                              for i, m in enumerate(consensus.get("minorities", []))]
    bounds_params = {g.id: po.bounded_params(g, model_t) for g in gaps if g.asked} if model else {}
    stale = bool(frames and model and frames.model_hash != pipeline.model_hash(pipeline.with_suggested_tags(story, model)))
    return dict(sid=sid, space=space, story=story, model=model, frames=frames, suite=suite, findings=findings,
                tags=tags, gaps=gaps, report=report, drafts=drafts, consensus=consensus, bounds_params=bounds_params,
                stale=stale, raw=space.hu_path.read_text(encoding="utf-8"),
                params={p.name: p for p in model.parameters} if model else {})


@app.get("/hu/{sid}", response_class=HTMLResponse)
def hu_view(request: Request, sid: str):
    if not workspace.HUSpace(sid).hu_path.exists():
        return _back("/", error=f"No existe {sid}")
    return _page(request, "hu.html", **_hu_context(sid))


@app.post("/hu/{sid}/editar")
def hu_edit(sid: str, markdown: str = Form(...)):
    workspace.HUSpace(sid).save_hu(markdown)
    return _back(f"/hu/{sid}", ok="Historia actualizada. Si cambiaron los criterios, volvé a analizarla.")


@app.post("/hu/{sid}/analizar")
def hu_analyze(sid: str):
    try:
        result = flows.analyze_with_ai(sid)
    except llm.LLMError as e:
        return _back(f"/hu/{sid}#modelo", error=str(e))
    return _back(f"/hu/{sid}#preguntas", ok=f"Análisis listo: consenso de {result.n} lecturas independientes.")


@app.post("/hu/{sid}/minoria/{i}")
def hu_minority_add(sid: str, i: int):
    """Agrega al modelo un elemento que vio una sola lectura de la IA (decisión de una persona)."""
    space = workspace.HUSpace(sid)
    cons_path = space.dir / "consensus.json"
    items = json.loads(cons_path.read_text(encoding="utf-8")).get("minorities", []) if cons_path.exists() else []
    if space.model() is None or not 0 <= i < len(items):
        return _back(f"/hu/{sid}#modelo", error="No se encontró ese elemento.")
    try:
        flows.add_minority(sid, i)
    except ValueError as e:
        return _back(f"/hu/{sid}#modelo", error=str(e))
    extra = " Los casos se volvieron a diseñar (los ya redactados se conservan)." if space.frames_path.exists() else ""
    return _back(f"/hu/{sid}#modelo", ok="Agregado al modelo." + extra)


@app.post("/hu/{sid}/basico")
def hu_basic(sid: str):
    """Seguir sin IA: criterios literales y reglas (ver flows.basic_model)."""
    try:
        flows.basic_model(sid)
    except ValueError as e:
        return _back(f"/hu/{sid}#historia", error=str(e))
    return _back(f"/hu/{sid}#preguntas", ok="Seguimos sin IA: las preguntas y los casos salen de los criterios y las "
                 "reglas. Los datos y variantes se pueden agregar después analizando con IA.")


@app.post("/hu/{sid}/po")
async def hu_po(request: Request, sid: str):
    space = workspace.HUSpace(sid)
    story, model = space.story(), space.model()
    if model is None:
        return _back(f"/hu/{sid}#modelo", error="Primero completá el paso 2.")
    form = await request.form()
    model_t = pipeline.with_suggested_tags(story, model)
    _, _, gaps = pipeline.analyze(story, model_t)
    data = {"story_id": model.story_id, "preguntas": []}
    for g in (g for g in gaps if g.asked):
        item = {"id": g.id, "respuesta": form.get(f"resp::{g.id}", ""), "acepto_default": bool(form.get(f"def::{g.id}"))}
        lim = {}
        for p in po.bounded_params(g, model_t):
            lo, hi = form.get(f"min::{g.id}::{p}", "").strip(), form.get(f"max::{g.id}::{p}", "").strip()
            if lo or hi:
                try:
                    lim[p] = {"min": _num(lo), "max": _num(hi), "unidad": form.get(f"unit::{g.id}::{p}", "chars")}
                except ValueError:
                    return _back(f"/hu/{sid}#preguntas", error=f"{p}: mínimo y máximo deben ser números")
        if lim:
            item["limites"] = lim
        data["preguntas"].append(item)
    try:
        res = po.apply_data(data, model_t, gaps)
    except ValueError as e:
        return _back(f"/hu/{sid}#preguntas", error=str(e))
    model_t.feature_tags = model.feature_tags
    space.save_model(model_t)
    if space.frames_path.exists():
        space.save_frames(pipeline.build(story, model_t))
    return _back(f"/hu/{sid}#casos", ok=f"Aplicado: {po.summary(res)}.")


def _num(s: str):
    if not s:
        return None
    return int(s) if s.lstrip("-").isdigit() else float(s)


@app.post("/hu/{sid}/generar")
def hu_generate(sid: str):
    space = workspace.HUSpace(sid)
    if space.model() is None:
        return _back(f"/hu/{sid}#modelo", error="Primero completá el paso 2 (analizar con IA o «Seguir sin IA»).")
    fs = pipeline.build(space.story(), space.model())
    space.save_frames(fs)
    return _back(f"/hu/{sid}#casos", ok=f"{len(fs.frames)} casos diseñados.")


@app.post("/hu/{sid}/redactar")
def hu_draft(sid: str):
    space = workspace.HUSpace(sid)
    if space.frames() is None:
        return _back(f"/hu/{sid}#casos", error="Primero diseñá los casos.")
    try:
        suite = ai.draft_cases(space.story(), space.frames(), space.suite())
    except llm.LLMError as e:
        return _back(f"/hu/{sid}#casos", error=str(e))
    space.save_suite(suite)
    return _back(f"/hu/{sid}#casos", ok="Casos redactados y validados.")


@app.post("/hu/{sid}/importar")
async def hu_import(request: Request, sid: str):
    """Importa la redacción hecha por otra IA (pegada o como archivo) y la valida con el gate."""
    space = workspace.HUSpace(sid)
    fs = space.frames()
    if fs is None:
        return _back(f"/hu/{sid}#casos", error="Primero diseñá los casos.")
    form = await request.form()
    text = (form.get("respuesta") or "").strip()
    upload = form.get("archivo")
    if not text and upload is not None and hasattr(upload, "read"):
        text = (await upload.read()).decode("utf-8", errors="replace")
    if not text:
        return _back(f"/hu/{sid}#casos", error="Pegá la respuesta de la IA o subí el archivo.")
    if len(text) > MAX_INPUT * 10:  # una suite redactada es más larga que una HU: tope más amplio
        return _back(f"/hu/{sid}#casos", error="La respuesta es demasiado larga.")
    try:
        suite, notes = export.import_drafts(text, fs, space.suite())
    except ValueError as e:
        return _back(f"/hu/{sid}#casos", error=str(e))
    space.save_suite(suite)
    report = validate(fs, suite)
    status = "Control de calidad OK." if report.ok else "El control de calidad marcó problemas: revisalos abajo o pedile a la IA que los corrija."
    return _back(f"/hu/{sid}#casos", ok=" ".join(notes) + " " + status)


@app.get("/hu/{sid}/caso/{fid}", response_class=HTMLResponse)
def case_view(request: Request, sid: str, fid: str):
    ctx = _hu_context(sid)
    frame = next((f for f in ctx["frames"].frames if f.frame_id == fid), None) if ctx["frames"] else None
    if frame is None:
        return _back(f"/hu/{sid}#casos", error="Caso inexistente")
    issues = []
    if ctx["report"]:
        issues = [f"{c.id} {d}" for c in ctx["report"].checks if not c.passed for d in c.details
                  if d.startswith(frame.case_id) or fid in d]
    return _page(request, "case.html", frame=frame, draft=ctx["drafts"].get(fid), issues=issues, **ctx)


@app.post("/hu/{sid}/caso/{fid}")
async def case_save(request: Request, sid: str, fid: str):
    form = await request.form()
    actions, expected = form.getlist("action"), form.getlist("expected")
    steps = [Step(action=a.strip(), expected=e.strip()) for a, e in zip(actions, expected) if a.strip() or e.strip()]
    if not steps:
        return _back(f"/hu/{sid}/caso/{fid}", error="El caso necesita al menos un paso")
    space = workspace.HUSpace(sid)
    suite = space.suite() or SuiteDraft(story_id=space.frames().story_id, cases=[])
    case = CaseDraft(frame_id=fid, title=form.get("title", "").strip(), preconditions=form.get("preconditions", "").strip(),
                     steps=steps, evidence=form.get("evidence", "").strip(), notes=form.get("notes", "").strip())
    suite.cases = [c for c in suite.cases if c.frame_id != fid] + [case]
    order = {f.frame_id: i for i, f in enumerate(space.frames().frames)}
    suite.cases.sort(key=lambda c: order.get(c.frame_id, 10**6))
    space.save_suite(suite)
    return _back(f"/hu/{sid}/caso/{fid}", ok="Caso guardado y revalidado.")


@app.get("/hu/{sid}/descargar/{kind}")
def hu_download(sid: str, kind: str):
    ctx = _hu_context(sid)
    fs, suite, model = ctx["frames"], ctx["suite"], ctx["model"]
    if fs is None:
        return _back(f"/hu/{sid}#casos", error="Primero diseñá los casos.")
    if kind in ("disenados", "paquete"):
        body = export.frames_markdown(fs) if kind == "disenados" else export.drafting_brief(ctx["raw"], fs, suite)
        name = f"{sid}_casos_disenados.md" if kind == "disenados" else f"{sid}_para_redactar.md"
        return Response(body, media_type="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{name}"'})
    if not suite:
        return _back(f"/hu/{sid}#exportar", error="Primero redactá los casos (con IA, con otra IA o a mano).")
    if kind == "md":
        body, name = render_suite(fs, model, suite, ctx["report"]), f"suite_{sid}.md"
    elif kind == "feature":
        body, name = export.to_gherkin(fs, suite), f"{sid}.feature"
    elif kind == "steps":
        body, name = export.to_playwright_steps(export.to_gherkin(fs, suite)), f"{sid}.steps.ts"
    else:
        return _back(f"/hu/{sid}#exportar", error="Formato desconocido")
    return Response(body, media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ---------------------------------------------------------------------------- configuración de IA


@app.get("/config", response_class=HTMLResponse)
def config_view(request: Request):
    active = llm.active_preset()
    preset = request.query_params.get("preset") or active or "anthropic"
    if preset not in llm.PRESETS:
        preset = "anthropic"
    try:
        current = llm.config()
    except llm.LLMError:
        current = None
    prof = llm.profile_config(preset)
    models = list(llm.profile(preset).get("models") or [])
    if prof.model and prof.model not in models:
        models.insert(0, prof.model)
    return _page(request, "config.html", preset=preset, prof=prof, models=models, active=active, current=current,
                 env_config=bool(current and current.source == "entorno"))


def _config_form_save(form, preset: str) -> None:
    model = (form.get("model_other") or "").strip() if form.get("model") == "__otro__" else (form.get("model") or "")
    p = llm.PRESETS[preset]
    llm.save(preset, model, form.get("base_url") or p["base_url"], form.get("api_key") or None,
             form.get("effort") or "medium", activate=True)


@app.post("/config")
async def config_save(request: Request):
    form = await request.form()
    preset = form.get("preset", "")
    if preset not in llm.PRESETS:
        return _back("/config", error="Proveedor desconocido.")
    if SETTINGS_LOCKED:
        return _back("/config", error="La configuración está bloqueada: en un deploy se define con variables de entorno.")
    if form.get("action") == "borrar":
        llm.clear(preset)
        return _back(f"/config?preset={preset}", ok=f"Se borró la configuración y la key de {llm.PRESETS[preset]['label']}.")
    _config_form_save(form, preset)
    if form.get("action") == "probar":
        return _config_test(preset)
    prof = llm.profile_config(preset)
    if not prof.model:
        return _back(f"/config?preset={preset}", ok="Guardado. Falta elegir el modelo: probá la conexión para ver la lista.")
    return _back(f"/config?preset={preset}", ok=f"Listo: la app usa {prof.label}.")


def _config_test(preset: str) -> RedirectResponse:
    prof = llm.profile_config(preset)
    if prof.provider == "openai" and not prof.base_url and preset != "openai":
        return _back(f"/config?preset={preset}", error="Falta el endpoint (opciones avanzadas).")
    try:
        models = llm.list_models(prof)
    except Exception as e:  # key inválida, endpoint mal escrito, sin red… (cada SDK tiene sus propias excepciones)
        return _back(f"/config?preset={preset}", error=f"No se pudo conectar: {type(e).__name__}: {str(e)[:200]}")
    llm.save_models(preset, models)
    if not prof.model:
        return _back(f"/config?preset={preset}", ok=f"Conecta: {len(models)} modelos disponibles. Elegí uno de la lista y guardá.")
    if prof.model not in models:
        return _back(f"/config?preset={preset}",
                     error=f"Conecta, pero el modelo «{prof.model}» no está entre los {len(models)} disponibles: elegí otro.")
    return _back(f"/config?preset={preset}", ok=f"Conexión OK con {prof.label} ({len(models)} modelos disponibles).")


# ---------------------------------------------------------------------------- bugs


@app.get("/bug/nuevo", response_class=HTMLResponse)
def bug_new_form(request: Request):
    return _page(request, "bug_new.html")


@app.post("/bug/nuevo")
def bug_new(texto: str = Form(...)):
    if err := _too_long(texto):
        return _back("/bug/nuevo", error=err)
    bid = workspace.next_id("BUG")
    space = workspace.BugSpace(bid)
    space.save_report(texto)
    if llm.available():
        return bug_analyze(bid)
    return _back(f"/bug/{bid}", ok="Reporte guardado.")


@app.post("/bug/{bid}/analizar")
def bug_analyze(bid: str):
    space = workspace.BugSpace(bid)
    try:
        space.save_facts(ai.extract_bug(space.report(), bid))
    except llm.LLMError as e:
        return _back(f"/bug/{bid}", error=str(e))
    return _back(f"/bug/{bid}", ok="Bug analizado: todos los hechos tienen cita verificada.")


@app.get("/bug/{bid}", response_class=HTMLResponse)
def bug_view(request: Request, bid: str):
    space = workspace.BugSpace(bid)
    if not space.report_path.exists():
        return _back("/", error=f"No existe {bid}")
    facts = space.facts()
    bc = bug.check(facts, space.report()) if facts else None
    return _page(request, "bug.html", bid=bid, space=space, report=space.report(), bc=bc)


@app.get("/bug/{bid}/descargar")
def bug_download(bid: str):
    space = workspace.BugSpace(bid)
    bc = bug.check(space.facts(), space.report())
    return Response(render_bug(bc, space.report()), media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="bug_normalizado_{bid}.md"'})


