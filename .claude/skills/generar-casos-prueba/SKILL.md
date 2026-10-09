---
name: generar-casos-prueba
description: Genera una suite completa de casos de prueba a partir de una historia de usuario o requisito, incluyendo análisis de la HU, preguntas al PO, casos positivos/negativos/bordes/excepciones según heurísticas de testing, priorización por riesgo y matriz de cobertura. Usar cuando el usuario pida casos de prueba, diseñar o armar una suite de pruebas, o dar cobertura a una HU/requisito.
---

# Generar suite de casos de prueba

Vos extraés y redactás; el diseño de la suite (qué casos, con qué datos, IDs, prioridad, cobertura, preguntas
al PO, auto-revisión) lo calcula `tbg`, de forma determinista. Seguí el **Flujo A de `AGENTS.md`** paso a paso.

## Resumen operativo

**Extracción con self-consistency**: lanzá **3 subagentes en paralelo** (Agent tool, en un mismo mensaje), cada uno con
el prompt de `prompts/extraer-modelo.md` y salida `work/<ID>/model.1.json`, `.2`, `.3`. Después:

```bash
tbg lint-hu work/<ID>/hu.md                                   # smells, tags, lagunas
tbg consensus work/<ID>/model.1.json work/<ID>/model.2.json work/<ID>/model.3.json --hu work/<ID>/hu.md -o work/<ID>/model.json
tbg check-model work/<ID>/model.json --hu work/<ID>/hu.md     # hasta 0 errores
tbg answer work/<ID>/model.json <gap_id> "<respuesta>"        # loop con el PO (o set-bounds)
tbg generate work/<ID>/model.json --hu work/<ID>/hu.md -o work/<ID>/frames.json
tbg validate work/<ID>/suite.json --frames work/<ID>/frames.json   # hasta "Gate APROBADO"
tbg render --model work/<ID>/model.json --frames work/<ID>/frames.json --suite work/<ID>/suite.json
```

(`tbg` = `.venv/Scripts/tbg` en Windows o `.venv/bin/tbg` si no está en el PATH.)

## Interacción con el usuario

- Después de `check-model`, mostrá las preguntas al PO (las marcadas `?`) con su default y preguntá si las
  responde o seguimos con los defaults. Registrá cada respuesta con `tbg answer` / `tbg set-bounds` y regenerá.
- Al terminar, contá: cantidad de casos por tipo, cobertura (CAs, pares, bordes), subset de humo, supuestos
  pendientes y la ruta en `salidas/`.

## Para redactar `suite.json`

Guía de estilo: `docs/lineamientos/estructuras/plantilla-caso-prueba.md` (reglas de redacción) y
`docs/lineamientos/estructuras/heuristicas-testing.md` (para entender el porqué de cada frame).
Un caso por frame, pasos atómicos, datos literales del frame, `[SUPUESTO: …]` donde el frame lo pide,
dependencias por `frame_id`.
