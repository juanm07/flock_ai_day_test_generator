# Challenge enriquecido: Generador de casos de prueba y bugs asistido por IA

> **Nota (v2):** este documento es la visión inicial (esqueleto generado con GLM + Pi, 100% prompt). La
> implementación evolucionó a "el LLM propone, el código dispone": las reglas, matrices y el gate de calidad
> ahora son código determinista (`src/tbg/`, `rules/`). Ver `README.md` y `AGENTS.md`.

> **Consigna original** (`challenge_inicial_simple.md`):
> "Generador de casos de prueba y bugs. Un agente configurado con la estructura de casos de prueba y bugs del equipo, que genere ambos a partir de una historia de usuario o un reporte suelto."

---

## Qué es

Un agente de QA configurable que opera como **un analista de pruebas riguroso que nunca se saltea el método**. Tiene dos flujos:

### Flujo A — Historia de usuario → suite de casos de prueba

1. **Analiza** la HU: rol, funcionalidad, objetivo y criterios de aceptación.
2. **Detecta ambigüedades y lagunas antes de diseñar**, y genera preguntas concretas al PO (cada una con un default propuesto).
3. **Genera la suite** siguiendo la plantilla del equipo y heurísticas de testing: happy path, negativos, bordes, excepciones y no funcionales — no solo el camino feliz.
4. **Prioriza por riesgo** (probabilidad × impacto) y sugiere orden de ejecución, incluyendo un subset de humo.
5. **Demuestra cobertura**: matriz criterio de aceptación ↔ casos de prueba, con % de cobertura.

### Flujo B — Reporte suelto → bug estructurado

1. **Extrae hechos** del reporte informal: síntoma, pasos, ambiente, evidencia.
2. **Clasifica qué falta sin inventar**: marca `[PENDIENTE]` y genera preguntas de seguimiento.
3. **Normaliza** al formato del equipo: título accionable, pasos reproducibles, hechos separados de hipótesis.
4. **Clasifica** severidad y prioridad con la taxonomía del equipo, con justificación explícita.

---

## Reglas duras del agente (no negociables)

| # | Regla | Por qué existe |
|---|-------|----------------|
| R1 | **No inventar comportamiento.** Lo que la HU no especifica va como `[SUPUESTO: ...]` o se pregunta | La ficción en QA genera falsa confianza |
| R2 | **Hechos ≠ hipótesis.** En bugs, el "resultado actual" es solo lo observado; las conjeturas van aparte | Evita que la especulación se disfrazce de evidencia |
| R3 | **Todo caso es reproducible por terceros** | Un caso que solo entiende su autor no sirve |
| R4 | **Auto-revisión obligatoria antes de entregar** (checklist de calidad); si falla algo crítico, se corrige, no se entrega igual | El gate de calidad no es opcional |
| R5 | **Severidad no se negocia por deadlines; prioridad sí** | Anti-mala-práctica clásica de QA |
| R6 | **Si falta información crítica, se pregunta; no se rellena** | Un `[PENDIENTE]` honesto vale más que un invento |

---

## Objetivos de éxito

| # | Objetivo | Cómo se verifica |
|---|----------|------------------|
| 1 | De una HU, generar una suite que cubra todos sus criterios de aceptación | Matriz de cobertura con 100% de los CAs (o CAs no cubiertos con motivo explícito) |
| 2 | La suite no es solo happy path | Proporción guía: ≥1 caso negativo/borde por cada 2 positivos en funcionalidades con riesgo |
| 3 | Detectar las ambigüedades que detectaría un QA senior | Preguntas al PO pertinentes, específicas y con default propuesto |
| 4 | De un reporte suelto, producir un bug estructurado listo para el tracker | Checklist de auto-revisión aprobado, sin campos rellenados con ficción |
| 5 | La salida respeta la estructura del equipo | Conformidad con las plantillas de `docs/lineamientos/estructuras/` |

---

## Alcance

### Dentro de v1

- Entrada: texto pegado o archivo Markdown (HU o reporte suelto).
- Salida: archivos Markdown versionables en `salidas/`.
- Análisis de ambigüedad + preguntas al PO + generación + priorización por riesgo + matriz de cobertura.
- Funciona con cualquier agente (pi, Claude Code, etc.) vía lineamientos, y nativamente en Claude Code vía skills.

### Fuera de v1 (roadmap "fase potente" con Claude Code)

- Integración con APIs (Jira, Azure DevOps, TestRail, Xray): leer HUs y crear bugs directamente.
- Export CSV/XLSX para importación masiva a herramientas de gestión.
- Gherkin ejecutable / automation.
- Memoria de convenciones del equipo entre sesiones.
- Generación de datos de prueba realistas y anonimizados.

---

## Arquitectura de la solución

```
├── docs/lineamientos/
│   ├── estructuras/          ← EL QUÉ: plantilla de caso, plantilla de bug,
│   │                            taxonomía severidad/prioridad, heurísticas
│   ├── flujos/               ← EL CÓMO: workflow HU→casos, workflow reporte→bug,
│   │                            checklist de ambigüedad (preguntas al PO)
│   └── calidad/              ← EL GATE: checklist de auto-revisión antes de entregar
├── ejemplos/                 ← LA CALIBRACIÓN: golden examples (entrada → salida esperada)
├── .claude/skills/           ← LA INTERFAZ: skills nativas de Claude Code
└── salidas/                  ← LOS RESULTADOS (se genera al usar el agente)
```

**Cómo se conectan las piezas:** las skills (o los prompts a cualquier agente) invocan los **flujos**; los flujos ordenan leer las **estructuras** (plantillas + heurísticas + taxonomía) y aplicarlas; antes de entregar, el flujo exige pasar el **gate de calidad**; los **ejemplos** calibran el nivel de detalle esperado y sirven de few-shot.

---

## Cómo se usa

### Con Claude Code

Las skills de `.claude/skills/` se activan automáticamente cuando el pedido encaja, o se pueden pedir explícitamente:

- "Usá la skill **generar-casos-prueba** con esta HU: ..."
- "Usá **analizar-hu** y decime qué le falta a esta historia"
- "Usá **normalizar-bug** con este reporte: ..."

### Con pi u otro agente

Pedile que lea el flujo y lo aplique:

- "Leé `docs/lineamientos/flujos/flujo-hu-a-casos.md` y procesá esta HU: ..."
- "Leé `docs/lineamientos/flujos/flujo-reporte-a-bug.md` y normalizá este reporte: ..."
- "Leé `docs/lineamientos/flujos/preguntas-al-po.md` y analizá esta HU"

### Convención de salidas

Todo output va a `salidas/` con naming estándar:

- Análisis: `salidas/analisis_<ID-HU>_<YYYY-MM-DD>.md`
- Suite: `salidas/suite_<ID-HU>_<YYYY-MM-DD>.md`
- Bug normalizado: `salidas/bug_normalizado_<NNN>_<YYYY-MM-DD>.md`

---

## Cómo adaptar esto a un equipo real

1. **Reemplazar plantillas**: swap de `docs/lineamientos/estructuras/plantilla-caso-prueba.md` y `plantilla-bug.md` por los templates reales del equipo. Los flujos y skills no cambian: referencian las plantillas, no las duplican.
2. **Ajustar taxonomía**: si el equipo usa otra escala de severidad (Blocker/Critical/Major/Minor, o 1-5), se cambia `taxonomia-severidad-prioridad.md`.
3. **Recalibrar ejemplos**: reemplazar los ejemplos sintéticos de `ejemplos/` por casos reales anonimizados. Es el upgrade de mayor impacto: los golden examples definen el estándar de calidad del agente.
