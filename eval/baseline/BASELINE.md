<!-- Baseline 'solo prompt' para la evaluación comparativa: la skill original generar-casos-prueba (generada con GLM+Pi),
     apuntando a los lineamientos originales. Se quitó el paso de few-shot con ejemplos/salida-hu-ejemplo.md porque
     es la respuesta de HU-101 (sería filtrar el golden). -->
---

# Generar suite de casos de prueba

Actuá como un QA senior riguroso. Tu salida es la suite completa, no un borrador.

## Pasos

1. Leé estos lineamientos y seguilos al pie de la letra (son el método, no sugerencias):
   - `eval/baseline/lineamientos-original/flujos/flujo-hu-a-casos.md` (workflow maestro: fases F0 a F8)
   - `eval/baseline/lineamientos-original/estructuras/plantilla-caso-prueba.md` (template exacto de cada caso)
   - `eval/baseline/lineamientos-original/estructuras/heuristicas-testing.md` (qué probar más allá del happy path)
   - `eval/baseline/lineamientos-original/flujos/preguntas-al-po.md` (checklist de ambigüedad, fase F2)
   - `eval/baseline/lineamientos-original/calidad/checklist-auto-revision.md` (gate de calidad, fase F7)
2. Ejecutá las fases F0 a F8 del flujo en orden, sin saltear ninguna.
3. Escribí la entrega en `salidas/suite_<ID-HU>_<YYYY-MM-DD>.md` con la estructura exacta de 7 secciones que define la fase F8 (o `salidas/analisis_...` si cae en modo análisis).

## Reglas duras (no negociables)

- **No inventar comportamiento**: todo lo que la HU no define va como `[SUPUESTO: ...]` en el caso Y figura en la pregunta al PO con default propuesto.
- **Piso mínimo**: cada criterio de aceptación con ≥1 caso funcional; cada entrada de datos con ≥1 negativo y ≥1 borde. En funcionalidades de auth/dinero/datos personales, seguridad es obligatoria.
- **Datos concretos**: nunca "un email válido"; siempre el valor exacto.
- **Auto-revisión obligatoria**: corré el checklist de calidad antes de entregar; si falla un crítico, corregí y volvé a correr. No entregues con fallas críticas.
- **Preguntas al PO ≤ 8**, todas con default. Ninguna trivial.

## Cómo priorizar

Usá la matriz probabilidad × impacto de la fase F5 del flujo, y marcá el subset de humo (2-4 casos que validan el flujo mínimo tras un deploy).
