# Prompt de extracción del TestModel (una extracción independiente)

> Se usa N veces (idealmente 3) en contextos **independientes** —subagentes en paralelo, o conversaciones nuevas—
> y después `tbg consensus` fusiona las extracciones por voto mayoritario (self-consistency, Wang et al. 2023).
> Cada extracción NO debe ver las otras.

---

Sos un analista de QA. Leé la historia de usuario en `{HU}` y escribí un TestModel en `{SALIDA}`.

1. Obtené el contrato con `tbg schema test-model` (`.venv/Scripts/tbg` en Windows, `.venv/bin/tbg` en Linux/macOS)
   y los tags válidos en `rules/tags.yaml`. Corré `tbg lint-hu {HU}` para ver los tags sugeridos.
2. Escribí el JSON siguiendo estas reglas y convenciones (las convenciones existen para que extracciones
   independientes coincidan y el consenso funcione):

**Contenido**
- `acceptance_criteria[].text`: cada CA copiado **literal** de la HU, con id `CA-1`, `CA-2`… en orden.
- `parameters`: una categoría por cada **dato que ingresa o elige el usuario** y por cada **condición del sistema
  mencionada explícitamente** en la HU (estado de los datos, disponibilidad de un servicio nombrado en las notas).
  No modeles seguridad, expiración, sesiones, rate limit, permisos ni navegadores: las reglas de `tbg` ya los cubren.
- `choices`: particiones de equivalencia. La primera `valid` es la típica. `invalid` = el sistema debe rechazarla.
  `exception` = condición adversa del entorno.
- `example`: valor concreto y realista (`qa.usuario01@empresa.com`, `01/09/2026`). `""` = vacío.
- `expected` + `quote`: solo si la HU dice qué pasa (cita textual). Si no lo dice: `expected: null`.
- `assumed: true` si que la partición sea válida/inválida es suposición tuya.
- `bounds` solo si la HU da números; si deberían existir y no están: `bounds: null`, `bounds_relevant: true`.
- `constraints` solo para combinaciones imposibles de ejecutar.

**Convenciones de nombres** (snake_case, sin tildes)
- Parámetro = nombre del campo o condición tal como lo nombra la HU: `fecha_desde`, `fecha_hasta`, `formato`, `cuenta`.
  **Un parámetro por campo**: no agrupes dos campos en uno (`desde` y `hasta` van separados).
- Condición de datos: `<entidad>_en_<contexto>` o como la nombre la HU: `movimientos_en_rango`.
- Servicio/dependencia: `<servicio>_estado` con `disponible` (valid) y `caido` (exception).
- Elección válida = el valor o la clase: `csv`, `cuenta_ars`, `con_movimientos`.
- Elección inválida = el problema: `vacio`, `formato_invalido`, `futura`, `sin_seleccionar`.
- Validación entre dos campos: va en el **segundo** campo del formulario, nombrada `anterior_a_<primer_campo>` /
  `posterior_a_<primer_campo>` (ej. en `fecha_hasta`: `anterior_a_fecha_desde`).

3. Corré `tbg check-model {SALIDA} --hu {HU}` y corregí hasta 0 errores. No generes frames ni casos.

Respondé solo con la ruta del archivo y la cantidad de parámetros.
