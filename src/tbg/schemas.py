"""Contratos tipados entre el agente (LLM) y el núcleo determinista.

El LLM produce `TestModel` (flujo A, a partir de la HU), `SuiteDraft` (redacción de los frames) y `BugFacts`
(flujo B). Todo lo demás (`Frame`, `FrameSet`, IDs, prioridades, cobertura) lo calcula el código.

El modelo de test sigue el Category-Partition Method (Ostrand & Balcer, CACM 1988):
parámetros (categorías) con elecciones (choices) y restricciones entre elecciones.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Flujo A — entrada del LLM
# ---------------------------------------------------------------------------

ChoiceKind = Literal["valid", "invalid", "exception"]
ParamKind = Literal["text", "number", "date", "enum", "bool", "file", "list", "state"]
Origin = Literal["HU", "PO", "SUPUESTO"]


class Choice(_Strict):
    """Una elección de la categoría (partición de equivalencia)."""

    name: str = Field(description="Slug corto y estable, ej. 'registrado', 'formato_invalido'.")
    description: str = Field(description="Qué representa esta partición.")
    kind: ChoiceKind = Field(
        description="valid = partición válida (entra en pairwise); invalid = [error] de TSL (un caso propio); "
        "exception = condición adversa del entorno (un caso propio, tipo Excepción)."
    )
    example: str | None = Field(
        default=None,
        description="Valor concreto de prueba (ej. 'qa.usuario01@empresa.com'). '' es un valor válido (vacío). "
        "Entre paréntesis = referencia descriptiva a otro dato, ej. '(la misma definida en password_nueva)'.",
    )
    expected: str | None = Field(
        default=None,
        description="Comportamiento esperado SOLO si la HU (o el PO) lo define. null = no definido → el caso exige [SUPUESTO].",
    )
    quote: str | None = Field(
        default=None, description="Cita textual de la HU que justifica 'expected'. Se verifica contra el texto fuente."
    )
    assumed: bool = Field(
        default=False,
        description="True si que esta partición sea válida/inválida es un supuesto (la HU no lo dice). Exige [SUPUESTO].",
    )


class Bounds(_Strict):
    min: float | None = None
    max: float | None = None
    unit: Literal["chars", "value", "bytes", "items", "days"] = "chars"
    integer: bool = True
    origin: Origin = Field(description="De dónde sale el límite: HU, respuesta del PO o default asumido.")


class Parameter(_Strict):
    """Categoría del Category-Partition: una entrada o condición que varía entre casos."""

    name: str
    description: str
    kind: ParamKind
    ac_refs: list[str] = Field(description="IDs de CAs donde interviene, ej. ['CA-3'].")
    choices: list[Choice] = Field(min_length=1)
    bounds: Bounds | None = Field(
        default=None, description="Límites numéricos/longitud si existen. null + bounds_relevant → laguna detectada por código."
    )
    bounds_relevant: bool = Field(
        default=False, description="True si el parámetro DEBERÍA tener límites (longitud, rango, tamaño)."
    )


class Constraint(_Strict):
    """Restricción TSL simplificada: si se da `if_choice`, quedan prohibidas las `forbids`."""

    if_choice: dict[str, str] = Field(description="{parametro: choice}")
    forbids: dict[str, list[str]] = Field(description="{parametro: [choices incompatibles]}")
    reason: str


class AcceptanceCriterion(_Strict):
    id: str = Field(pattern=r"^CA-\d+$")
    text: str = Field(description="Texto del CA tal como aparece en la HU (se verifica).")


class Answer(_Strict):
    value: str
    by: Literal["PO", "default"] = "PO"


class TestModel(_Strict):
    __test__ = False  # evita que pytest intente recolectarlo

    story_id: str
    title: str
    module: str
    role: str
    want: str
    so_that: str | None = None
    feature_tags: list[str] = Field(
        default_factory=list, description="Tags del vocabulario de rules/tags.yaml. El código sugiere tags; el agente puede agregar."
    )
    acceptance_criteria: list[AcceptanceCriterion]
    parameters: list[Parameter] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    answers: dict[str, Answer] = Field(
        default_factory=dict, description="Respuestas a lagunas, por id de gap (ej. 'token.expiration')."
    )


# ---------------------------------------------------------------------------
# Flujo A — salida determinista
# ---------------------------------------------------------------------------

CaseType = Literal["Funcional", "Negativo", "Borde", "Excepción", "No funcional"]
Level = Literal["Alta", "Media", "Baja"]
GapClass = Literal["BLOQUEANTE", "IMPORTANTE", "MENOR"]


class Gap(_Strict):
    id: str
    category: str
    gap_class: GapClass
    question: str
    why: str
    default: str
    source: str = Field(description="Regla que lo disparó: 'tag:auth', 'schema:bounds', 'structure'…")
    status: Literal["open", "answered", "covered"] = "open"
    answer: str | None = None
    asked: bool = Field(default=False, description="True si entra en el tope de preguntas al PO.")


class Finding(_Strict):
    rule: str
    category: str
    message: str
    text: str = Field(description="Fragmento que dispara el hallazgo.")
    location: str


class Frame(_Strict):
    """Esqueleto de caso (test frame en TSL): qué probar, con qué datos y qué se espera; sin prosa."""

    frame_id: str
    case_id: str = ""
    type: CaseType
    title_hint: str
    ac_refs: list[str]
    bindings: dict[str, str] = Field(description="{parametro: choice o valor límite}")
    data: dict[str, str] = Field(default_factory=dict, description="{parametro: valor concreto}")
    expected_hints: list[str] = Field(default_factory=list)
    supuestos: list[str] = Field(default_factory=list, description="Si no está vacío, el caso DEBE llevar [SUPUESTO].")
    exploratory: bool = False
    examples: list[dict[str, str]] = Field(
        default_factory=list, description="Solo frames de valores límite: [{etiqueta, valor (literal completo), resultado}]."
    )
    origin: str = Field(description="Técnica que generó el frame: ac-happy-path, pairwise, error-choice, bva, rule:<id>.")
    probability: Level = "Media"
    impact: Literal["Alto", "Medio", "Bajo"] = "Medio"
    priority: Level = "Media"
    risk_reason: str = ""
    smoke: bool = False


class CoverageRow(_Strict):
    ac_id: str
    text: str
    case_ids: list[str]
    covered: bool
    reason: str = ""


class Coverage(_Strict):
    acceptance: list[CoverageRow]
    ac_percent: float
    pairs_total: int
    pairs_covered: int
    pairs_percent: float
    boundaries_total: int
    boundaries_covered: int
    boundaries_percent: float


class FrameSet(_Strict):
    story_id: str
    title: str
    module: str
    model_hash: str
    feature_tags: list[str]
    findings: list[Finding]
    gaps: list[Gap]
    frames: list[Frame]
    coverage: Coverage
    mode: Literal["completo", "analisis"]


# ---------------------------------------------------------------------------
# Flujo A — redacción del LLM sobre los frames
# ---------------------------------------------------------------------------


class Step(_Strict):
    action: str
    expected: str


class CaseDraft(_Strict):
    frame_id: str
    title: str = Field(description="'Verificar que …'. Debe entenderse solo.")
    preconditions: str
    steps: list[Step] = Field(min_length=1)
    evidence: str
    notes: str = ""


class SuiteDraft(_Strict):
    story_id: str
    cases: list[CaseDraft]


# ---------------------------------------------------------------------------
# Flujo B — entrada del LLM
# ---------------------------------------------------------------------------


class Fact(_Strict):
    text: str = Field(description="El hecho normalizado (puede reformular).")
    quote: str = Field(description="Cita TEXTUAL del reporte que lo respalda. Se verifica.")


class BugStep(_Strict):
    text: str
    quote: str | None = Field(default=None, description="Cita que respalda el paso; null solo si es un paso de navegación obvio.")


class Hypothesis(_Strict):
    text: str
    by: Literal["reporter", "agent"]
    quote: str | None = None


class Feature(_Strict):
    value: bool | None = Field(default=None, description="null = el reporte no lo dice.")
    quote: str | None = Field(default=None, description="Obligatoria si value != null.")


class BugFeatures(_Strict):
    data_loss: Feature = Feature()
    security: Feature = Feature()
    blocks_critical_flow: Feature = Feature()
    workaround_exists: Feature = Feature()
    affects_subset_only: Feature = Feature()
    cosmetic_only: Feature = Feature()
    regression: Feature = Feature()
    in_production: Feature = Feature()
    before_release: Feature = Feature()


class BugEnvironment(_Strict):
    app_version: Fact | None = None
    environment: Fact | None = None
    platform: Fact | None = None


class BugFacts(_Strict):
    bug_id: str = "BUG-001"
    module: str | None = None
    symptom: Fact
    observed: list[Fact] = Field(default_factory=list)
    expected: Fact | None = None
    steps: list[BugStep] = Field(default_factory=list)
    environment: BugEnvironment = BugEnvironment()
    error_text: Fact | None = Field(default=None, description="Texto LITERAL del error, solo si el reporte lo da.")
    evidence: list[Fact] = Field(default_factory=list)
    frequency: Fact | None = None
    since: Fact | None = None
    reporter: str | None = None
    affected_user: Fact | None = None
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    features: BugFeatures = BugFeatures()


SCHEMAS: dict[str, type[BaseModel]] = {
    "test-model": TestModel,
    "suite": SuiteDraft,
    "bug-facts": BugFacts,
}
