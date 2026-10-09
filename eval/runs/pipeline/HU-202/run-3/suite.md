# Suite de pruebas — HU-202: Exportación de movimientos de cuenta

> Generada por `tbg` (modelo `95ea37cef999`). Diseño de casos, IDs, prioridades, cobertura y auto-revisión
> calculados por código; redacción de pasos por el agente, validada por `tbg validate`.

## 1. Resumen del análisis

- **Rol**: cliente de home banking
- **Funcionalidad**: exportar los movimientos de mi cuenta en un rango de fechas
- **Objetivo de negocio**: conciliarlos con mi sistema contable
- **Módulo**: Movimientos
- **Criterios de aceptación:**
  - **CA-1**: Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar".
  - **CA-2**: El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo.
  - **CA-3**: El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`.
  - **CA-4**: Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado.
- **Parámetros modelados (Category-Partition)**: `cuenta` (2 particiones), `rango_fechas` (5 particiones), `formato` (4 particiones), `generacion_archivo` (2 particiones)
- **Tags de riesgo**: dates, export, money, ui
- **Lint de la HU**: 2 hallazgo(s) — ver sección 8.
- **Modo**: completo.

## 2. Preguntas para el PO

**P-1. [A. Criterios de aceptación] En CA-2, «rápidamente» no es verificable: ¿cuál es el resultado/umbral concreto?**
- **Por qué importa**: Adverbios/adjetivos ambiguos: no fijan un umbral verificable. Sin umbral, otra persona no puede decir 'pasó' o 'falló'.
- **Default propuesto**: Se prueba de forma exploratoria y se documenta lo observado.

**P-2. [A. Criterios de aceptación] En CA-4, «adecuado» no es verificable: ¿cuál es el resultado/umbral concreto?**
- **Por qué importa**: Lenguaje subjetivo: su verificación depende de la opinión de quien prueba. Sin umbral, otra persona no puede decir 'pasó' o 'falló'.
- **Default propuesto**: Se prueba de forma exploratoria y se documenta lo observado.

**P-3. [G. Concurrencia] ¿Qué pasa ante doble submit o reintento de la operación? ¿Se garantiza que se ejecute una sola vez?**
- **Por qué importa**: En operaciones de dinero, un doble submit genera cobros/movimientos duplicados.
- **Default propuesto**: La operación es idempotente: el segundo submit no genera un segundo movimiento.

**P-4. [D. Permisos] ¿Qué roles pueden ejecutar la funcionalidad y cuáles NO? ¿Ve cada usuario solo sus propios datos?**
- **Por qué importa**: La autorización se prueba con un rol SIN permiso; sin definición no se puede diseñar ese negativo.
- **Default propuesto**: Solo el titular de la cuenta; otro usuario autenticado recibe 403 y no ve datos ajenos.

**P-5. [B. Datos] ¿Qué pasa si no hay datos en el rango y cuál es el volumen máximo exportable?**
- **Por qué importa**: Reporte vacío y reporte masivo son los bordes clásicos de un export.
- **Default propuesto**: Sin datos: mensaje 'No hay movimientos para el período' y no se genera archivo; máximo 10.000 filas.

**P-6. [B. Datos] ¿Cuál es el rango de fechas máximo permitido y en qué zona horaria se interpretan las fechas?**
- **Por qué importa**: Define bordes del rango (desde > hasta, rango máximo ±1) y errores por zona horaria en los cortes de día.
- **Default propuesto**: Rango máximo de 12 meses, 'desde' ≤ 'hasta', fechas en hora de Argentina (UTC-3).

**P-7. [B. Datos] ¿Cuáles son los límites de «Rango de fechas desde/hasta del período a exportar.» (mínimo/máximo)?**
- **Por qué importa**: Sin límites no se pueden calcular los valores de borde (mín-1, mín, máx, máx+1).
- **Default propuesto**: Se prueba con valores típicos; los bordes quedan como exploratorios.

**P-8. [J. Contexto] ¿En qué idiomas se muestra/envía el contenido y qué navegadores/dispositivos se soportan?**
- **Por qué importa**: Define el alcance de i18n y de compatibilidad.
- **Default propuesto**: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil.

## 3. Casos de prueba

### CP-001 — Verificar que se exporta en CSV los movimientos de una cuenta en ARS con un rango con movimientos

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta en CSV los movimientos de una cuenta en ARS con un rango con movimientos |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3, CA-4 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678, con movimientos registrados entre 01/09/2026 y 30/09/2026; rango de fechas de prueba: desde 01/09/2026 hasta 30/09/2026; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `rango_fechas`: desde 01/09/2026 hasta 30/09/2026 · `formato`: CSV · `generacion_archivo`: servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta Caja de ahorro ARS 0012345678 queda seleccionada |
| 4 | Ingresar la fecha desde 01/09/2026 | El campo desde muestra 01/09/2026 |
| 5 | Ingresar la fecha hasta 30/09/2026 | El campo hasta muestra 30/09/2026 |
| 6 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema inicia la generación del archivo |
| 8 | Observar la descarga del archivo | Se descarga un archivo con nombre movimientos_<cuenta>_<desde>_<hasta>.csv correspondiente a la cuenta Caja de ahorro ARS 0012345678, desde 01/09/2026 hasta 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre del archivo] |
| 9 | Abrir el archivo CSV descargado | El archivo contiene los movimientos del período 01/09/2026 a 30/09/2026, con fecha, descripción, importe y saldo de cada movimiento |
| 10 | Revisar los importes y el saldo del archivo | Los importes y el saldo se expresan en ARS (pesos), la moneda de la cuenta |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla de selección, archivo CSV descargado (nombre visible) y su contenido |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: ac-happy-path._ |

### CP-002 — Verificar que se exporta en PDF los movimientos de una cuenta en USD con un rango con movimientos

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta en PDF los movimientos de una cuenta en USD con un rango con movimientos |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro USD 0087654321, con movimientos registrados entre 01/09/2026 y 30/09/2026; rango de fechas de prueba: desde 01/09/2026 hasta 30/09/2026; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro USD 0087654321 · `rango_fechas`: desde 01/09/2026 hasta 30/09/2026 · `formato`: PDF · `generacion_archivo`: servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro USD 0087654321 | La cuenta Caja de ahorro USD 0087654321 queda seleccionada |
| 4 | Ingresar la fecha desde 01/09/2026 | El campo desde muestra 01/09/2026 |
| 5 | Ingresar la fecha hasta 30/09/2026 | El campo hasta muestra 30/09/2026 |
| 6 | Seleccionar el formato PDF | El formato PDF queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema inicia la generación del archivo |
| 8 | Observar la descarga del archivo | Se descarga un archivo con nombre movimientos_<cuenta>_<desde>_<hasta>.pdf correspondiente a la cuenta Caja de ahorro USD 0087654321, desde 01/09/2026 hasta 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre del archivo] |
| 9 | Abrir el archivo PDF descargado | El archivo contiene los movimientos del período 01/09/2026 a 30/09/2026, con fecha, descripción, importe y saldo de cada movimiento |
| 10 | Revisar los importes y el saldo del archivo | Los importes y el saldo se expresan en USD (dólares), la moneda de la cuenta |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla de selección, archivo PDF descargado (nombre visible) y su contenido |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-003 — Verificar que se muestra un mensaje al exportar en PDF un rango sin movimientos de una cuenta en ARS

| Campo | Valor |
|---|---|
| **Título** | Verificar que se muestra un mensaje al exportar en PDF un rango sin movimientos de una cuenta en ARS |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678, sin movimientos registrados entre 01/01/2020 y 31/01/2020; rango de fechas de prueba: desde 01/01/2020 hasta 31/01/2020; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `rango_fechas`: desde 01/01/2020 hasta 31/01/2020 · `formato`: PDF · `generacion_archivo`: servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta Caja de ahorro ARS 0012345678 queda seleccionada |
| 4 | Ingresar la fecha desde 01/01/2020 | El campo desde muestra 01/01/2020 |
| 5 | Ingresar la fecha hasta 31/01/2020 | El campo hasta muestra 31/01/2020 |
| 6 | Seleccionar el formato PDF | El formato PDF queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema procesa la solicitud de exportación |
| 8 | Observar la pantalla tras la solicitud | Se muestra un mensaje en pantalla indicando que no hay movimientos en el rango 01/01/2020 a 31/01/2020 [SUPUESTO: la HU solo dice "un mensaje adecuado"; el texto exacto no está definido] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-004 — Verificar que se muestra un mensaje al exportar en XLSX un rango sin movimientos de una cuenta en ARS

| Campo | Valor |
|---|---|
| **Título** | Verificar que se muestra un mensaje al exportar en XLSX un rango sin movimientos de una cuenta en ARS |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678, sin movimientos registrados entre 01/01/2020 y 31/01/2020; rango de fechas de prueba: desde 01/01/2020 hasta 31/01/2020; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `rango_fechas`: desde 01/01/2020 hasta 31/01/2020 · `formato`: XLSX · `generacion_archivo`: servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta Caja de ahorro ARS 0012345678 queda seleccionada |
| 4 | Ingresar la fecha desde 01/01/2020 | El campo desde muestra 01/01/2020 |
| 5 | Ingresar la fecha hasta 31/01/2020 | El campo hasta muestra 31/01/2020 |
| 6 | Seleccionar el formato XLSX | El formato XLSX queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema procesa la solicitud de exportación |
| 8 | Observar la pantalla tras la solicitud | Se muestra un mensaje en pantalla indicando que no hay movimientos en el rango 01/01/2020 a 31/01/2020 [SUPUESTO: la HU solo dice "un mensaje adecuado"; el texto exacto no está definido] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-005 — Verificar que se muestra un mensaje al exportar en CSV un rango sin movimientos de una cuenta en USD

| Campo | Valor |
|---|---|
| **Título** | Verificar que se muestra un mensaje al exportar en CSV un rango sin movimientos de una cuenta en USD |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro USD 0087654321, sin movimientos registrados entre 01/01/2020 y 31/01/2020; rango de fechas de prueba: desde 01/01/2020 hasta 31/01/2020; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro USD 0087654321 · `rango_fechas`: desde 01/01/2020 hasta 31/01/2020 · `formato`: CSV · `generacion_archivo`: servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro USD 0087654321 | La cuenta Caja de ahorro USD 0087654321 queda seleccionada |
| 4 | Ingresar la fecha desde 01/01/2020 | El campo desde muestra 01/01/2020 |
| 5 | Ingresar la fecha hasta 31/01/2020 | El campo hasta muestra 31/01/2020 |
| 6 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema procesa la solicitud de exportación |
| 8 | Observar la pantalla tras la solicitud | Se muestra un mensaje en pantalla indicando que no hay movimientos en el rango 01/01/2020 a 31/01/2020 [SUPUESTO: la HU solo dice "un mensaje adecuado"; el texto exacto no está definido] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-006 — Verificar que se exporta en XLSX los movimientos de una cuenta en USD con un rango con movimientos

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta en XLSX los movimientos de una cuenta en USD con un rango con movimientos |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro USD 0087654321, con movimientos registrados entre 01/09/2026 y 30/09/2026; rango de fechas de prueba: desde 01/09/2026 hasta 30/09/2026; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro USD 0087654321 · `rango_fechas`: desde 01/09/2026 hasta 30/09/2026 · `formato`: XLSX · `generacion_archivo`: servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro USD 0087654321 | La cuenta Caja de ahorro USD 0087654321 queda seleccionada |
| 4 | Ingresar la fecha desde 01/09/2026 | El campo desde muestra 01/09/2026 |
| 5 | Ingresar la fecha hasta 30/09/2026 | El campo hasta muestra 30/09/2026 |
| 6 | Seleccionar el formato XLSX | El formato XLSX queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema inicia la generación del archivo |
| 8 | Observar la descarga del archivo | Se descarga un archivo con nombre movimientos_<cuenta>_<desde>_<hasta>.xlsx correspondiente a la cuenta Caja de ahorro USD 0087654321, desde 01/09/2026 hasta 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre del archivo] |
| 9 | Abrir el archivo XLSX descargado | El archivo contiene los movimientos del período 01/09/2026 a 30/09/2026, con fecha, descripción, importe y saldo de cada movimiento |
| 10 | Revisar los importes y el saldo del archivo | Los importes y el saldo se expresan en USD (dólares), la moneda de la cuenta |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla de selección, archivo XLSX descargado (nombre visible) y su contenido |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-007 — Verificar que se rechaza la exportación cuando la fecha desde es posterior a la fecha hasta

| Campo | Valor |
|---|---|
| **Título** | Verificar que se rechaza la exportación cuando la fecha desde es posterior a la fecha hasta |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3, CA-4 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678; rango de fechas de prueba: desde 30/09/2026 hasta 01/09/2026; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `formato`: CSV · `generacion_archivo`: servicio operativo · `rango_fechas`: desde 30/09/2026 hasta 01/09/2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta Caja de ahorro ARS 0012345678 queda seleccionada |
| 4 | Ingresar la fecha desde 30/09/2026 | El campo desde muestra 30/09/2026 |
| 5 | Ingresar la fecha hasta 01/09/2026 | El campo hasta muestra 01/09/2026 |
| 6 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema rechaza la solicitud y muestra un mensaje que explica que la fecha desde no puede ser posterior a la fecha hasta; no se descarga ningún archivo [SUPUESTO: la HU no define el rechazo ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje de error y verificación de que no se descargó archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha desde posterior a fecha hasta» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.rango_fechas.desde_posterior_a_hasta)]` _Técnica: error-choice._ |

### CP-008 — Verificar que se rechaza la exportación cuando no se completan las fechas desde y hasta

| Campo | Valor |
|---|---|
| **Título** | Verificar que se rechaza la exportación cuando no se completan las fechas desde y hasta |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3, CA-4 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `formato`: CSV · `generacion_archivo`: servicio operativo · `rango_fechas`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta Caja de ahorro ARS 0012345678 queda seleccionada |
| 4 | Dejar vacíos los campos de fecha desde y hasta | Los campos de fecha desde y hasta permanecen vacíos |
| 5 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 6 | Tocar el botón "Exportar" | El sistema rechaza la solicitud y muestra un mensaje que explica que deben completarse las fechas desde y hasta; no se descarga ningún archivo [SUPUESTO: la HU no define el rechazo ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje de error y verificación de que no se descargó archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Falta completar la fecha desde y/o hasta» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.rango_fechas.fecha_vacia)]` _Técnica: error-choice._ |

### CP-009 — Verificar que se rechaza la exportación cuando la fecha hasta es posterior a la fecha actual

| Campo | Valor |
|---|---|
| **Título** | Verificar que se rechaza la exportación cuando la fecha hasta es posterior a la fecha actual |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3, CA-4 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678; rango de fechas de prueba: desde 01/09/2026 hasta 31/12/2030; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `formato`: CSV · `generacion_archivo`: servicio operativo · `rango_fechas`: desde 01/09/2026 hasta 31/12/2030 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta Caja de ahorro ARS 0012345678 queda seleccionada |
| 4 | Ingresar la fecha desde 01/09/2026 | El campo desde muestra 01/09/2026 |
| 5 | Ingresar la fecha hasta 31/12/2030 | El campo hasta muestra 31/12/2030 |
| 6 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema rechaza la solicitud y muestra un mensaje que explica que la fecha hasta no puede ser posterior a la fecha actual; no se descarga ningún archivo [SUPUESTO: la HU no define el rechazo ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje de error y verificación de que no se descargó archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha hasta posterior a la fecha actual» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.rango_fechas.hasta_futura)]` _Técnica: error-choice._ |

### CP-010 — Verificar que se rechaza la exportación cuando no se selecciona ningún formato

| Campo | Valor |
|---|---|
| **Título** | Verificar que se rechaza la exportación cuando no se selecciona ningún formato |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678; rango de fechas de prueba: desde 01/09/2026 hasta 30/09/2026; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `rango_fechas`: desde 01/09/2026 hasta 30/09/2026 · `generacion_archivo`: servicio operativo · `formato`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta Caja de ahorro ARS 0012345678 queda seleccionada |
| 4 | Ingresar la fecha desde 01/09/2026 | El campo desde muestra 01/09/2026 |
| 5 | Ingresar la fecha hasta 30/09/2026 | El campo hasta muestra 30/09/2026 |
| 6 | No seleccionar ningún formato | Ningún formato (CSV, XLSX o PDF) queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema rechaza la solicitud y muestra un mensaje que explica que debe seleccionarse un formato; no se descarga ningún archivo [SUPUESTO: la HU no define el rechazo ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje de error y verificación de que no se descargó archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «No se selecciona ningún formato» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.formato.sin_formato)]` _Técnica: error-choice._ |

### CP-011 — Verificar que un usuario sin permiso no puede exportar movimientos de una cuenta ajena

| Campo | Valor |
|---|---|
| **Título** | Verificar que un usuario sin permiso no puede exportar movimientos de una cuenta ajena |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Existen dos clientes: el titular de la cuenta Caja de ahorro ARS 0012345678 y otro cliente autenticado que no es titular de esa cuenta |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión con el cliente que no es titular de la cuenta Caja de ahorro ARS 0012345678 | Se muestra el home banking del cliente |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con solo las cuentas propias de ese cliente |
| 3 | Verificar la lista de cuentas seleccionables | La cuenta Caja de ahorro ARS 0012345678 no aparece en la lista |
| 4 | Enviar el pedido de exportación de la cuenta Caja de ahorro ARS 0012345678 directamente al endpoint (por ejemplo con una herramienta de pruebas de API) | El pedido es rechazado con 403 y no se descarga archivo ni se exponen datos ajenos [SUPUESTO: solo el titular puede exportar; ver roles.permissions] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la lista de cuentas y respuesta 403 del pedido |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Solo el titular de la cuenta; otro usuario autenticado recibe 403 y no ve datos ajenos. (ver roles.permissions)]` _Técnica: rule:roles.permissions._ |

### CP-012 — Verificar que una exportación de un período sin datos informa que no hay movimientos y no genera archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que una exportación de un período sin datos informa que no hay movimientos y no genera archivo |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678, sin movimientos entre 01/01/2020 y 31/01/2020 |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde 01/01/2020 | El campo desde muestra 01/01/2020 |
| 4 | Ingresar la fecha hasta 31/01/2020 | El campo hasta muestra 31/01/2020 |
| 5 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 6 | Tocar el botón "Exportar" | Se muestra el mensaje "No hay movimientos para el período" y no se descarga ningún archivo [SUPUESTO: texto del mensaje y no generación de archivo vacío; ver export.volume] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje y verificación de que no hay archivo descargado |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Sin datos: mensaje 'No hay movimientos para el período' y no se genera archivo; máximo 10.000 filas. (ver export.volume)]` _Técnica: rule:export.volume._ |

### CP-013 — Verificar que un doble toque en Exportar genera una sola exportación

| Campo | Valor |
|---|---|
| **Título** | Verificar que un doble toque en Exportar genera una sola exportación |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678 con movimientos entre 01/09/2026 y 30/09/2026 |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde 01/09/2026 | El campo desde muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta 30/09/2026 | El campo hasta muestra 30/09/2026 |
| 5 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 6 | Tocar dos veces seguidas el botón "Exportar" en menos de un segundo | Se registra una sola operación de exportación [SUPUESTO: la operación es idempotente; ver money.idempotency] |
| 7 | Revisar los archivos descargados | Se descargó un único archivo de exportación, sin duplicados |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la carpeta de descargas y del registro de operaciones |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: La operación es idempotente: el segundo submit no genera un segundo movimiento. (ver money.idempotency)]` _Técnica: rule:money.idempotency._ |

### CP-014 — Verificar que se muestra un mensaje al exportar en XLSX un rango sin movimientos de una cuenta en USD

| Campo | Valor |
|---|---|
| **Título** | Verificar que se muestra un mensaje al exportar en XLSX un rango sin movimientos de una cuenta en USD |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2, CA-3, CA-4 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro USD 0087654321, sin movimientos registrados entre 01/01/2020 y 31/01/2020; rango de fechas de prueba: desde 01/01/2020 hasta 31/01/2020; servicio operativo |
| **Datos de prueba** | `cuenta`: Caja de ahorro USD 0087654321 · `rango_fechas`: desde 01/01/2020 hasta 31/01/2020 · `formato`: XLSX · `generacion_archivo`: servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión en el home banking con un cliente titular de la cuenta | Se muestra el home banking con el menú principal |
| 2 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con la opción de exportar |
| 3 | Seleccionar la cuenta Caja de ahorro USD 0087654321 | La cuenta Caja de ahorro USD 0087654321 queda seleccionada |
| 4 | Ingresar la fecha desde 01/01/2020 | El campo desde muestra 01/01/2020 |
| 5 | Ingresar la fecha hasta 31/01/2020 | El campo hasta muestra 31/01/2020 |
| 6 | Seleccionar el formato XLSX | El formato XLSX queda seleccionado |
| 7 | Tocar el botón "Exportar" | El sistema procesa la solicitud de exportación |
| 8 | Observar la pantalla tras la solicitud | Se muestra un mensaje en pantalla indicando que no hay movimientos en el rango 01/01/2020 a 31/01/2020 [SUPUESTO: la HU solo dice "un mensaje adecuado"; el texto exacto no está definido] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla con el mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-015 — Verificar que se informa el error cuando falla el servicio de generación del archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que se informa el error cuando falla el servicio de generación del archivo |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2, CA-3 |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678 con movimientos entre 01/09/2026 y 30/09/2026; servicio de exportación caído (simulado); rango de fechas de prueba: desde 01/09/2026 hasta 30/09/2026 |
| **Datos de prueba** | `cuenta`: Caja de ahorro ARS 0012345678 · `rango_fechas`: desde 01/09/2026 hasta 30/09/2026 · `formato`: CSV · `generacion_archivo`: servicio de exportación caído |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta Caja de ahorro ARS 0012345678 | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde 01/09/2026 | El campo desde muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta 30/09/2026 | El campo hasta muestra 30/09/2026 |
| 5 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 6 | Tocar el botón "Exportar" | El sistema muestra un mensaje que explica que no se pudo generar el archivo, no se descarga ningún archivo y el cliente permanece en la pantalla "Movimientos" con los datos cargados [SUPUESTO: la HU no define el comportamiento ante fallos del servicio] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y verificación de que no hay archivo descargado |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.generacion_archivo.fallo_generacion)]` _Técnica: error-choice._ |

### CP-016 — Verificar que el flujo de exportación se completa igual en los navegadores soportados

| Campo | Valor |
|---|---|
| **Título** | Verificar que el flujo de exportación se completa igual en los navegadores soportados |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado titular de la cuenta Caja de ahorro ARS 0012345678 con movimientos entre 01/09/2026 y 30/09/2026; Chrome, Firefox y Safari desktop y Chrome móvil disponibles |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el home banking en Chrome desktop | Se muestra la pantalla de inicio de sesión |
| 2 | Iniciar sesión con el cliente titular | Se muestra el home banking |
| 3 | Exportar en CSV la cuenta Caja de ahorro ARS 0012345678 del 01/09/2026 al 30/09/2026 desde "Movimientos" | Se descarga el archivo con los movimientos del período |
| 4 | Repetir los pasos anteriores en Firefox desktop | Se descarga el archivo con los mismos movimientos |
| 5 | Repetir los pasos anteriores en Safari desktop | Se descarga el archivo con los mismos movimientos |
| 6 | Repetir los pasos anteriores en Chrome móvil | Se descarga el archivo con los mismos movimientos [SUPUESTO: solo español; Chrome, Firefox y Safari desktop + Chrome móvil; ver context.platform_i18n] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas de cada navegador y archivos descargados |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil. (ver context.platform_i18n)]` _Técnica: rule:context.platform_i18n._ |

## 4. Priorización por riesgo

| Caso | Probabilidad | Impacto | Prioridad | Justificación |
|---|---|---|---|---|
| CP-001 | Baja | Alto | Alta | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media; humo → Alta |
| CP-002 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-003 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-004 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-005 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-006 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-007 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-008 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-009 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-010 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-011 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-012 | Alta | Medio | Alta | Prob. Alta (tipo Borde) × Impacto Medio (tipo Borde en funcionalidad crítica) → Alta |
| CP-013 | Media | Alto | Alta | Prob. Media (tipo Excepción) × Impacto Alto (regla de G. Concurrencia) → Alta |
| CP-014 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-015 | Media | Medio | Media | Prob. Media (tipo Excepción) × Impacto Medio (tipo Excepción en funcionalidad crítica) → Media |
| CP-016 | Media | Medio | Media | Prob. Media (tipo No funcional) × Impacto Medio (tipo No funcional en funcionalidad crítica) → Media |

**Orden de ejecución sugerido:** CP-001 → CP-012 → CP-013 → CP-002 → CP-003 → CP-004 → CP-005 → CP-006 → CP-007 → CP-008 → CP-009 → CP-010 → CP-011 → CP-014 → CP-015 → CP-016

**Subset de humo:** CP-001

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar". | CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008, CP-009, CP-010, CP-011, CP-012, CP-013 | ✓ Cubierta |
| CA-2 | El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo. | CP-001, CP-002, CP-003, CP-007, CP-008, CP-009, CP-014, CP-015 | ✓ Cubierta |
| CA-3 | El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`. | CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008, CP-009, CP-010, CP-014, CP-015 | ✓ Cubierta |
| CA-4 | Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado. | CP-001, CP-007, CP-008, CP-009, CP-014, CP-016 | ✓ Cubierta |

**Cobertura de CAs: 4/4 (100.0%).**
Cobertura 2-wise de particiones válidas: 47/47 pares (100.0%).
Cobertura de valores límite: 0/0 (100.0%) — ningún parámetro tiene límites definidos aún (ver preguntas sobre límites).

## 6. Supuestos asumidos

1. `[SUPUESTO: «Fecha desde posterior a fecha hasta» se considera inválido aunque la HU no lo dice]` — en CP-007.
2. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.rango_fechas.desde_posterior_a_hasta)]` — en CP-007.
3. `[SUPUESTO: «Falta completar la fecha desde y/o hasta» se considera inválido aunque la HU no lo dice]` — en CP-008.
4. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.rango_fechas.fecha_vacia)]` — en CP-008.
5. `[SUPUESTO: «Fecha hasta posterior a la fecha actual» se considera inválido aunque la HU no lo dice]` — en CP-009.
6. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.rango_fechas.hasta_futura)]` — en CP-009.
7. `[SUPUESTO: «No se selecciona ningún formato» se considera inválido aunque la HU no lo dice]` — en CP-010.
8. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.formato.sin_formato)]` — en CP-010.
9. `[SUPUESTO: Solo el titular de la cuenta; otro usuario autenticado recibe 403 y no ve datos ajenos. (ver P-4)]` — en CP-011.
10. `[SUPUESTO: Sin datos: mensaje 'No hay movimientos para el período' y no se genera archivo; máximo 10.000 filas. (ver P-5)]` — en CP-012.
11. `[SUPUESTO: La operación es idempotente: el segundo submit no genera un segundo movimiento. (ver P-3)]` — en CP-013.
12. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.generacion_archivo.fallo_generacion)]` — en CP-015.
13. `[SUPUESTO: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil. (ver P-8)]` — en CP-016.
14. `[SUPUESTO: Navegable por teclado con foco visible.]` — laguna menor `context.a11y` no preguntada (tope de preguntas).

## 7. Auto-revisión (`tbg validate`)

| Ítem | Crítico | Resultado |
|---|---|---|
| C1 — Cada frame tiene exactamente un caso redactado (sin casos inventados) | Sí | ✓ |
| C2 — Cero comportamiento inventado: los frames con supuestos llevan [SUPUESTO] en el caso | Sí | ✓ |
| C3 — Pasos atómicos: una acción por paso | Sí | ✓ |
| C4 — Resultados esperados observables (sin 'correctamente', 'se ve bien', …) | Sí | ✓ |
| C5 — Datos concretos y fieles a los frames (el LLM no cambia ni abstrae los datos) | Sí | ✓ |
| C6 — IDs únicos y secuenciales | Sí | ✓ Asignados por código (CP-001…), no por el LLM |
| C7 — Cada CA cubierta o con motivo explícito | Sí | ✓ 100% de CAs (4/4) — calculado por código |
| C8 — Preguntas al PO ≤ 8, todas con default | Sí | ✓ 8 preguntas |
| O1 — Títulos con formato 'Verificar / Explorar …' | No | ✓ |
| O2 — ≥1 negativo/borde cada 2 positivos | No | ✓ 6 negativos/bordes vs 7 funcionales (ratio 0.86) |
| O3 — Subset de humo marcado | No | ✓ CP-001 |
| O4 — Sin casos duplicados (mismo título) | No | ✓ |
| O5 — Dependencias entre casos apuntan a casos existentes (referenciar por frame_id F-…) | No | ✓ |

**Gate: APROBADO.**

## 8. Trazabilidad técnica

**Lint de la HU** (Requirements Smells — Femmer et al. 2017; Quality User Story — Lucassen et al. 2016):

- `smell.subjective_language` en CA-4: «adecuado» — Lenguaje subjetivo: su verificación depende de la opinión de quien prueba.
- `smell.ambiguous_adverbs_adjectives` en CA-2: «rápidamente» — Adverbios/adjetivos ambiguos: no fijan un umbral verificable.

**Técnicas de diseño por caso:** ac-happy-path: 1 · error-choice: 5 · pairwise: 6 · rule: 4.

- `ac-happy-path` / `each-choice` / `pairwise`: Category-Partition (Ostrand & Balcer 1988) + cobertura 2-wise (Kuhn et al. 2004).
- `error-choice`: elecciones `[error]` de TSL, un caso cada una sin combinar.
- `bva`: análisis de valores límite (mín-1, mín, mín+1, máx-1, máx, máx+1).
- `rule:<id>`: heurística de `rules/gaps.yaml`.
