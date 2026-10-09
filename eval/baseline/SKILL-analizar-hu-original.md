---
name: analizar-hu
description: Analiza una historia de usuario o requisito para testearlo: extrae criterios de aceptación, detecta ambigüedades y lagunas, y genera preguntas específicas para el PO/producto con defaults propuestos. Usar cuando el usuario quiera evaluar la testabilidad de una HU, saber qué le falta a una historia, o preparar preguntas antes de diseñar casos de prueba.
---

# Analizar una historia de usuario

Actuá como un QA senior haciendo análisis de testabilidad. Este es el análisis previo al diseño de casos: no generes la suite acá (eso es la skill `generar-casos-prueba`).

## Pasos

1. Leé estos lineamientos antes de empezar:
   - `docs/lineamientos/flujos/preguntas-al-po.md` (checklist de ambigüedad: es tu guía principal)
   - `docs/lineamientos/estructuras/plantilla-caso-prueba.md` (para entender qué va a necesitar el diseño después)
2. Analizá la HU que te pase el usuario (texto pegado o archivo).
3. Extraé: rol, funcionalidad, objetivo de negocio, criterios de aceptación numerados (CA-1, CA-2, ...), entidades y datos.
4. Recorré las 10 categorías del checklist (A-J) y clasificá cada gap: BLOQUEANTE / IMPORTANTE / MENOR.
5. Generá las preguntas al PO en el formato del lineamiento (cada una con "por qué importa" y "default propuesto"), máximo 8, bloqueantes primero.
6. Cerrá con un veredicto: "lista para diseñar casos" o "necesita respuestas del PO primero" (y cuáles).

## Reglas duras

- No inventés criterios de aceptación que la HU no tiene: reportalos como gaps.
- No generés casos de prueba en este análisis.
- Si la entrada no es una HU, decílo y sugiere el flujo correcto.

## Salida

Escribí el resultado en `salidas/analisis_<ID-HU>_<YYYY-MM-DD>.md` con las secciones: Resumen del análisis · Gaps detectados (clasificados) · Preguntas para el PO · Veredicto.
