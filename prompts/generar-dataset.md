# Prompt para generar un dataset de evaluación con OTRO modelo

> Copiá todo lo que está debajo de la línea en otro modelo (GPT, Gemini, GLM, otro Claude…) y guardá la respuesta
> completa en un archivo, por ejemplo `eval/dataset/raw/lote-01.txt`. Después:
>
> ```bash
> python eval/import_dataset.py eval/dataset/raw/lote-01.txt     # separa los archivos en eval/dataset/
> python eval/gap_recall.py                                      # recall/precisión de lagunas (sin LLM)
> ```
>
> **No le muestres a ese modelo nada de `rules/` ni de este repo**: el valor del dataset es que fue escrito por alguien
> que no conoce nuestras reglas (evaluación fuera de muestra). Pedí varios lotes cambiando `{SEMILLA}` y `{CANTIDAD}`.

---

Sos un QA senior y analista funcional con 15 años de experiencia en Latinoamérica. Necesito un dataset sintético
en **español** para evaluar una herramienta que (a) detecta lagunas en historias de usuario y (b) normaliza
reportes de bugs informales. Generá **{CANTIDAD} historias de usuario** y **{CANTIDAD} reportes de bug**. Semilla de
variedad: {SEMILLA} (usala para no repetir dominios ni funcionalidades entre lotes).

## Parte A — Historias de usuario con lagunas

Cada HU debe ser realista, como las que escribe un PO apurado: formato "Como… quiero… para…", 2 a 6 criterios de
aceptación numerados y, a veces, una línea de "Notas del equipo". Variá:

- **Dominio**: banca, e-commerce, salud, logística, RRHH, educación, gobierno, seguros, viajes, SaaS B2B.
- **Tipo de funcionalidad**: alta/edición/baja de entidades, login/autenticación/recuperación de acceso, formulario
  con validaciones, integración con un tercero (pasarela, API, servicio de mails/SMS), reporte o exportación,
  subida de archivos, búsqueda y filtros, pagos o acciones irreversibles, notificaciones, permisos y roles.
- **Calidad**: algunas con lenguaje vago ("rápidamente", "adecuado", "etc.", "si es posible"), otras bien escritas.
  Incluí al menos una HU **sin criterios de aceptación** y al menos una **muy completa** (pocas lagunas).

Para cada HU listá:

- `lagunas`: entre 3 y 8 cosas que un QA senior le preguntaría al PO **porque la HU no las define** y cambian el
  diseño de las pruebas (límites y formatos de datos, comportamiento ante errores, estados de la entidad, permisos,
  seguridad, concurrencia/doble envío, dependencias externas, rangos y zonas horarias, volumen, i18n/dispositivos,
  accesibilidad, mensajes exactos de error). Cada laguna con `match`: 2 a 5 **raíces de palabras** en minúscula
  (sin símbolos) que aparecerían en una pregunta que la cubra. Ej.: `["expir", "vigen", "venc"]`.
- `no_preguntar`: 1 a 3 temas que la HU **sí define explícitamente** (preguntarlos sería un falso positivo), con su
  `match` igual que arriba.

## Parte B — Reportes de bug informales

Cada reporte es un mensaje real de chat, mail o audio transcripto de un usuario, soporte o comercial: con
muletillas, desorden, datos a medias, opiniones mezcladas con hechos. Variá: canal, tono, cuánto información trae
(algunos casi completos, otros muy pobres), y incluí **trampas**: hipótesis del reportero presentadas como hecho
("seguro es por el último deploy"), datos dichos con duda ("creo que era Chrome"), texto de error parafraseado,
y al menos un reporte con **dos defectos distintos**.

Para cada reporte indicá el golden según esta taxonomía del equipo:

- **Severidad** (impacto, no urgencia): S1 bloquea un flujo crítico sin workaround, o pierde/corrompe datos;
  S2 funcionalidad clave degradada con workaround difícil o solo para un subconjunto de usuarios; S3 funcionalidad
  secundaria o workaround simple; S4 cosmético. Seguridad nunca baja de S2. Pérdida de datos siempre S1.
- `severidad_esperada`: el nivel que corresponde **solo con lo que dice el reporte**; si depende de algo que no
  dice, marcá `preliminar: true` y en `condicionada_a` qué dato la cambiaría.
- `features`: para cada una, `true`, `false` o `null` (= el reporte no lo dice), con `cita` textual si no es null:
  `data_loss`, `security`, `blocks_critical_flow`, `workaround_exists`, `affects_subset_only`, `cosmetic_only`,
  `regression`, `in_production`, `before_release`.
- `faltantes_criticos`: subconjunto de `steps, observed, expected, error_text, app_version, environment, platform`
  que el reporte NO trae (error_text cuenta como faltante si solo hay paráfrasis).
- `datos_dudosos`: citas textuales donde el reportero expresa duda.
- `hipotesis`: citas de conjeturas del reportero que NO deben tratarse como hechos.

## Formato de salida (obligatorio, para importarlo automáticamente)

Separá cada archivo con una línea `=== FILE: <ruta> ===`. Sin texto fuera de los archivos. IDs: `HU-D{SEMILLA}NN`
y `BUG-D{SEMILLA}NN` (NN = 01, 02…).

```
=== FILE: hu/HU-D101.md ===
## HU-D101 — <Título>

**Como** <rol>,
**quiero** <acción>,
**para** <objetivo>.

**Criterios de aceptación:**

1. ...
2. ...

**Notas del equipo:** ...
=== FILE: golden/hu-d101.gaps.yaml ===
story: HU-D101
dominio: banca
tipo: exportación
gaps:
  - id: rango_fechas_maximo
    label: "Rango máximo de fechas"
    match: ["rango", "máximo", "meses"]
no_preguntar:
  - id: formatos
    label: "Formatos de archivo (los define el CA-1)"
    match: ["formato", "csv"]
=== FILE: bugs/BUG-D101.md ===
<el mensaje tal cual, sin encabezados>
=== FILE: golden/bug-d101.yaml ===
bug: BUG-D101
dos_defectos: false
severidad_esperada: S2
preliminar: true
condicionada_a: ["data_loss"]
justificacion: "..."
features:
  data_loss: { value: null }
  blocks_critical_flow: { value: true, cita: "no puedo entrar" }
  ...
faltantes_criticos: ["app_version", "error_text"]
datos_dudosos: ["creo que era chrome"]
hipotesis: ["seguro es por el deploy"]
```
