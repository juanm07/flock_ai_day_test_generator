# Protocolo para agentes (Claude Code, Pi, GLM, cualquier LLM)

Este repo separa responsabilidades: **vos (el LLM) extraés y redactás; `tbg` (código determinista) diseña,
clasifica, valida y mide.** No calcules a mano nada que `tbg` calcula: IDs, prioridades, cobertura,
severidad, preguntas al PO, valores límite, combinaciones. Si `tbg` rechaza tu salida, corregí tu salida;
nunca edites a mano los archivos que genera `tbg` (`frames.json`, `salidas/*.md`).

**Cómo correr `tbg`**: `tbg <comando>` si está en el PATH; si no, `.venv/Scripts/tbg` (Windows) o
`.venv/bin/tbg` (Linux/macOS). Setup: `python -m venv .venv` + `pip install -e .[dev]`.
Directorio de trabajo por HU/bug: `work/<ID>/` (no versionado). Entregables: `salidas/`.

---

## Flujo A — HU → suite de casos

1. **Guardar la HU** en `work/<ID>/hu.md` (texto tal cual, con el encabezado `## <ID> — <Título>`).
2. **Lint**: `tbg lint-hu work/<ID>/hu.md` → tags sugeridos, smells, lagunas.
3. **Extraer el TestModel con self-consistency** → `work/<ID>/model.json`:
   - Hacé **3 extracciones independientes** con `prompts/extraer-modelo.md` → `work/<ID>/model.1.json`, `.2`, `.3`.
     Independientes = cada una sin ver las otras: subagentes en paralelo (Claude Code) o 3 conversaciones/contextos
     nuevos. Si tu entorno no permite contextos independientes, hacé una sola (`model.json`) y avisá al usuario que
     la suite será menos estable.
   - Fusioná: `tbg consensus work/<ID>/model.*.json --hu work/<ID>/hu.md -o work/<ID>/model.json`. Mostrá al usuario
     los elementos **minoritarios** que reporta: si alguno debería estar, agregalo a `model.json` a mano.
   - Medido en HU-202: la coincidencia de frames entre corridas pasa de 0.39 (extracción única) a 0.88 (consenso).

   Reglas de cada extracción (el detalle y las convenciones de nombres están en `prompts/extraer-modelo.md`):
   - `acceptance_criteria[].text`: copiá cada CA **literal** de la HU (se verifica contra el texto).
   - `feature_tags`: solo del vocabulario de `rules/tags.yaml` (los sugeridos se suman solos).
   - `parameters` = categorías del Category-Partition: cada entrada o condición que varía entre casos y
     que influye en el resultado (un campo, un estado, un tipo de dato, un formato). `ac_refs` = CAs donde interviene.
   - `choices` = particiones de equivalencia. `kind`: `valid` (se combinan pairwise), `invalid` (error: un
     caso propio cada una), `exception` (condición adversa del entorno). La **primera** `valid` es la típica.
   - `example`: valor **concreto** (`qa.usuario01@empresa.com`, no "un email válido"). `""` = vacío.
     Entre paréntesis = referencia a otro dato: `(la misma definida en password_nueva)`.
   - `expected` + `quote`: SOLO si la HU lo dice; `quote` es la cita textual. Si la HU no lo dice: `expected: null`.
   - `assumed: true` si que la partición sea válida/inválida es un supuesto tuyo (ej. "acepta unicode").
   - `bounds`: solo si la HU (origin `HU`) o el PO (`PO`) los dan. Si deberían existir y no están:
     `bounds: null` + `bounds_relevant: true` → `tbg` genera la pregunta al PO.
   - `constraints`: combinaciones imposibles (`if_choice` → `forbids`).
   - No modeles vos seguridad, expiración, sesiones, rate limit, etc.: las reglas de `rules/gaps.yaml` ya
     agregan esas preguntas y casos según los tags.
4. **Validar el modelo**: `tbg check-model work/<ID>/model.json --hu work/<ID>/hu.md` hasta 0 errores.
5. **Preguntas al PO** — dos formas:
   - **Formulario (recomendado)**: `tbg po-form work/<ID>/model.json --hu work/<ID>/hu.md -o work/<ID>/po.yaml`.
     El PO completa `respuesta`, `acepto_default` y, en las preguntas de límites, `min`/`max` numéricos. Después:
     `tbg po-apply work/<ID>/po.yaml work/<ID>/model.json --hu work/<ID>/hu.md`. **Así es como el PO define los
     límites**: nunca los infieras vos de una respuesta en texto libre.
   - **Interactivo**: mostrá las preguntas marcadas `?` con su default; por cada respuesta,
     `tbg answer work/<ID>/model.json <gap_id> "<respuesta>"`, o para límites
     `tbg set-bounds work/<ID>/model.json <param> --min N --max M --origin PO` (solo si el usuario dio los números).
   Lo no respondido queda como `[SUPUESTO]` automáticamente. Regla del equipo: **sin límites del PO no hay casos de
   valores límite** (no se inventan rangos).
6. **Generar**: `tbg generate work/<ID>/model.json --hu work/<ID>/hu.md -o work/<ID>/frames.json`.
7. **Redactar** `work/<ID>/suite.json` (schema: `tbg schema suite`): **exactamente un caso por frame**, sin agregar ni
   quitar. Por cada frame leé `title_hint`, `bindings`, `data`, `expected_hints`, `supuestos`, `exploratory`:
   - Título "Verificar que …" (o "Explorar …" si `exploratory`).
   - Pasos atómicos: **una acción por paso**, nunca "ingresar X y confirmar".
   - Resultado esperado observable: qué se ve/qué mensaje/a dónde navega. Prohibido "correctamente", "se ve bien".
   - Usá los valores de `data` **literales** en los pasos o precondiciones.
   - Si el frame tiene `supuestos`, el resultado esperado afectado lleva `[SUPUESTO: …]`.
   - Para dependencias entre casos referenciá el `frame_id` (`F-xxxxxxxx`), no el `CP-NNN`: `tbg` lo traduce.
8. **Gate**: `tbg validate work/<ID>/suite.json --frames work/<ID>/frames.json`. Si falla (exit 1), corregí la
   redacción y repetí. Si regenerás frames (ej. tras una respuesta del PO), los `frame_id` previos se conservan:
   solo redactá los nuevos.
9. **Entregar**: `tbg render --model work/<ID>/model.json --frames work/<ID>/frames.json --suite work/<ID>/suite.json`
   → `salidas/suite_<ID>_<fecha>.md`.
10. **Tests concretos** (si el usuario los pide): `tbg export --frames work/<ID>/frames.json --suite work/<ID>/suite.json -o salidas/tests`
   → `.feature` en español + esqueleto de steps Playwright (`playwright-bdd`). No escribas el .feature a mano.

Solo análisis (sin suite): pasos 1–2 (y 3–4 si querés lagunas sobre el modelo). Resumí al usuario lo que dice `tbg`.

## Flujo B — Reporte suelto → bug

1. **Guardar el reporte** literal en `work/BUG-<NNN>/reporte.md`.
2. **Extraer hechos** → `work/BUG-<NNN>/facts.json` (schema: `tbg schema bug-facts`). Reglas:
   - Cada hecho lleva `quote`: **cita textual** del reporte (se verifica; una paráfrasis no pasa).
   - Lo que el reporte no dice va `null` (nunca inventes versión, ambiente, texto de error).
   - `error_text` solo si el reporte da el texto; si el reportero lo parafrasea, citá su frase igual: `tbg` la marca como paráfrasis.
   - `features` (data_loss, security, blocks_critical_flow, …): `true/false` **con cita**, o `null` si el reporte no lo dice.
     Nunca pongas `true` por intuición: la severidad la decide `tbg` y deja la duda explícita.
   - Conjeturas (del reportero o tuyas) van en `hypotheses`, nunca en `observed`.
   - Pasos sin respaldo textual (navegación obvia) van con `quote: null`: se marcan "reconstruido".
3. **Verificar y clasificar**: `tbg bug-check work/BUG-<NNN>/facts.json --report work/BUG-<NNN>/reporte.md -o salidas/bug_normalizado_<NNN>_<fecha>.md`.
   Si B1 falla (cita no encontrada), **eliminá o corregí el hecho**; nunca ajustes la cita para "que pase" sin que esté en el reporte.
4. Mostrá al usuario la severidad/prioridad con su condición y las preguntas de seguimiento.

## Qué NO hacer

- No calcular prioridades, severidad, cobertura, IDs ni % a mano.
- No agregar casos que no vienen de un frame (si falta algo, es un parámetro/elección faltante en el modelo).
- No completar con ficción lo que falta: va a `[PENDIENTE]`/`[SUPUESTO]` por diseño.
