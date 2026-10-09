---
name: normalizar-bug
description: Convierte un reporte de bug informal o suelto (mensaje de chat, mail, comentario, voz transcrita) en un reporte de bug estructurado y accionable según la plantilla del equipo, con severidad y prioridad clasificadas, marcando [PENDIENTE] la información faltante y generando preguntas de seguimiento. Usar cuando el usuario traiga un bug "suelto", pida armar/redactar/mejorar un reporte de bug, o quiera clasificar un defecto.
---

# Normalizar un reporte de bug

Vos extraés hechos **con cita textual**; `tbg bug-check` verifica cada cita contra el reporte, detecta los
faltantes (OB/EB/S2R/ambiente), clasifica severidad y prioridad por reglas y renderiza el bug. Seguí el
**Flujo B de `AGENTS.md`**.

## Resumen operativo

```bash
tbg schema bug-facts
tbg bug-check work/BUG-<NNN>/facts.json --report work/BUG-<NNN>/reporte.md -o salidas/bug_normalizado_<NNN>_<fecha>.md
```

(`tbg` = `.venv/Scripts/tbg` en Windows o `.venv/bin/tbg` si no está en el PATH.)

## Reglas duras

- Toda `quote` es texto literal del reporte. Si `bug-check` dice que una cita no está (B1), sacá o corregí el
  hecho: nunca "acomodes" una cita.
- `null` para lo que el reporte no dice (versión, texto del error, features de clasificación).
- Conjeturas → `hypotheses` (con `by: reporter` o `by: agent`), nunca `observed`.
- Si el reporte describe dos defectos distintos, generá dos `facts.json` y dos bugs, con nota de relación.
- No discutas ni ajustes la severidad/prioridad que calcula `tbg`: si el usuario aporta contexto nuevo (ej.
  "está en producción"), agregalo como hecho citado de su mensaje y volvé a correr.

Guía de estilo para los textos: `docs/lineamientos/estructuras/plantilla-bug.md`.
