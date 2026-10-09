---
name: analizar-hu
description: Analiza una historia de usuario o requisito para testearlo: extrae criterios de aceptación, detecta ambigüedades y lagunas, y genera preguntas específicas para el PO/producto con defaults propuestos. Usar cuando el usuario quiera evaluar la testabilidad de una HU, saber qué le falta a una historia, o preparar preguntas antes de diseñar casos de prueba.
---

# Analizar una historia de usuario

El análisis de testabilidad lo hace `tbg` de forma determinista (Requirements Smells, Quality User Story y
reglas de lagunas por tipo de funcionalidad). Vos lo corrés, lo interpretás y lo comunicás.

## Pasos

1. Guardá la HU en `work/<ID>/hu.md` (encabezado `## <ID> — <Título>`, enunciado Como/quiero/para, CAs numerados).
2. Corré `tbg lint-hu work/<ID>/hu.md` (`.venv/Scripts/tbg` en Windows si no está en el PATH).
3. Opcional, para lagunas de datos (límites, errores sin definir): extraé el TestModel y corré `tbg check-model`
   (ver Flujo A, pasos 3–4, de `AGENTS.md`).
4. Escribí `salidas/analisis_<ID>_<YYYY-MM-DD>.md` con: resumen de la HU (rol, funcionalidad, objetivo, CAs),
   hallazgos del lint (citando la regla), preguntas al PO **tal como las emite `tbg`** (P-1…, con categoría,
   por qué importa y default; bloqueantes primero) y veredicto: "lista para diseñar casos" si no hay
   BLOQUEANTES abiertas, si no "necesita respuestas del PO primero".

## Reglas

- No inventes preguntas extra ni cambies la clasificación: si creés que falta una regla, proponela como
  mejora a `rules/gaps.yaml` en una sección aparte ("Sugerencias de reglas"), separada de la salida de `tbg`.
- No generes casos de prueba acá (eso es `generar-casos-prueba`).
