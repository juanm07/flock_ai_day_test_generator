"""Self-consistency: voto mayoritario determinista sobre extracciones independientes del TestModel."""

import itertools

from tbg.consensus import merge
from tbg.schemas import Choice, Parameter


def _variant(model, rename: dict[str, str] | None = None, drop_choice: tuple[str, str] | None = None,
             extra_param: Parameter | None = None):
    m = model.model_copy(deep=True)
    for p in m.parameters:
        if drop_choice and p.name == drop_choice[0]:
            p.choices = [c for c in p.choices if c.name != drop_choice[1]]
        if rename and p.name in rename:
            p.name = rename[p.name]
    if extra_param:
        m.parameters.append(extra_param)
    return m


def test_identical_models_are_a_fixed_point(model):
    r = merge([model, model.model_copy(deep=True), model.model_copy(deep=True)])
    expected = model.model_copy(update={"feature_tags": sorted(model.feature_tags)})  # el consenso ordena los tags
    assert r.model == expected and r.agreement == 1.0 and not r.minorities


def test_majority_keeps_and_minority_is_reported(model):
    extra = Parameter(name="idioma_email", description="Idioma del email de recuperación", kind="enum",
                      ac_refs=["CA-2"], choices=[Choice(name="es", description="español", kind="valid", example="es")])
    a = model
    b = _variant(model, drop_choice=("password_nueva", "con_espacios"))   # 2/3 la tienen → se queda
    c = _variant(model, extra_param=extra)                                 # 1/3 → minoritario
    r = merge([a, b, c])
    names = {p.name: [ch.name for ch in p.choices] for p in r.model.parameters}
    assert "con_espacios" in names["password_nueva"]
    assert "idioma_email" not in names
    assert any(x.kind == "parámetro" and x.name == "idioma_email" and x.votes == 1 for x in r.minorities)


def test_renamed_parameter_is_aligned_and_majority_name_wins(model):
    b = _variant(model, rename={"email_solicitud": "email_ingresado"})
    r = merge([model, model.model_copy(deep=True), b])
    assert [p.name for p in r.model.parameters] == [p.name for p in model.parameters]


def test_result_does_not_depend_on_input_order(model):
    b = _variant(model, rename={"email_solicitud": "email_ingresado"}, drop_choice=("password_nueva", "unicode"))
    c = _variant(model, drop_choice=("email_solicitud", "vacio"))
    results = {merge(list(p)).model.model_dump_json() for p in itertools.permutations([model, b, c])}
    assert len(results) == 1
