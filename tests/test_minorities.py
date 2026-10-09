"""Elementos que vio una sola lectura: descripción legible y alta manual al modelo."""

import pytest

from tbg import minorities
from tbg.schemas import AcceptanceCriterion, Choice, Parameter, TestModel

# Lo que mostraba la app en una HU real (consenso guardado por la versión anterior, sin payload)
LEGACY = [
    {"kind": "tag", "name": "ui", "votes": 1, "total": 3, "detail": ""},
    {"kind": "elección", "name": "telefono_del_referente.formato_invalido", "votes": 1, "total": 3,
     "detail": "El teléfono está mal ingresado o con formato inválido"},
    {"kind": "restricción", "votes": 1, "total": 3, "detail": "",
     "name": '{"if_choice":{"telefono_del_referente":"mal"},"forbids":{"confirmacion_envio":["lo_mande"]},"reason":"consenso"}'},
]


@pytest.fixture
def model():
    return TestModel(
        story_id="HU-L001", title="t", module="m", role="r", want="w",
        acceptance_criteria=[AcceptanceCriterion(id="CA-1", text="x")],
        parameters=[
            Parameter(name="telefono_del_referente", description="Teléfono del referente", kind="text", ac_refs=["CA-1"],
                      choices=[Choice(name="valido", description="teléfono válido", kind="valid", example="+5491122334455"),
                               Choice(name="mal", description="teléfono mal cargado", kind="invalid", example="123")]),
            Parameter(name="confirmacion_envio", description="Confirmación de la operadora", kind="enum", ac_refs=["CA-1"],
                      choices=[Choice(name="lo_mande", description="«lo mandé»", kind="valid", example="lo mandé"),
                               Choice(name="no_lo_mande", description="«no lo mandé»", kind="valid", example="no lo mandé")]),
        ])


def test_legacy_items_are_described_in_plain_language(model):
    texts = [minorities.describe(m, model) for m in LEGACY]
    assert texts[0].startswith("Tipo de funcionalidad «ui»: Interfaz de usuario")
    assert texts[1] == ("Variante «El teléfono está mal ingresado o con formato inválido» de «Teléfono del referente» — "
                        "inválida (el sistema debe rechazarla)")
    assert texts[2] == ("Combinación imposible: si «Teléfono del referente» es «teléfono mal cargado», "
                        "«Confirmación de la operadora» no puede ser ««lo mandé»»")
    assert "{" not in "".join(texts)  # nada de JSON a la vista


def test_adding_a_constraint_and_a_tag(model):
    m2 = minorities.apply(LEGACY[2], minorities.apply(LEGACY[0], model))
    assert "ui" in m2.feature_tags and len(m2.constraints) == 1
    assert minorities.present(LEGACY[2], m2) and minorities.present(LEGACY[0], m2)


def test_legacy_choice_asks_to_reanalyze_instead_of_guessing(model):
    with pytest.raises(ValueError, match="Volver a analizar"):
        minorities.apply(LEGACY[1], model)
