"""Parser, lint (smells + QUS), verificación de citas y lagunas."""

from tbg import gaps, lint, pipeline
from tbg.quotes import quote_in
from tbg.schemas import Answer

GOLDEN_HU101 = {"credential.policy", "token.expiration", "token.invalidation", "auth.rate_limit",
                "credential.sessions", "account.state", "context.platform_i18n"}


def test_parser_reads_only_the_story_block(story):
    assert story.id == "HU-101"
    assert [a for a, _ in story.acceptance_criteria] == ["CA-1", "CA-2", "CA-3", "CA-4"]
    assert story.role.startswith("usuario registrado")
    assert story.so_that.startswith("volver a acceder")
    # la sección de calibración "Lagunas deliberadas" NO debe filtrarse al texto analizado
    assert "expiración" not in story.text and "Lagunas deliberadas" not in story.text


def test_quotes_accept_formatting_noise_and_reject_paraphrase():
    src = 'El sistema muestra el mensaje "Si el email existe, recibirás un enlace".'
    assert quote_in("el sistema MUESTRA el mensaje “Si el email existe", src)
    assert not quote_in("el sistema informa que el email existe", src)
    assert not quote_in("", src)


def test_smells_detect_vague_language(make_story):
    s = make_story("""## HU-7 — Exportar
**Como** analista, **quiero** exportar movimientos, **para** conciliar.
**Criterios de aceptación:**
1. El sistema genera el archivo rápidamente en los formatos habituales (CSV, XLSX, etc.).
2. Si es posible, el sistema muestra un resumen adecuado.
""")
    rules_hit = {f.rule for f in lint.smells(s)}
    assert {"smell.ambiguous_adverbs_adjectives", "smell.open_ended", "smell.loopholes",
            "smell.subjective_language"} <= rules_hit


def test_qus_and_blocking_gap_without_acceptance_criteria(make_story):
    s = make_story("## HU-9 — Algo\n**Como** usuario **quiero** ver mi saldo.\n")
    findings = lint.qus(s)
    assert {"qus.has_benefit", "qus.has_acceptance_criteria"} <= {f.rule for f in findings}
    detected = gaps.detect(s, set(), findings)
    assert detected[0].id == "structure.no_ac" and detected[0].gap_class == "BLOQUEANTE"


def test_hu101_golden_gaps_are_all_asked(story):
    _, _, detected = pipeline.analyze(story)
    asked = {g.id for g in detected if g.asked}
    assert GOLDEN_HU101 <= asked
    assert len(asked) <= 8


def test_story_that_defines_a_topic_covers_its_gap(make_story):
    s = make_story("""## HU-5 — Reset
**Como** usuario, **quiero** recibir un enlace para cambiar mi contraseña, **para** entrar.
**Criterios de aceptación:**
1. El sistema envía un enlace que expira a las 24 horas.
""")
    _, _, detected = pipeline.analyze(s)
    by_id = {g.id: g for g in detected}
    assert by_id["token.expiration"].status == "covered"
    assert by_id["token.invalidation"].status == "open"


def test_answers_and_bounds_close_gaps(story, model):
    model.answers["token.expiration"] = Answer(value="1 hora", by="PO")
    _, _, detected = pipeline.analyze(story, model)
    by_id = {g.id: g for g in detected}
    assert by_id["token.expiration"].status == "answered"
    assert by_id["credential.policy"].status == "open"  # password_nueva sin límites todavía

    from tbg.schemas import Bounds
    next(p for p in model.parameters if p.name == "password_nueva").bounds = Bounds(min=8, max=64, origin="PO")
    _, _, detected = pipeline.analyze(story, model)
    assert {g.id: g for g in detected}["credential.policy"].status == "answered"
