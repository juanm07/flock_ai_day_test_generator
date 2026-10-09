# Resultados de la evaluación (baseline solo-prompt vs pipeline tbg)

Generado por `python eval/evaluate.py`. Mismo modelo LLM en ambos brazos; mismas métricas sobre el markdown final.

## HU-101

| Métrica | baseline | pipeline |
|---|---|---|
| Corridas | 1 | 1 |
| Recall de lagunas golden (por corrida) | 86% | 100% |
| Casos por corrida | 38 | 18 |
| CV de cantidad de casos | — | — |
| Jaccard firmas tipo×CA (prom. entre pares de corridas) | — | — |
| Jaccard firmas + prioridad | — | — |
| Jaccard de lagunas preguntadas | — | — |
| Jaccard frames de reglas (solo pipeline) | — | — |
| Jaccard frames del modelo extraído (solo pipeline) | — | — |
| Preguntas al PO por corrida | 8 | 8 |
| Pasos compuestos (viola regla 1) | 25 | 0 |
| Esperados no observables (regla 2) | 1 | 0 |
| Casos con datos abstractos (regla 3) | 6 | 0 |
| Reporta cobertura de pares | no | sí |

- `eval/runs/baseline/HU-101/run-1/suite.md` (baseline): tipos {'Funcional': 5, 'Negativo': 13, 'Borde': 11, 'No funcional': 5, 'Excepción': 3, 'Regresión': 1}, prioridades {'Media': 15, 'Alta': 16, 'Baja': 7}, lagunas NO detectadas: context
- `eval/runs/pipeline/HU-101/run-1/suite.md` (pipeline): tipos {'Funcional': 4, 'Negativo': 8, 'No funcional': 2, 'Excepción': 4}, prioridades {'Alta': 10, 'Media': 8}, gate APROBADO

## HU-202

| Métrica | baseline | pipeline |
|---|---|---|
| Corridas | 3 | 3 |
| Recall de lagunas golden (por corrida) | 71% / 86% / 71% | 86% / 86% / 86% |
| Casos por corrida | 39, 37, 32 | 19, 22, 16 |
| CV de cantidad de casos | 0.082 | 0.129 |
| Jaccard firmas tipo×CA (prom. entre pares de corridas) | 0.459 | 0.401 |
| Jaccard firmas + prioridad | 0.341 | 0.38 |
| Jaccard de lagunas preguntadas | 0.889 | 1.0 |
| Jaccard frames de reglas (solo pipeline) | — | 1.0 |
| Jaccard frames del modelo extraído (solo pipeline) | — | 0.107 |
| Preguntas al PO por corrida | 8, 8, 8 | 8, 8, 8 |
| Pasos compuestos (viola regla 1) | 4, 10, 23 | 0, 0, 0 |
| Esperados no observables (regla 2) | 1, 1, 0 | 0, 0, 0 |
| Casos con datos abstractos (regla 3) | 0, 0, 0 | 0, 0, 0 |
| Reporta cobertura de pares | no, no, no | sí, sí, sí |

- `eval/runs/baseline/HU-202/run-1/suite.md` (baseline): tipos {'Humo': 4, 'Funcional': 3, 'Borde': 9, 'Negativo': 7, 'No funcional': 10, 'Excepción': 6}, prioridades {'Alta': 11, 'Media': 21, 'Baja': 7}, lagunas NO detectadas: timezone, volume
- `eval/runs/baseline/HU-202/run-2/suite.md` (baseline): tipos {'Humo': 4, 'Funcional': 5, 'Borde': 9, 'No funcional': 8, 'Negativo': 7, 'Excepción': 4}, prioridades {'Alta': 12, 'Media': 17, 'Baja': 8}, lagunas NO detectadas: timezone
- `eval/runs/baseline/HU-202/run-3/suite.md` (baseline): tipos {'Humo': 4, 'Funcional': 5, 'Borde': 8, 'Negativo': 5, 'No funcional': 7, 'Excepción': 3}, prioridades {'Alta': 11, 'Media': 17, 'Baja': 4}, lagunas NO detectadas: timezone, volume
- `eval/runs/pipeline/HU-202/run-1/suite.md` (pipeline): tipos {'Funcional': 8, 'Negativo': 7, 'Borde': 1, 'Excepción': 2, 'No funcional': 1}, prioridades {'Alta': 5, 'Media': 14}, lagunas NO detectadas: number_format, gate APROBADO
- `eval/runs/pipeline/HU-202/run-2/suite.md` (pipeline): tipos {'Funcional': 12, 'Negativo': 6, 'Borde': 1, 'Excepción': 2, 'No funcional': 1}, prioridades {'Alta': 4, 'Media': 18}, lagunas NO detectadas: number_format, gate APROBADO
- `eval/runs/pipeline/HU-202/run-3/suite.md` (pipeline): tipos {'Funcional': 7, 'Negativo': 5, 'Borde': 1, 'Excepción': 2, 'No funcional': 1}, prioridades {'Alta': 3, 'Media': 13}, lagunas NO detectadas: number_format, gate APROBADO
