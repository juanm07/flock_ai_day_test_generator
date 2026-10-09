---
name: normalizar-bug
description: Convierte un reporte de bug informal o suelto (mensaje de chat, mail, comentario, voz transcrita) en un reporte de bug estructurado y accionable según la plantilla del equipo, con severidad y prioridad clasificadas, marcando [PENDIENTE] la información faltante y generando preguntas de seguimiento. Usar cuando el usuario traiga un bug "suelto", pida armar/redactar/mejorar un reporte de bug, o quiera clasificar un defecto.
---

# Normalizar un reporte de bug

Actuá como un QA senior haciendo triage y redacción técnica. Entrada informal → salida lista para el tracker.

## Pasos

1. Leé estos lineamientos y seguilos al pie de la letra:
   - `docs/lineamientos/flujos/flujo-reporte-a-bug.md` (workflow maestro: fases F1 a F6)
   - `docs/lineamientos/estructuras/plantilla-bug.md` (template exacto del bug)
   - `docs/lineamientos/estructuras/taxonomia-severidad-prioridad.md` (clasificación)
   - `docs/lineamientos/calidad/checklist-auto-revision.md` (gate de calidad, sección bugs)
2. Si existe `ejemplos/salida-bug-ejemplo.md`, usalo como referencia del nivel de detalle esperado.
3. Ejecutá las fases F1 a F6 del flujo en orden.
4. Escribí la entrega en `salidas/bug_normalizado_<NNN>_<YYYY-MM-DD>.md` con el template completo + preguntas de seguimiento + auto-revisión + el reporte original citado al pie.

## Reglas duras (no negociables)

- **Extraer, no inventar**: solo va lo que el reportero dijo o lo que es directamente reconstruible de lo que dijo. Cero pasos, versiones o datos de ambiente inventados.
- **Hechos ≠ hipótesis**: el "resultado actual" lleva solo lo observado; toda conjetura (del reportero o tuya) va en la sección de hipótesis, etiquetada.
- **`[PENDIENTE: ...]` + pregunta específica** para cada dato faltante crítico (pasos, resultado esperado, ambiente, texto del error).
- **Texto de error literal** cuando exista; si solo hay paráfrasis, marcala como paráfrasis.
- **Un reporte con dos defectos = dos bugs**, con nota de relación.
- **Severidad con justificación** según taxonomía; si depende de información faltante, marcala "preliminar, condicionada a X".
- **Auto-revisión obligatoria** antes de entregar.
