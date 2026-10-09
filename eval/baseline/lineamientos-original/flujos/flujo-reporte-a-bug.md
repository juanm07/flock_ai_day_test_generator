# Flujo: de reporte suelto a bug estructurado

> Workflow maestro del Flujo B. Un reporte "suelto" es cualquier texto informal: un mensaje de Slack/WhatsApp, un mail, un comentario, un voice note transcrito.

---

## F1 — Extracción de hechos

Leer el reporte completo y extraer **solo lo que el reportero dijo**, sin interpretar de más:

- **Síntoma**: qué falla, en palabras del reportero.
- **Pasos**: qué hizo, en el orden en que se puedan reconstruir (aunque vengan desordenados).
- **Ambiente**: todo dato de versión, navegador, dispositivo, entorno, usuario.
- **Evidencia**: capturas, logs, textos de error mencionados.
- **Frecuencia**: cuántas veces pasó / cuántas probó.
- **Contexto temporal**: "desde ayer", "desde el deploy".

Atención: distinguir lo **observado** ("vi un mensaje rojo") de lo **deducido por el reportero** ("seguro es la ñ"). La deducción del reportero es una hipótesis más, no un hecho.

## F2 — Clasificación de faltantes

Comparar lo extraído contra la `plantilla-bug.md`:

| Crítico (sin esto el bug casi no sirve) | Secundario (mejora el triage) |
|---|---|
| Pasos ordenados y reproducibles | Evidencia (captura, log) |
| Resultado esperado implícito o explícito | Frecuencia / reproducibilidad |
| Ambiente y versión | Impacto en otros usuarios |
| Texto del error | Workaround conocido |

- Si falta algo crítico → el bug se entrega igual, con `[PENDIENTE: ...]` y preguntas de seguimiento específicas. **No se rellena con ficción** (R6).
- Si el reporte contiene **dos defectos distintos** → dos bugs, con nota de relación.

## F3 — Redacción normalizada

- Título: `[Módulo] síntoma observable` (deducible del síntoma; si el módulo no es claro, `[Módulo a confirmar]`).
- Pasos: reconstruir el orden razonable, atómicos, incluyendo los pasos "obvios" que el reportero omitió **solo si son reconstruibles de lo dicho**. Si un paso es inventado, no va.
- Resultado actual: solo lo observado, con textos de error literales.
- Hipótesis (del reportero o del agente): sección separada, etiquetada como tal.
- Resultado esperado: si la HU/CA no lo define, `[SUPUESTO: ...]` + candidato a pregunta al PO.

## F4 — Clasificación

- **Severidad** con `taxonomia-severidad-prioridad.md`, con justificación de una línea.
- Si la severidad depende de información faltante: "S2 **preliminar**, condicionada a confirmar X".
- **Prioridad** según la matriz, incorporando contexto de negocio si el reporte lo da ("estamos a 3 días del release", "es el cliente más grande").

## F5 — Auto-revisión (gate)

Ejecutar `checklist-auto-revision.md` (sección bugs). Falla crítica → corregir antes de entregar.

## F6 — Entrega

Escribir `salidas/bug_normalizado_<NNN>_<YYYY-MM-DD>.md` con esta estructura:

```markdown
# BUG-NNN — [Módulo] Síntoma

Template completo de plantilla-bug.md, con:
- [PENDIENTE: ...] en cada campo sin dato + pregunta específica de seguimiento
- Hipótesis separadas de hechos
- Severidad/prioridad con justificación
- Sección final "Preguntas de seguimiento" consolidadas
- Sección final "Auto-revisión" con el checklist corrido
```

El texto original del reportero se cita al pie (bloque de cita), para que quien lo lea pueda verificar la normalización.
