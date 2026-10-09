# Checklist de auto-revisión (gate de calidad)

> **Versión ejecutable:** casos → `tbg validate` (C1–C8 críticos, O1–O5 observaciones; léxico en `rules/quality.yaml`); bugs → `tbg bug-check` (B1–B7). El gate ya no es una autoevaluación del LLM: es código con exit code.

> El agente corre esto ANTES de entregar (R4). Un ítem **CRÍTICO** fallado bloquea la entrega: se corrige y se vuelve a correr. Los demás son observaciones que se corrigen si el costo es bajo.

---

## Casos de prueba (Flujo A)

### Críticos

- [ ] **Cada CA tiene ≥1 caso** que la cubra, o figura en "sin cobertura" con motivo explícito.
- [ ] **Cero comportamiento inventado**: todo resultado esperado no especificado por la HU tiene `[SUPUESTO: ...]` o el caso es exploratorio.
- [ ] **Pasos reproducibles por terceros**: atómicos, con datos concretos, sin depender de "cómo pensé yo".
- [ ] **Resultados esperados observables**: otra persona puede decir "pasó" o "falló" sin interpretar.
- [ ] **IDs únicos y secuenciales**, sin huecos.
- [ ] **Matriz de cobertura completa** con % calculado y verificado contra los casos listados.
- [ ] **Preguntas al PO ≤ 8**, todas con default propuesto, ninguna trivial.

### Observaciones

- [ ] Hay ≥1 negativo/borde por funcionalidad con riesgo (guía: 1 por cada 2 positivos).
- [ ] Prioridades justificadas por la matriz de riesgo, no por "me parece".
- [ ] Subset de humo marcado.
- [ ] Sin casos duplicados o casi-duplicados (misma acción, mismo dato, mismo assertion).
- [ ] Dependencias entre casos declaradas en Precondiciones.
- [ ] Supuestos consolidados en su sección (6 del entregable).

## Bugs (Flujo B)

### Críticos

- [ ] **Título autónomo**: `[Módulo] + síntoma`, entendible en una lista de 200 bugs.
- [ ] **Pasos reproducibles por alguien que no vio el bug original**; nada inventado "para completar".
- [ ] **Resultado actual = solo hechos observados**; hipótesis en su propia sección.
- [ ] **Texto de error literal** entre comillas (si el reporte lo dio); si no, `[PENDIENTE]`.
- [ ] **Severidad justificada** con la taxonomía; si es preliminar, dice qué la condiciona.
- [ ] **Cada dato faltante tiene `[PENDIENTE: ...]` + pregunta específica**, no silencio.
- [ ] **Cero datos de ambiente/versión inventados.**
- [ ] Si el reporte tenía 2 defectos, hay 2 bugs (o justificación de por qué no).

### Observaciones

- [ ] Preguntas de seguimiento consolidadas y específicas.
- [ ] Reporte original citado textualmente al pie.
- [ ] Impacto estimado con lo que se sabe (aunque sea "subconjunto desconocido").

---

## Protocolo ante fallas

1. Falla CRÍTICA → corregir el entregable → re-correr el checklist completo (puede haber cascado otra cosa).
2. Falla de observación → corregir si el costo es bajo; si no, listarla en "Auto-revisión" del entregable como conocida.
3. Nunca entregar con críticos fallados, aunque el usuario "tenga apuro": se entrega el gate fallido como diagnóstico + lo corregido.
