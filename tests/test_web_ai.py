"""App web y capa de IA, con un LLM falso (sin llamadas reales)."""

import json

import pytest
from fastapi.testclient import TestClient

from tbg import ai, llm
from tbg.consensus import merge
from tbg.schemas import BugFacts, SuiteDraft

from .conftest import ROOT


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TBG_WORK_DIR", str(tmp_path))
    monkeypatch.setenv("TBG_LLM", "none")
    from tbg.web.app import app
    return TestClient(app)


def test_assured_loop_retries_with_validator_errors(story, monkeypatch, model):
    bad = model.model_copy(deep=True)
    bad.acceptance_criteria[0].text = "Un criterio inventado que no está en la HU."
    replies = iter([bad.model_dump_json(), "```json\n" + model.model_dump_json() + "\n```"])
    prompts = []

    def fake(system, user, max_tokens=0):
        prompts.append(user)
        return next(replies)

    monkeypatch.setattr(llm, "complete", fake)
    out = ai.extract_model(story)
    assert out == model
    assert "rechazada por los validadores" in prompts[1] and "no aparece literalmente" in prompts[1]


def test_assured_loop_gives_up_instead_of_accepting_invalid_output(story, monkeypatch):
    monkeypatch.setattr(llm, "complete", lambda *a, **k: '{"story_id": "x"}')
    with pytest.raises(llm.LLMError, match="no pasó la validación"):
        ai.extract_model(story)


def test_bug_extraction_rejects_invented_quotes(monkeypatch):
    report = (ROOT / "ejemplos" / "reporte-001.md").read_text(encoding="utf-8")
    good = BugFacts.model_validate_json((ROOT / "ejemplos" / "reporte-001.facts.json").read_text(encoding="utf-8"))
    bad = good.model_copy(deep=True)
    bad.observed[0].quote = "la pantalla se puso azul"
    replies = iter([bad.model_dump_json(), good.model_dump_json()])
    monkeypatch.setattr(llm, "complete", lambda *a, **k: next(replies))
    assert ai.extract_bug(report, "BUG-001").observed[0].quote == "me tira un error rojo"


def test_full_hu_flow_through_the_web(client, monkeypatch, model):
    hu = (ROOT / "ejemplos" / "hu-101.md").read_text(encoding="utf-8")
    r = client.post("/hu/nueva", data={"texto": hu}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/hu/HU-101")
    page = client.get("/hu/HU-101").text
    assert "CA-4" in page and "Preguntas para el PO" in page and "AGENTS.md" in page  # sin LLM: instrucciones al agente

    monkeypatch.setattr(ai, "extract_with_consensus", lambda story, n=3: ([model] * 3, merge([model] * 3)))
    monkeypatch.setattr(llm, "available", lambda: True)
    client.post("/hu/HU-101/analizar")
    monkeypatch.setattr(llm, "available", lambda: False)
    assert "Nueva contraseña definida desde el enlace" in client.get("/hu/HU-101").text

    client.post("/hu/HU-101/generar")
    client.post("/hu/HU-101/po", data={"min::credential.policy::password_nueva": "8",
                                       "max::credential.policy::password_nueva": "64",
                                       "unit::credential.policy::password_nueva": "chars",
                                       "resp::token.expiration": "1 hora"})
    page = client.get("/hu/HU-101").text
    assert "6/6" in page  # valores límite cubiertos tras la respuesta del PO

    from tbg import workspace
    space = workspace.HUSpace("HU-101")
    suite = SuiteDraft.model_validate_json((ROOT / "ejemplos" / "hu-101.suite.json").read_text(encoding="utf-8"))
    space.save_suite(suite)
    borde = next(f for f in space.frames().frames if f.type == "Borde")
    r = client.post(f"/hu/HU-101/caso/{borde.frame_id}", data={
        "title": "Verificar el límite inferior de la contraseña", "preconditions": "Enlace vigente abierto",
        "action": ["Ingresar cada valor de la tabla", ""], "expected": ["Se acepta o rechaza según la tabla", ""],
        "evidence": "Screenshot por valor", "notes": ""})
    assert r.status_code == 200 and "Caso guardado" in r.text
    feature = client.get("/hu/HU-101/descargar/feature").text
    assert "Esquema del escenario" in feature and "@CP-001" in feature
    assert "createBdd" in client.get("/hu/HU-101/descargar/steps").text


def test_bug_flow_without_llm_shows_agent_instructions_then_analysis(client, monkeypatch):
    report = (ROOT / "ejemplos" / "reporte-001.md").read_text(encoding="utf-8")
    r = client.post("/bug/nuevo", data={"texto": report}, follow_redirects=False)
    bid = r.headers["location"].split("/")[2].split("?")[0]
    assert "Flujo B" in client.get(f"/bug/{bid}").text
    facts = json.loads((ROOT / "ejemplos" / "reporte-001.facts.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(ai, "extract_bug", lambda rep, b: BugFacts.model_validate({**facts, "bug_id": b}))
    client.post(f"/bug/{bid}/analizar")
    page = client.get(f"/bug/{bid}").text
    assert "Severidad S2 preliminar" in page and "pérdida de datos → S1" in page
    assert "BUG-" in client.get(f"/bug/{bid}/descargar").text


# ---------------------------------------------------------------------------- sin IA, configuración y protecciones


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    """App sin ninguna IA por entorno y con la configuración en un archivo temporal."""
    for var in ("TBG_LLM", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "TBG_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("TBG_WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setenv("TBG_CONFIG", str(tmp_path / "cfg" / "config.json"))
    from tbg.web import app as webapp
    return webapp, TestClient(webapp.app)


def test_no_ai_path_still_yields_questions_and_cases(fresh):
    _, c = fresh
    c.post("/hu/nueva", data={"texto": (ROOT / "ejemplos" / "hu-101.md").read_text(encoding="utf-8")})
    assert "Seguir sin IA" in c.get("/hu/HU-101").text
    c.post("/hu/HU-101/basico")
    c.post("/hu/HU-101/generar")
    from tbg import workspace
    fs = workspace.HUSpace("HU-101").frames()
    assert fs.coverage.ac_percent == 100.0
    assert any(f.origin == "rule:token.expiration" for f in fs.frames)  # las reglas funcionan sin IA


def test_settings_store_key_outside_repo_and_never_render_it(fresh, tmp_path):
    _, c = fresh
    secret = "AIzaSy-super-secreta-123456"
    c.post("/config", data={"preset": "gemini", "model": "gemini-x", "api_key": secret})
    cfg = llm.config()
    assert cfg.provider == "openai" and cfg.base_url.startswith("https://generativelanguage.googleapis.com")
    assert cfg.api_key == secret and (tmp_path / "cfg" / "config.json").exists()
    page = c.get("/config").text
    assert secret not in page and "AIza…3456" in page
    c.post("/config", data={"preset": "gemini", "model": "gemini-y", "api_key": ""})  # vacío conserva la key
    assert llm.config().api_key == secret and llm.config().model == "gemini-y"


def test_password_protects_the_whole_app(fresh, monkeypatch):
    webapp, c = fresh
    monkeypatch.setattr(webapp, "PASSWORD", "clave-del-equipo")
    assert c.get("/").status_code == 401
    assert c.get("/", auth=("qa", "otra")).status_code == 401
    assert c.get("/", auth=("qa", "clave-del-equipo")).status_code == 200


def test_locked_settings_cannot_be_changed_from_the_ui(fresh, monkeypatch):
    webapp, c = fresh
    monkeypatch.setattr(webapp, "SETTINGS_LOCKED", True)
    r = c.post("/config", data={"preset": "anthropic", "api_key": "sk-robada"})
    assert "bloqueada" in r.text and llm.config().provider == "none"


def test_ai_usage_is_rate_limited_per_client(fresh, monkeypatch):
    webapp, c = fresh
    monkeypatch.setattr(webapp, "AI_LIMIT", 1)
    monkeypatch.setattr(webapp, "_usage", __import__("collections").defaultdict(__import__("collections").deque))
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(ai, "extract_bug", lambda rep, b: (_ for _ in ()).throw(llm.LLMError("sin red")))
    assert c.post("/bug/nuevo", data={"texto": "no anda"}).status_code == 200
    assert c.post("/bug/nuevo", data={"texto": "no anda"}).status_code == 429


def test_oversized_input_is_rejected(fresh):
    _, c = fresh
    r = c.post("/bug/nuevo", data={"texto": "x" * 30000})
    assert "supera el máximo" in r.text


# ---------------------------------------------------------------------------- regresiones reportadas por el usuario

FREE_FORM = (ROOT / "tests" / "hu_formato_libre.txt").read_text(encoding="utf-8")


def test_parser_understands_labeled_story_with_paragraph_criteria():
    from tbg.hu import parse_story
    s = parse_story(FREE_FORM)
    assert s.role.startswith("responsable de referencias") and s.want.startswith("que al crearse")
    assert s.so_that.startswith("no copiar el número")
    assert len(s.acceptance_criteria) == 5
    assert s.acceptance_criteria[2][1].startswith("Tras abrir el link")
    assert "Notas / contexto" in s.notes and "Fathom" in s.notes  # los metadatos no se cuelan como criterios


def test_free_form_story_flows_without_ai_one_happy_path_per_criterion(fresh):
    _, c = fresh
    r = c.post("/hu/nueva", data={"texto": FREE_FORM}, follow_redirects=False)
    sid = r.headers["location"].split("?")[0].split("/")[2]
    from tbg import workspace
    md = workspace.HUSpace(sid).hu_path.read_text(encoding="utf-8")
    assert md.count(f"## {sid} —") == 1  # un solo encabezado, con el ID asignado
    c.post(f"/hu/{sid}/basico")
    c.post(f"/hu/{sid}/generar")
    fs = workspace.HUSpace(sid).frames()
    happy = [f for f in fs.frames if f.origin == "ac-happy-path"]
    assert [f.ac_refs for f in happy] == [[f"CA-{i}"] for i in range(1, 6)]
    asked = {g.id for g in fs.gaps if g.asked}
    assert "phone.format" in asked and "token.expiration" not in asked and "dates.range" not in asked


def test_messages_survive_anchors_and_steps_out_of_order_do_not_crash(fresh):
    _, c = fresh
    c.post("/hu/nueva", data={"texto": FREE_FORM})
    r = c.post("/hu/HU-L001/generar", follow_redirects=False)
    loc = r.headers["location"]
    assert r.status_code == 303 and loc.index("?error=") < loc.index("#modelo")  # el mensaje va antes del #


def test_switching_provider_does_not_reuse_the_other_key_and_dropdown_lists_models(fresh, monkeypatch):
    _, c = fresh
    c.post("/config", data={"preset": "gemini", "model": "__otro__", "model_other": "", "api_key": "AIzaGeminiKey123456"})
    c.post("/config", data={"preset": "anthropic", "model": "claude-opus-5-5", "api_key": ""})
    assert llm.profile_config("anthropic").api_key is None  # no hereda la key de Gemini
    assert llm.profile_config("gemini").api_key == "AIzaGeminiKey123456"

    monkeypatch.setattr(llm, "list_models", lambda cfg: ["gemini-a", "gemini-b"])
    c.post("/config", data={"preset": "gemini", "model": "__otro__", "model_other": "", "action": "probar"})
    page = c.get("/config?preset=gemini").text
    assert '<select id="model"' in page and '<option value="gemini-b"' in page
    c.post("/config", data={"preset": "gemini", "model": "gemini-b"})
    assert llm.config().model == "gemini-b" and llm.config().preset == "gemini"
    c.post("/config", data={"preset": "gemini", "model": "gemini-a"})  # cambiar de modelo después
    assert llm.config().model == "gemini-a"


def test_web_export_package_and_import_answer_from_another_ai(fresh, model):
    _, c = fresh
    c.post("/hu/nueva", data={"texto": (ROOT / "ejemplos" / "hu-101.md").read_text(encoding="utf-8")})
    from tbg import workspace
    workspace.HUSpace("HU-101").save_model(model)
    c.post("/hu/HU-101/generar")
    page = c.get("/hu/HU-101").text
    assert "Descargar paquete para otra IA" in page and "Importar la respuesta" in page
    pkg = c.get("/hu/HU-101/descargar/paquete")
    assert pkg.status_code == 200 and "para_redactar.md" in pkg.headers["content-disposition"]
    answer = (ROOT / "ejemplos" / "hu-101.suite.json").read_text(encoding="utf-8")
    r = c.post("/hu/HU-101/importar", data={"respuesta": "Acá va:\n" + answer})
    assert "16 casos importados" in r.text and "Control de calidad OK" in r.text
    assert c.get("/hu/HU-101/descargar/disenados").text.startswith("# Casos diseñados")
