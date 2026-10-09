# Flujo: de historia de usuario a suite de casos de prueba

> Workflow maestro del Flujo A. El agente lo ejecuta de principio a fin, sin saltearse el gate de calidad.

---

## F0 — Validación de entrada

- ¿Es una HU o requisito? Si es otra cosa (bug, idea suelta), reenviar al flujo correcto.
- ¿Tiene criterios de aceptación? Si no: **no inventarlos**. Pasar igual a F1/F2 y a preguntas al PO.
- Guardar el texto original: se referencia textualmente, no se "recuerda distinto".

## F1 — Análisis de la HU

Extraer en forma estructurada:

- **Rol**: quién es el actor.
- **Funcionalidad**: qué puede hacer.
- **Objetivo de negocio**: para qué (el "para poder..." de la HU).
- **Criterios de aceptación (CA)**: numerarlos `CA-1, CA-2, ...` tal como están escritos.
- **Entidades y datos**: usuarios, datos, estados, sistemas involucrados.

Salida: sección "Resumen del análisis" del entregable.

## F2 — Detección de ambigüedades

Aplicar el checklist completo de `preguntas-al-po.md`. Clasificar cada gap:

| Clase | Definición | Tratamiento |
|---|---|---|
| **BLOQUEANTE** | Sin esa respuesta no se puede diseñar ni el happy path (o hay contradicción entre CAs) | No se generan casos para esa parte; se explica en el análisis |
| **IMPORTANTE** | Cambia el diseño de casos (límites, permisos, manejo de errores) | Se generan casos con `[SUPUESTO: ...]` explícito + pregunta al PO |
| **MENOR** | Detalle que no cambia el diseño | Se anota como supuesto |

Cada gap genera una pregunta en el formato de `preguntas-al-po.md` (con default propuesto).

## F3 — Decisión de modo

- **Modo completo** (default): hay CAs suficientes → generar toda la suite, con supuestos marcados y preguntas.
- **Modo análisis**: todo es bloqueante → entregar solo análisis + preguntas + recomendación de volver cuando estén las respuestas.
- Nunca un intermedio a medias: o se entrega suite completa o se entrega análisis; no "algunos casos".

## F4 — Diseño de la suite

Reglas:

1. Por cada CA-1..N: ≥1 caso funcional que la cubra.
2. Aplicar `heuristicas-testing.md` (regla de riesgo primero) para negativos, bordes, excepciones y no funcionales.
3. Usar el template exacto de `plantilla-caso-prueba.md` para cada caso.
4. IDs secuenciales (`CP-001`, `CP-002`, ...), sin huecos.
5. Marcar el **subset de humo**: los 2-4 casos que validan el flujo mínimo tras un deploy.
6. Dependencias explícitas entre casos en Precondiciones ("CP-001 ejecutado con éxito").
7. Ningún caso cuyo resultado esperado sea inventado: `[SUPUESTO: ...]` o tipo exploratorio.

## F5 — Priorización por riesgo

Para cada caso estimar:

- **Probabilidad del defecto** (Alta/Media/Baja): qué tan probable es que ESTE escenario encuentre algo.
- **Impacto si falla** (Alto/Medio/Bajo): qué se rompe para el negocio/usuario.

| | Impacto Alto | Impacto Medio | Impacto Bajo |
|---|---|---|---|
| **Prob. Alta** | Alta | Alta | Media |
| **Prob. Media** | Alta | Media | Baja |
| **Prob. Baja** | Media | Media | Baja |

Sugerir **orden de ejecución**: humo → Alta → Media → Baja.

## F6 — Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | ... | CP-001, CP-004, CP-005 | ✓ Cubierta |
| CA-2 | ... | ... | ✓ / ✗ + motivo |

- Cerrar con el **% de cobertura** (`CAs cubiertas / CAs totales`).
- Un CA sin cobertura exige motivo explícito ("bloqueante: falta definición de X, ver pregunta P-3").

## F7 — Auto-revisión (gate)

Ejecutar `checklist-auto-revision.md` (sección casos). Si falla algo crítico: corregir y volver a correr. No se entrega con fallas críticas.

## F8 — Entrega

Escribir `salidas/suite_<ID-HU>_<YYYY-MM-DD>.md` (o `analisis_<ID-HU>_<YYYY-MM-DD>.md` en modo análisis) con esta estructura:

```markdown
# Suite de pruebas — <ID-HU>: <título de la HU>

## 1. Resumen del análisis
   Rol, funcionalidad, objetivo, CAs numerados, entidades/datos.

## 2. Preguntas para el PO
   P-1..P-N en formato de preguntas-al-po.md, ordenadas por prioridad.

## 3. Casos de prueba
   CP-001 ... CP-N con template completo.

## 4. Priorización por riesgo
   Tabla prob × impacto por caso + orden de ejecución sugerido + subset de humo.

## 5. Matriz de cobertura
   CA ↔ CP + % de cobertura + CAs sin cubrir con motivo.

## 6. Supuestos asumidos
   Lista consolidada de todos los [SUPUESTO: ...] usados.

## 7. Auto-revisión
   Checklist con el resultado de cada ítem.
```

Si la entrada vino de un archivo, no sobrescribir la entrada: la salida es siempre un archivo nuevo en `salidas/`.
