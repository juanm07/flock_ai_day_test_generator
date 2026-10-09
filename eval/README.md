# Evaluación

Cómo se midió que el enfoque "el LLM propone, el código dispone" funciona mejor que pedirle todo a un LLM, y cómo
reproducirlo o ampliarlo con tus propios casos.

Todas las corridas usaron el mismo modelo (Claude Sonnet) en todos los brazos. **HU-101** es *en muestra* (las reglas
se diseñaron mirándola); **HU-202** es *fuera de muestra* (su golden se escribió antes de correr y no se ajustaron
reglas después). Las salidas crudas de cada corrida están en `eval/runs/`.

| Carpeta / archivo | Qué es |
|---|---|
| `baseline/` | La versión original "solo prompt" (skill + lineamientos), preservada para comparar |
| `golden/` | Lagunas que un QA senior debería detectar en cada HU (con términos para buscarlas en la salida) |
| `runs/` | Salidas de las corridas: baseline, pipeline v1 y extracciones para el consenso |
| `evaluate.py` → `results.md` | Baseline vs pipeline sobre el markdown final |
| `model_stability.py` → `stability_HU-202.md` | Estabilidad de la extracción: única vs convenciones vs consenso |
| `gap_recall.py` | Recall/precisión de lagunas **sin LLM** (segundos, sobre cualquier cantidad de HUs) |
| `import_dataset.py` · `evaluate_bugs.py` | Importar un dataset generado por otro modelo y medir el flujo de bugs |

## 1. Baseline solo-prompt vs pipeline v1 (extracción única) — `python eval/evaluate.py`

| Métrica | Baseline solo-prompt | Pipeline v1 |
|---|---|---|
| Recall de lagunas, HU-202 fuera de muestra (3 corridas) | 71% / 86% / 71% | **86% / 86% / 86%** |
| Recall de lagunas, HU-101 en muestra (1 corrida) | 86% | 100% |
| Estabilidad de las preguntas al PO entre corridas (Jaccard) | 0.89 | **1.00** |
| Pasos compuestos por corrida (viola la regla 1 de la plantilla) | 4 / 10 / 23 (HU-101: 25) | **0** |
| Esperados no observables · casos con datos abstractos (HU-101) | 1 · 6 | **0 · 0** |
| Cobertura de pares / bordes reportada y verificada | no | **sí** |
| Errores aritméticos en la propia suite | sí (HU-101: conteo de prioridades inconsistente) | imposible: lo calcula el código |
| Casos por corrida (HU-202) | 39 / 37 / 32 | 19 / 22 / 16 |
| Estabilidad de casos tipo×CA entre corridas (Jaccard) | **0.46** | 0.40 |

En v1 la varianza quedó **localizada** en la extracción del modelo de la HU: los casos que salen de reglas eran
idénticos entre corridas (1.00) y los del modelo extraído casi no coincidían (0.11). Eso motivó la v2.

## 2. v2: convenciones de extracción + self-consistency — `python eval/model_stability.py HU-202`

9 extracciones independientes nuevas de HU-202, fusionadas en 3 consensos disjuntos de a 3 (Wang et al., ICLR 2023).
Mide los casos que diseña `tbg` a partir de cada modelo (sin redacción: aísla la varianza de extracción).

| Condición | Casos por modelo | CV | Jaccard `frame_id` | Jaccard tipo×CA×técnica |
|---|---|---|---|---|
| Extracción única, prompt v1 | 19, 22, 16 | 0.13 | 0.22 | 0.40 |
| Extracción única, `prompts/extraer-modelo.md` (convenciones) | 17–24 (9 modelos) | 0.09 | 0.39 | 0.72 |
| **Consenso de 3** (`tbg consensus`) | 19, 21, 19 | **0.05** | **0.88** | **0.88** |

Las convenciones de nombres hacen que extracciones independientes vean los mismos datos; el voto elimina las
variantes idiosincráticas de cada corrida. Pendiente: repetir la evaluación 1 de punta a punta usando v2.

## 3. Recall/precisión de lagunas sin LLM — `python eval/gap_recall.py --detalle`

Las preguntas al PO salen solo del texto de la HU + reglas, así que se evalúan instantáneamente. Hoy: 13/14 lagunas
golden (93%). El miss es `number_format` en HU-202: no hay regla, y no se agregó a posteriori para no sobreajustar
(es el ejemplo del loop de mejora).

## 4. Probar con más casos (tuyos o generados)

No hay un dataset público en español de HUs con lagunas etiquetadas ni de reportes de bug con severidad esperada. Lo
más cercano está en inglés y sin ese golden: los 22 sets de user stories de Dalpiaz (Mendeley Data,
doi:10.17632/7zbk8zsd8y), PURE (79 documentos de requisitos, Ferrari et al., RE 2017) y la herramienta BEE de Chaparro
et al. (OB/EB/S2R en bug reports).

Dos caminos:

- **Tus casos**: escribí el golden de tu HU con el formato de `golden/hu-101.gaps.yaml` (campo `hu_file` con la ruta
  a la HU) y corré `python eval/gap_recall.py --detalle`.
- **Generados**: `prompts/generar-dataset.md` es un prompt para que **otro modelo** (que no conozca nuestras reglas)
  genere HUs con lagunas, temas `no_preguntar` (para medir falsos positivos) y reportes de bug con su golden.
  `python eval/import_dataset.py <respuesta.txt>` lo importa a `eval/dataset/`; `gap_recall.py` y `evaluate_bugs.py`
  lo miden.

## Próximos pasos

1. Generar 2–3 lotes con `prompts/generar-dataset.md`, medir recall/precisión y convertir cada miss recurrente en regla.
2. Repetir la evaluación 1 de punta a punta con la v2 (consenso) y con otros proveedores (Gemini, GLM).
3. Ejecutar los casos contra la app real (agente con navegador que corre el `.feature` y adjunta evidencia).
4. Export a Jira/Xray/TestRail.
