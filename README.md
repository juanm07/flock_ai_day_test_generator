# Test & Bug Generator · Flock QA

Herramienta para equipos de QA que, a partir de una **historia de usuario** o un **reporte de bug informal**, genera:

- las **preguntas para el PO** sobre lo que la historia no define;
- una **suite de casos de prueba** con el formato del equipo: priorizada por riesgo, con cobertura medida y exportable a
  **Gherkin / Playwright**;
- un **bug normalizado** listo para el tracker: hechos con su cita, severidad y prioridad justificadas, y las preguntas
  para quien reportó.

Se usa desde una **app web**, un **asistente guiado en la terminal** o un **CLI**. Funciona con IA (Claude, Gemini, GLM,
OpenAI…), con otra IA vía copiar y pegar, o sin IA.

---

## El problema

Pedirle a un LLM "armame los casos de esta HU" da algo razonable, pero:

- **cada vez da algo distinto** (32 casos en una corrida, 39 en otra, otras prioridades);
- **inventa** comportamiento que la historia no define, sin avisar;
- **se equivoca en las cuentas** (conteos, cobertura) y no respeta del todo el formato del equipo;
- se **audita a sí mismo**, así que su "control de calidad" no controla nada.

## La idea: el LLM propone, el código dispone

Lo que requiere entender lenguaje lo hace la IA; **todo lo que tiene una respuesta correcta lo hace código
determinista y testeado** (`tbg`), y la salida de la IA solo se acepta si pasa sus controles.

| Lo hace la IA | Lo hace `tbg` (siempre igual, sin IA) |
|---|---|
| Leer la HU y anotar qué datos entran y sus variantes (3 lecturas independientes + consenso) | Verificar cada cita contra la HU y fusionar las lecturas por mayoría |
| Redactar los pasos de cada caso | Decidir **qué casos existen**, con qué datos y qué se espera; prioridad, cobertura, IDs |
| Extraer los hechos de un reporte de bug, con cita textual | Detectar lagunas y armar las preguntas al PO; rechazar hechos sin cita; clasificar S/P |
| — | Control de calidad (pasos atómicos, esperados observables, datos concretos, supuestos marcados) |

Cada pieza sigue un método publicado: Category-Partition (Ostrand & Balcer, 1988), pairwise (Kuhn et al., 2004; PICT),
valores límite (Myers), Requirements Smells (Femmer et al., 2017), Quality User Story (Lucassen et al., 2016), riesgo
(Amland, 2000), calidad de bug reports (Bettenburg et al., 2008; Chaparro et al., 2017), self-consistency (Wang et al.,
2023) y *Assured LLM-based SE* (Meta, 2024). Detalle en [Cómo funciona](#cómo-funciona).

---

## Empezar en 5 minutos

Requisitos: **Python 3.11+** y git.

```bash
git clone https://github.com/juanm07/flock_ai_day_test_generator.git
cd flock_ai_day_test_generator
python -m venv .venv
```

| | Windows (PowerShell o Git Bash) | macOS / Linux |
|---|---|---|
| Instalar | `.venv\Scripts\pip install -e ".[all,dev]"` | `.venv/bin/pip install -e ".[all,dev]"` |
| Correr los tests | `.venv\Scripts\python -m pytest` | `.venv/bin/python -m pytest` |
| Usar `tbg` | `.venv\Scripts\tbg …` (o activá el venv: `.venv\Scripts\activate`) | `.venv/bin/tbg …` (o `source .venv/bin/activate`) |

Los tests (~70) no usan IA ni red: corren en segundos. En los ejemplos de abajo `tbg` es el comando del venv.

---

## Probalo con tus casos

Guardá tus historias o reportes en `mis-casos/` (está en `.gitignore`, no se sube) o usá los de `ejemplos/`:

| Archivo | Qué es |
|---|---|
| `ejemplos/hu-101.md` | Recuperación de contraseña (formato prolijo) |
| `ejemplos/hu-202.md` | Exportación de movimientos (con palabras vagas a propósito) |
| `ejemplos/hu-formato-libre.txt` | HU real anonimizada, tal como la escribe un equipo (etiquetas, párrafos, notas) |
| `ejemplos/reporte-001.md` | Reporte de bug por chat ("che, no puedo entrar con mi contraseña con ñ…") |

### A. App web — para QA y PO, sin terminal

```bash
tbg ui            # abre http://127.0.0.1:8765
```

**Nueva HU**: pegala en cualquier formato y seguí los 5 pasos de la página:

1. **Cómo se interpretó**: rol, criterios, palabras vagas (se puede editar).
2. **Datos y variantes**: con IA (3 lecturas + consenso) o «Seguir sin IA».
3. **Preguntas al PO**: respuesta, «acepto el default» o límites numéricos.
4. **Casos**: tabla con filtros y cobertura. Se redactan con la IA configurada, con **otra IA** (paquete para copiar y
   pegar, más rápido) o a mano; todo pasa por el control de calidad.
5. **Exportar**: Markdown, `.feature` y steps de Playwright.

**Nuevo bug**: pegá el mensaje como llegó.

### B. Asistente guiado — la misma experiencia, en la terminal

```bash
tbg asistente mis-casos/mi-hu.md          # o sin archivo: lo pegás
tbg asistente ejemplos/reporte-001.md --bug
```

Te hace las mismas preguntas paso a paso (`s`/`n`, Enter para el default) y deja los resultados en `salidas/<ID>/`.
Lo que hagas queda en `work/<ID>/`, así podés continuarlo en `tbg ui`.

### C. CLI — paso a paso, para automatizar o integrar

```bash
tbg lint-hu ejemplos/hu-202.md                                  # palabras vagas + preguntas al PO
tbg generate ejemplos/hu-101.model.json --hu ejemplos/hu-101.md -o work/frames.json   # diseña 16 casos
tbg brief --frames work/frames.json --hu ejemplos/hu-101.md -o work/paquete.md        # paquete para otra IA
tbg import-suite ejemplos/hu-101.suite.json --frames work/frames.json --suite work/suite.json   # importa + valida
tbg export --frames work/frames.json --suite work/suite.json -o salidas/tests          # .feature + steps .ts
tbg bug-check ejemplos/reporte-001.facts.json --report ejemplos/reporte-001.md        # S2 preliminar, P2
tbg --help                                                      # todos los comandos
```

Los comandos que necesitan la "lectura" de la HU (`model.json`) la reciben de la app, del asistente, de un agente o de
`tbg consensus` (ver `AGENTS.md`). Para tests ejecutables: el `.feature` usa `# language: es` y los tags permiten
correr por partes (`npx playwright test --grep @humo` con [playwright-bdd](https://vitalets.github.io/playwright-bdd)).

### Con o sin IA

- **Sin IA**: «Seguir sin IA» (app) o lo mismo en el asistente. Preguntas al PO y casos de camino feliz, seguridad,
  estados y errores salen de los criterios y las reglas.
- **Con otra IA, copiando y pegando**: descargá el *paquete* (app, asistente o `tbg brief`), pegalo en ChatGPT, Gemini,
  Claude o la que uses, y traé la respuesta: se valida igual.
- **Con IA integrada**: en la app, **IA · configurar** (arriba a la derecha): elegí el proveedor, pegá la key, tocá
  «Guardar y probar conexión» y elegí el modelo de la lista. Gemini tiene key gratuita en
  [Google AI Studio](https://aistudio.google.com). La key queda en `~/.tbg/config.json`, fuera del repo.
- **Con un agente** (Claude Code / Pi): skills en `.claude/skills/` y protocolo en `AGENTS.md`.

---

## Cómo funciona

```
HU ──► lint (smells, QUS) ──► lectura con IA ×3 ──► consenso + citas verificadas ──► preguntas al PO (≤8, con default)
                                                                                         │ respuestas / límites
casos ◄── control de calidad ◄── redacción (IA, otra IA o persona) ◄── diseño: Category-Partition + pairwise + bordes + reglas
  └──► Markdown · Gherkin (.feature) · steps Playwright

Bug ──► hechos con cita textual (IA) ──► citas verificadas ──► faltantes OB/EB/S2R ──► severidad/prioridad por reglas
```

| Componente | Referencia | Cómo se usa |
|---|---|---|
| Principio rector | Alshahwan et al. 2024, *Assured LLM-Based Software Engineering* (ICSE-InteNSE); TestGen-LLM (FSE 2024) | La salida de la IA se acepta solo si pasa filtros deterministas |
| Estabilidad | Wang et al. 2023, *Self-Consistency…* (ICLR) | 3 lecturas independientes + voto mayoritario (`tbg consensus`) |
| Modelo de test | Ostrand & Balcer 1988, *The Category-Partition Method* (CACM 31(6)) | Datos × variantes + restricciones; cada variante inválida es un caso propio |
| Combinatoria | Kuhn, Wallace & Gallo 2004 (IEEE TSE 30(6)); Czerwonka 2006 (PICT) | Pares cubiertos al 100%, con verificador independiente |
| Valores límite | Myers, *The Art of Software Testing* | mín-1, mín, mín+1, máx-1, máx, máx+1 calculados |
| Lint de HU | Femmer et al. 2017, *Requirements Smells* (JSS 123) | Léxico de palabras vagas en español |
| Calidad de HU | Lucassen et al. 2016, *Quality User Story / AQUSA* (REJ 21) | Formato, objetivo, atomicidad, criterios observables |
| Riesgo | Amland 2000, *Risk-based testing* (JSS 53(3)) | Prioridad = probabilidad × impacto, justificada por caso |
| Bugs | Bettenburg et al. 2008 (FSE); Chaparro et al. 2017 (FSE) | Faltantes OB/EB/S2R/ambiente → `[PENDIENTE]` + pregunta |

**Garantías, cubiertas por tests**: mismo modelo ⇒ misma suite; ningún caso fuera del diseño; ningún comportamiento
inventado sin `[SUPUESTO]`; sin límites del PO no hay casos de borde; cobertura recalculada aparte del generador (ese
verificador encontró que `allpairspy` deja pares sin cubrir con restricciones); ningún hecho de un bug sin cita; si
la severidad depende de algo que el reporte no dice, sale "preliminar" con la condición exacta.

### Resultados (detalle y cómo reproducirlos en [`eval/README.md`](eval/README.md))

| | Solo prompt | `tbg` |
|---|---|---|
| Lagunas detectadas, HU fuera de muestra (3 corridas) | 71% / 86% / 71% | **86% / 86% / 86%** |
| Pasos que violan las reglas de redacción del equipo | 4 a 25 por corrida | **0** |
| Coincidencia de casos entre corridas (tipo × criterio) | 0.46 | **0.88**\* |
| Errores aritméticos en la suite | sí | imposible: lo calcula el código |

\* Con consenso de 3 lecturas, medido sobre el diseño de casos (antes de redactar); sin consenso daba 0.40. La
comparación de punta a punta con consenso está pendiente (ver `eval/README.md`).

---

## Deploy seguro (para que nadie use tu API key)

La key nunca llega al navegador; lo que hay que cuidar es **quién usa la app** y **cuánto puede gastar**:

1. **Tope de gasto en el proveedor** (presupuesto en Google Cloud, límite mensual en la consola de Anthropic) y una key
   exclusiva para esta app.
2. **Acceso restringido**: SSO de la empresa (Google IAP, Cloudflare Access) o VPN; como mínimo
   `TBG_UI_PASSWORD=<clave>`, siempre detrás de HTTPS.
3. **Key solo en el servidor**: `TBG_LLM`, `TBG_MODEL`, `TBG_API_KEY` (y `TBG_OPENAI_BASE_URL` para Gemini/GLM). Con
   contraseña o `TBG_LOCK_SETTINGS=1`, la configuración queda bloqueada en la UI.
4. **Límites**: `TBG_AI_LIMIT_PER_HOUR` (default 30 operaciones con IA por persona) y `TBG_MAX_INPUT` (20.000 caracteres).
5. **Datos**: lo que se pega viaja al proveedor de IA; revisá su política antes de usarlo con información real.

```bash
TBG_LLM=openai TBG_OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/ \
TBG_MODEL=<modelo> TBG_API_KEY=<key> TBG_UI_PASSWORD=<clave> \
uvicorn tbg.web.app:app --host 0.0.0.0 --port 8765      # detrás de un proxy con HTTPS
```

## Adaptar a tu equipo

Todo el criterio vive en archivos editables, sin tocar código:

- `rules/gaps.yaml`: qué preguntarle al PO según el tipo de funcionalidad (cada laguna que la herramienta no detecta
  se agrega acá; `python eval/gap_recall.py` mide el efecto).
- `rules/severity.yaml` · `rules/risk.yaml`: taxonomía de severidad/prioridad y matriz de riesgo.
- `rules/smells_es.yaml` · `rules/tags.yaml` · `rules/quality.yaml`: vocabulario y reglas de redacción.
- `src/tbg/templates/*.j2`: formato de la suite y del bug.

## Mapa del repo

```
├── src/tbg/            núcleo: hu, lint, gaps, consensus, generate/ (partition, pairwise, bva), risk, coverage,
│                       validate, bug, export, po, flows · cli.py · wizard.py (asistente) · web/ (app) · llm.py, ai.py
├── rules/              reglas del equipo (YAML)
├── prompts/            extracción para agentes · generador de datasets para otro modelo
├── ejemplos/           HUs y reporte de ejemplo + artefactos de referencia
├── eval/               evaluación reproducible (ver eval/README.md)
├── tests/              pytest (~70 tests, sin IA ni red)
├── docs/lineamientos/  el criterio en prosa (plantillas, heurísticas, taxonomía)
├── AGENTS.md           protocolo para Claude Code, Pi u otro agente
├── salidas/            ejemplos de entregables
└── challenge_inicial_simple.md · challenge-enriquecido.md   consigna y visión inicial
```
