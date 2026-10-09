# Suite de pruebas — HU-202: Exportación de movimientos de cuenta

> Generada por `tbg` (modelo `f89a55ebedca`). Diseño de casos, IDs, prioridades, cobertura y auto-revisión
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
- **Parámetros modelados (Category-Partition)**: `cuenta` (3 particiones), `fecha_desde` (3 particiones), `fecha_hasta` (2 particiones), `formato` (4 particiones), `movimientos_en_rango` (2 particiones), `generacion_archivo` (2 particiones)
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

**P-7. [B. Datos] ¿Cuáles son los límites de «Fecha inicial del rango a exportar» (mínimo/máximo)?**
- **Por qué importa**: Sin límites no se pueden calcular los valores de borde (mín-1, mín, máx, máx+1).
- **Default propuesto**: Se prueba con valores típicos; los bordes quedan como exploratorios.

**P-8. [J. Contexto] ¿En qué idiomas se muestra/envía el contenido y qué navegadores/dispositivos se soportan?**
- **Por qué importa**: Define el alcance de i18n y de compatibilidad.
- **Default propuesto**: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil.

## 3. Casos de prueba

### CP-001 — Verificar que el cliente exporta en CSV los movimientos de su cuenta en ARS del 01/09/2026 al 30/09/2026 y el archivo se descarga con el nombre esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que el cliente exporta en CSV los movimientos de su cuenta en ARS del 01/09/2026 al 30/09/2026 y el archivo se descarga con el nombre esperado |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Verificar el nombre del archivo descargado | El archivo se llama movimientos_<cuenta>_<desde>_<hasta>.csv, con <cuenta> de "Caja de ahorro en pesos 0010-1234567/8 (ARS)", <desde> de 01/09/2026 y <hasta> de 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre] |
| 8 | Abrir el archivo CSV descargado | El archivo contiene los movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo, y los importes figuran en ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y archivo .csv descargado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: ac-happy-path._ |

### CP-002 — Verificar que se exportan en XLSX los movimientos de la cuenta en USD del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exportan en XLSX los movimientos de la cuenta en USD del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en dólares 0010-7654321/9 (USD)". La cuenta tiene movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en dólares 0010-7654321/9 (USD) · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en dólares 0010-7654321/9 (USD)" | El selector de cuenta muestra "Caja de ahorro en dólares 0010-7654321/9 (USD)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "XLSX" | El selector de formato muestra "XLSX" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Verificar el nombre del archivo descargado | El archivo se llama movimientos_<cuenta>_<desde>_<hasta>.xlsx, con <cuenta> de "Caja de ahorro en dólares 0010-7654321/9 (USD)", <desde> de 01/09/2026 y <hasta> de 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre] |
| 8 | Abrir el archivo XLSX descargado | El archivo contiene los movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo, y los importes figuran en USD |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y archivo .xlsx descargado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-003 — Verificar que se exportan en PDF los movimientos de la cuenta en USD del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exportan en PDF los movimientos de la cuenta en USD del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en dólares 0010-7654321/9 (USD)". La cuenta tiene movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en dólares 0010-7654321/9 (USD) · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en dólares 0010-7654321/9 (USD)" | El selector de cuenta muestra "Caja de ahorro en dólares 0010-7654321/9 (USD)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "PDF" | El selector de formato muestra "PDF" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Verificar el nombre del archivo descargado | El archivo se llama movimientos_<cuenta>_<desde>_<hasta>.pdf, con <cuenta> de "Caja de ahorro en dólares 0010-7654321/9 (USD)", <desde> de 01/09/2026 y <hasta> de 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre] |
| 8 | Abrir el archivo PDF descargado | El archivo contiene los movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo, y los importes figuran en USD |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y archivo .pdf descargado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-004 — Verificar que se exportan en PDF los movimientos de la cuenta en ARS del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exportan en PDF los movimientos de la cuenta en ARS del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "PDF" | El selector de formato muestra "PDF" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Verificar el nombre del archivo descargado | El archivo se llama movimientos_<cuenta>_<desde>_<hasta>.pdf, con <cuenta> de "Caja de ahorro en pesos 0010-1234567/8 (ARS)", <desde> de 01/09/2026 y <hasta> de 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre] |
| 8 | Abrir el archivo PDF descargado | El archivo contiene los movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo, y los importes figuran en ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y archivo .pdf descargado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-005 — Verificar que se exportan en XLSX los movimientos de la cuenta en ARS del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exportan en XLSX los movimientos de la cuenta en ARS del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "XLSX" | El selector de formato muestra "XLSX" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Verificar el nombre del archivo descargado | El archivo se llama movimientos_<cuenta>_<desde>_<hasta>.xlsx, con <cuenta> de "Caja de ahorro en pesos 0010-1234567/8 (ARS)", <desde> de 01/09/2026 y <hasta> de 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre] |
| 8 | Abrir el archivo XLSX descargado | El archivo contiene los movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo, y los importes figuran en ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y archivo .xlsx descargado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-006 — Verificar que se exportan en CSV los movimientos de la cuenta en USD del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exportan en CSV los movimientos de la cuenta en USD del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en dólares 0010-7654321/9 (USD)". La cuenta tiene movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en dólares 0010-7654321/9 (USD) · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en dólares 0010-7654321/9 (USD)" | El selector de cuenta muestra "Caja de ahorro en dólares 0010-7654321/9 (USD)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Verificar el nombre del archivo descargado | El archivo se llama movimientos_<cuenta>_<desde>_<hasta>.csv, con <cuenta> de "Caja de ahorro en dólares 0010-7654321/9 (USD)", <desde> de 01/09/2026 y <hasta> de 30/09/2026 [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre] |
| 8 | Abrir el archivo CSV descargado | El archivo contiene los movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo, y los importes figuran en USD |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y archivo .csv descargado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-007 — Verificar que no se exporta si no se selecciona ninguna cuenta

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta si no se selecciona ninguna cuenta |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026; Servicio operativo; '' (vacío). |
| **Datos de prueba** | `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: CSV · `movimientos_en_rango`: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026 · `generacion_archivo`: Servicio operativo · `cuenta`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Dejar el selector de cuenta sin seleccionar | El selector de cuenta muestra ninguna cuenta seleccionada |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema no genera ni descarga ningún archivo y muestra un mensaje de error que indica que debe seleccionarse una cuenta [SUPUESTO: la HU no define el texto del mensaje ni la validación; se asume rechazo con mensaje explicativo sin cambiar el estado] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «No se selecciona ninguna cuenta» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.cuenta.sin_cuenta)]` _Técnica: error-choice._ |

### CP-008 — Verificar que no se exporta si la fecha desde está vacía

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta si la fecha desde está vacía |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: '' (vacío). |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `fecha_hasta`: 30/09/2026 · `formato`: CSV · `fecha_desde`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Dejar vacío el campo de fecha desde | El campo de fecha desde muestra vacío |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema no genera ni descarga ningún archivo y muestra un mensaje de error que indica que debe completarse la fecha desde [SUPUESTO: la HU no define el texto del mensaje ni la validación; se asume rechazo con mensaje explicativo sin cambiar el estado] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha desde sin completar» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_vacia)]` _Técnica: error-choice._ |

### CP-009 — Verificar que no se exporta si la fecha desde (30/09/2026) es posterior a la fecha hasta (01/09/2026)

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta si la fecha desde (30/09/2026) es posterior a la fecha hasta (01/09/2026) |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: 30/09/2026 (con hasta 01/09/2026). |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `fecha_hasta`: 30/09/2026 · `formato`: CSV · `fecha_desde`: 30/09/2026 (con hasta 01/09/2026) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "30/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "30/09/2026" |
| 4 | Ingresar "01/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "01/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema no genera ni descarga ningún archivo y muestra un mensaje de error que indica que la fecha desde no puede ser posterior a la fecha hasta [SUPUESTO: la HU no define el texto del mensaje ni la validación; se asume rechazo con mensaje explicativo sin cambiar el estado] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha desde posterior a la fecha hasta (rango invertido)» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_posterior_a_hasta)]` _Técnica: error-choice._ |

### CP-010 — Verificar que no se exporta si la fecha hasta está vacía

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta si la fecha hasta está vacía |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: '' (vacío). |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `fecha_desde`: 01/09/2026 · `formato`: CSV · `fecha_hasta`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Dejar vacío el campo de fecha hasta | El campo de fecha hasta muestra vacío |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema no genera ni descarga ningún archivo y muestra un mensaje de error que indica que debe completarse la fecha hasta [SUPUESTO: la HU no define el texto del mensaje ni la validación; se asume rechazo con mensaje explicativo sin cambiar el estado] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha hasta sin completar» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_hasta.fecha_vacia)]` _Técnica: error-choice._ |

### CP-011 — Verificar que no se exporta si no se selecciona ningún formato

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta si no se selecciona ningún formato |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026; Servicio operativo; '' (vacío). |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `movimientos_en_rango`: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026 · `generacion_archivo`: Servicio operativo · `formato`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Dejar sin seleccionar el formato | El selector de formato muestra ningún formato seleccionado |
| 6 | Tocar el botón "Exportar" | El sistema no genera ni descarga ningún archivo y muestra un mensaje de error que indica que debe seleccionarse un formato [SUPUESTO: la HU no define el texto del mensaje ni la validación; se asume rechazo con mensaje explicativo sin cambiar el estado] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «No se selecciona ningún formato» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.formato.sin_formato)]` _Técnica: error-choice._ |

### CP-012 — Verificar que un usuario sin permiso no puede exportar ni ver los movimientos de una cuenta ajena

| Campo | Valor |
|---|---|
| **Título** | Verificar que un usuario sin permiso no puede exportar ni ver los movimientos de una cuenta ajena |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Existen dos clientes: qa.usuario01@empresa.com (titular de la cuenta 0010-1234567/8) y qa.usuario02@empresa.com (titular de otra cuenta). Se conoce el identificador de la cuenta 0010-1234567/8. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión como qa.usuario02@empresa.com | Se muestra el home banking del usuario qa.usuario02@empresa.com |
| 2 | Ingresar a la sección "Movimientos" | El selector de cuenta lista solo las cuentas de qa.usuario02@empresa.com y no incluye la cuenta 0010-1234567/8 |
| 3 | Enviar la solicitud de exportación de la cuenta 0010-1234567/8 desde 01/09/2026 hasta 30/09/2026 en CSV con un cliente HTTP usando la sesión de qa.usuario02@empresa.com | La solicitud es rechazada con respuesta 403 y no se descarga ningún archivo ni se exponen datos de la cuenta ajena [SUPUESTO: solo el titular de la cuenta puede exportar; otro usuario autenticado recibe 403] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Respuesta HTTP 403 capturada y selector de cuentas del usuario |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Solo el titular de la cuenta; otro usuario autenticado recibe 403 y no ve datos ajenos. (ver roles.permissions)]` _Técnica: rule:roles.permissions._ |

### CP-013 — Verificar que la exportación de un período sin datos informa que no hay movimientos y no genera archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que la exportación de un período sin datos informa que no hay movimientos y no genera archivo |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta no tiene movimientos entre 01/01/2026 y 31/01/2026. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/01/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/01/2026" |
| 4 | Ingresar "31/01/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "31/01/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema muestra el mensaje "No hay movimientos para el período" y no se genera ni descarga ningún archivo [SUPUESTO: texto del mensaje y máximo de 10.000 filas exportables no definidos en la HU] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado y de la ausencia de descarga |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Sin datos: mensaje 'No hay movimientos para el período' y no se genera archivo; máximo 10.000 filas. (ver export.volume)]` _Técnica: rule:export.volume._ |

### CP-014 — Verificar que un doble submit sobre "Exportar" genera una sola exportación

| Campo | Valor |
|---|---|
| **Título** | Verificar que un doble submit sobre "Exportar" genera una sola exportación |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar dos veces seguidas el botón "Exportar" en menos de un segundo | Se registra una sola operación de exportación y se descarga un único archivo movimientos_<cuenta>_<desde>_<hasta>.csv [SUPUESTO: la operación es idempotente ante doble submit] |
| 7 | Revisar la carpeta de descargas | Existe un solo archivo movimientos_<cuenta>_<desde>_<hasta>.csv y no una segunda copia |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la carpeta de descargas y del registro de operaciones |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: La operación es idempotente: el segundo submit no genera un segundo movimiento. (ver money.idempotency)]` _Técnica: rule:money.idempotency._ |

### CP-015 — Verificar que el archivo CSV de la cuenta en ARS incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026

| Campo | Valor |
|---|---|
| **Título** | Verificar que el archivo CSV de la cuenta en ARS incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026 |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2, CA-4 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026; Servicio operativo. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `formato`: CSV · `movimientos_en_rango`: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026 · `generacion_archivo`: Servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Abrir el archivo CSV descargado | El archivo contiene los 25 movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo de cada movimiento, y los importes figuran en ARS |
| 8 | Verificar el tiempo de generación | El archivo se genera dentro del umbral que defina el PO [SUPUESTO: la HU dice "rápidamente" sin umbral; se toma como criterio provisional un máximo de 5 segundos] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Archivo .csv descargado y cronometraje de la generación |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: ac-happy-path._ |

### CP-016 — Verificar que al exportar en XLSX una cuenta en USD sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje

| Campo | Valor |
|---|---|
| **Título** | Verificar que al exportar en XLSX una cuenta en USD sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2, CA-4 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en dólares 0010-7654321/9 (USD)". La cuenta no tiene movimientos entre 01/01/2026 y 31/01/2026. Datos de prueba: Cuenta sin movimientos entre 01/01/2026 y 31/01/2026; Servicio operativo. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en dólares 0010-7654321/9 (USD) · `formato`: XLSX · `movimientos_en_rango`: Cuenta sin movimientos entre 01/01/2026 y 31/01/2026 · `generacion_archivo`: Servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en dólares 0010-7654321/9 (USD)" | El selector de cuenta muestra "Caja de ahorro en dólares 0010-7654321/9 (USD)" |
| 3 | Ingresar "01/01/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/01/2026" |
| 4 | Ingresar "31/01/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "31/01/2026" |
| 5 | Seleccionar el formato "XLSX" | El selector de formato muestra "XLSX" |
| 6 | Tocar el botón "Exportar" | El sistema muestra un mensaje indicando que no hay movimientos en el rango 01/01/2026 al 31/01/2026 y no descarga ningún archivo XLSX [SUPUESTO: la HU solo dice "un mensaje adecuado"; el texto exacto no está definido] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-017 — Verificar que el archivo PDF de la cuenta en USD incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026

| Campo | Valor |
|---|---|
| **Título** | Verificar que el archivo PDF de la cuenta en USD incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026 |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en dólares 0010-7654321/9 (USD)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026; Servicio operativo. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en dólares 0010-7654321/9 (USD) · `formato`: PDF · `movimientos_en_rango`: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026 · `generacion_archivo`: Servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en dólares 0010-7654321/9 (USD)" | El selector de cuenta muestra "Caja de ahorro en dólares 0010-7654321/9 (USD)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "PDF" | El selector de formato muestra "PDF" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Abrir el archivo PDF descargado | El archivo contiene los 25 movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo de cada movimiento, y los importes figuran en USD |
| 8 | Verificar el tiempo de generación | El archivo se genera dentro del umbral que defina el PO [SUPUESTO: la HU dice "rápidamente" sin umbral; se toma como criterio provisional un máximo de 5 segundos] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Archivo .pdf descargado y cronometraje de la generación |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-018 — Verificar que al exportar en PDF una cuenta en ARS sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje

| Campo | Valor |
|---|---|
| **Título** | Verificar que al exportar en PDF una cuenta en ARS sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta no tiene movimientos entre 01/01/2026 y 31/01/2026. Datos de prueba: Cuenta sin movimientos entre 01/01/2026 y 31/01/2026; Servicio operativo. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `formato`: PDF · `movimientos_en_rango`: Cuenta sin movimientos entre 01/01/2026 y 31/01/2026 · `generacion_archivo`: Servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/01/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/01/2026" |
| 4 | Ingresar "31/01/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "31/01/2026" |
| 5 | Seleccionar el formato "PDF" | El selector de formato muestra "PDF" |
| 6 | Tocar el botón "Exportar" | El sistema muestra un mensaje indicando que no hay movimientos en el rango 01/01/2026 al 31/01/2026 y no descarga ningún archivo PDF [SUPUESTO: la HU solo dice "un mensaje adecuado"; el texto exacto no está definido] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-019 — Verificar que el archivo XLSX de la cuenta en ARS incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026

| Campo | Valor |
|---|---|
| **Título** | Verificar que el archivo XLSX de la cuenta en ARS incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026 |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. Datos de prueba: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026; Servicio operativo. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `formato`: XLSX · `movimientos_en_rango`: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026 · `generacion_archivo`: Servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "XLSX" | El selector de formato muestra "XLSX" |
| 6 | Tocar el botón "Exportar" | El sistema genera el archivo y la descarga se inicia |
| 7 | Abrir el archivo XLSX descargado | El archivo contiene los 25 movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo de cada movimiento, y los importes figuran en ARS |
| 8 | Verificar el tiempo de generación | El archivo se genera dentro del umbral que defina el PO [SUPUESTO: la HU dice "rápidamente" sin umbral; se toma como criterio provisional un máximo de 5 segundos] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Archivo .xlsx descargado y cronometraje de la generación |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-020 — Verificar que al exportar en CSV una cuenta en USD sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje

| Campo | Valor |
|---|---|
| **Título** | Verificar que al exportar en CSV una cuenta en USD sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en dólares 0010-7654321/9 (USD)". La cuenta no tiene movimientos entre 01/01/2026 y 31/01/2026. Datos de prueba: Cuenta sin movimientos entre 01/01/2026 y 31/01/2026; Servicio operativo. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en dólares 0010-7654321/9 (USD) · `formato`: CSV · `movimientos_en_rango`: Cuenta sin movimientos entre 01/01/2026 y 31/01/2026 · `generacion_archivo`: Servicio operativo |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en dólares 0010-7654321/9 (USD)" | El selector de cuenta muestra "Caja de ahorro en dólares 0010-7654321/9 (USD)" |
| 3 | Ingresar "01/01/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/01/2026" |
| 4 | Ingresar "31/01/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "31/01/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema muestra un mensaje indicando que no hay movimientos en el rango 01/01/2026 al 31/01/2026 y no descarga ningún archivo CSV [SUPUESTO: la HU solo dice "un mensaje adecuado"; el texto exacto no está definido] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-021 — Verificar que si el servicio de generación de archivos está caído se informa el error y no se descarga ningún archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que si el servicio de generación de archivos está caído se informa el error y no se descarga ningún archivo |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. El servicio de generación de archivos está caído. Datos de prueba: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026; Servicio de generación de archivos caído. |
| **Datos de prueba** | `cuenta`: Caja de ahorro en pesos 0010-1234567/8 (ARS) · `formato`: CSV · `movimientos_en_rango`: Cuenta con 25 movimientos entre 01/09/2026 y 30/09/2026 · `generacion_archivo`: Servicio de generación de archivos caído |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)" | El selector de cuenta muestra "Caja de ahorro en pesos 0010-1234567/8 (ARS)" |
| 3 | Ingresar "01/09/2026" en el campo de fecha desde | El campo de fecha desde muestra "01/09/2026" |
| 4 | Ingresar "30/09/2026" en el campo de fecha hasta | El campo de fecha hasta muestra "30/09/2026" |
| 5 | Seleccionar el formato "CSV" | El selector de formato muestra "CSV" |
| 6 | Tocar el botón "Exportar" | El sistema muestra un mensaje de error indicando que no se pudo generar el archivo, no descarga ningún archivo y los datos seleccionados siguen cargados en la pantalla [SUPUESTO: la HU no define el comportamiento ante falla del servicio] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.generacion_archivo.servicio_caido)]` _Técnica: error-choice._ |

### CP-022 — Verificar que el flujo de exportación se completa igual en los navegadores soportados

| Campo | Valor |
|---|---|
| **Título** | Verificar que el flujo de exportación se completa igual en los navegadores soportados |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | El cliente tiene sesión iniciada en home banking y posee las cuentas "Caja de ahorro en pesos 0010-1234567/8 (ARS)". La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir home banking en Chrome desktop | Se muestra la pantalla de login en Chrome desktop |
| 2 | Iniciar sesión con el usuario del cliente | Se muestra el home banking en Chrome desktop |
| 3 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" en Chrome desktop con el botón "Exportar" |
| 4 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)", fecha desde "01/09/2026", fecha hasta "30/09/2026" y formato "CSV" | Los cuatro campos muestran los valores elegidos en Chrome desktop |
| 5 | Tocar el botón "Exportar" | En Chrome desktop se descarga el archivo movimientos_<cuenta>_<desde>_<hasta>.csv con los movimientos del período |
| 6 | Abrir home banking en Firefox desktop | Se muestra la pantalla de login en Firefox desktop |
| 7 | Iniciar sesión con el usuario del cliente | Se muestra el home banking en Firefox desktop |
| 8 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" en Firefox desktop con el botón "Exportar" |
| 9 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)", fecha desde "01/09/2026", fecha hasta "30/09/2026" y formato "CSV" | Los cuatro campos muestran los valores elegidos en Firefox desktop |
| 10 | Tocar el botón "Exportar" | En Firefox desktop se descarga el archivo movimientos_<cuenta>_<desde>_<hasta>.csv con los movimientos del período |
| 11 | Abrir home banking en Safari desktop | Se muestra la pantalla de login en Safari desktop |
| 12 | Iniciar sesión con el usuario del cliente | Se muestra el home banking en Safari desktop |
| 13 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" en Safari desktop con el botón "Exportar" |
| 14 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)", fecha desde "01/09/2026", fecha hasta "30/09/2026" y formato "CSV" | Los cuatro campos muestran los valores elegidos en Safari desktop |
| 15 | Tocar el botón "Exportar" | En Safari desktop se descarga el archivo movimientos_<cuenta>_<desde>_<hasta>.csv con los movimientos del período |
| 16 | Abrir home banking en Chrome móvil | Se muestra la pantalla de login en Chrome móvil |
| 17 | Iniciar sesión con el usuario del cliente | Se muestra el home banking en Chrome móvil |
| 18 | Ingresar a la sección "Movimientos" | Se muestra la pantalla "Movimientos" en Chrome móvil con el botón "Exportar" |
| 19 | Seleccionar la cuenta "Caja de ahorro en pesos 0010-1234567/8 (ARS)", fecha desde "01/09/2026", fecha hasta "30/09/2026" y formato "CSV" | Los cuatro campos muestran los valores elegidos en Chrome móvil |
| 20 | Tocar el botón "Exportar" | En Chrome móvil se descarga el archivo movimientos_<cuenta>_<desde>_<hasta>.csv con los movimientos del período |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas de la descarga en cada navegador [SUPUESTO: navegadores soportados: Chrome, Firefox y Safari desktop + Chrome móvil; solo español] |
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
| CP-012 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-013 | Alta | Medio | Alta | Prob. Alta (tipo Borde) × Impacto Medio (tipo Borde en funcionalidad crítica) → Alta |
| CP-014 | Media | Alto | Alta | Prob. Media (tipo Excepción) × Impacto Alto (regla de G. Concurrencia) → Alta |
| CP-015 | Baja | Alto | Alta | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media; humo → Alta |
| CP-016 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-017 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-018 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-019 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-020 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-021 | Media | Medio | Media | Prob. Media (tipo Excepción) × Impacto Medio (tipo Excepción en funcionalidad crítica) → Media |
| CP-022 | Media | Medio | Media | Prob. Media (tipo No funcional) × Impacto Medio (tipo No funcional en funcionalidad crítica) → Media |

**Orden de ejecución sugerido:** CP-001 → CP-015 → CP-013 → CP-014 → CP-002 → CP-003 → CP-004 → CP-005 → CP-006 → CP-007 → CP-008 → CP-009 → CP-010 → CP-011 → CP-012 → CP-016 → CP-017 → CP-018 → CP-019 → CP-020 → CP-021 → CP-022

**Subset de humo:** CP-001, CP-015

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar". | CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008, CP-009, CP-010, CP-011, CP-012, CP-013, CP-014 | ✓ Cubierta |
| CA-2 | El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo. | CP-007, CP-011, CP-015, CP-016, CP-017, CP-018, CP-019, CP-020, CP-021 | ✓ Cubierta |
| CA-3 | El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`. | CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008, CP-009, CP-010, CP-011 | ✓ Cubierta |
| CA-4 | Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado. | CP-015, CP-016, CP-022 | ✓ Cubierta |

**Cobertura de CAs: 4/4 (100.0%).**
Cobertura 2-wise de particiones válidas: 57/57 pares (100.0%).
Cobertura de valores límite: 0/0 (100.0%) — ningún parámetro tiene límites definidos aún (ver preguntas sobre límites).

## 6. Supuestos asumidos

1. `[SUPUESTO: «No se selecciona ninguna cuenta» se considera inválido aunque la HU no lo dice]` — en CP-007.
2. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.cuenta.sin_cuenta)]` — en CP-007.
3. `[SUPUESTO: «Fecha desde sin completar» se considera inválido aunque la HU no lo dice]` — en CP-008.
4. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_vacia)]` — en CP-008.
5. `[SUPUESTO: «Fecha desde posterior a la fecha hasta (rango invertido)» se considera inválido aunque la HU no lo dice]` — en CP-009.
6. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_posterior_a_hasta)]` — en CP-009.
7. `[SUPUESTO: «Fecha hasta sin completar» se considera inválido aunque la HU no lo dice]` — en CP-010.
8. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_hasta.fecha_vacia)]` — en CP-010.
9. `[SUPUESTO: «No se selecciona ningún formato» se considera inválido aunque la HU no lo dice]` — en CP-011.
10. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.formato.sin_formato)]` — en CP-011.
11. `[SUPUESTO: Solo el titular de la cuenta; otro usuario autenticado recibe 403 y no ve datos ajenos. (ver P-4)]` — en CP-012.
12. `[SUPUESTO: Sin datos: mensaje 'No hay movimientos para el período' y no se genera archivo; máximo 10.000 filas. (ver P-5)]` — en CP-013.
13. `[SUPUESTO: La operación es idempotente: el segundo submit no genera un segundo movimiento. (ver P-3)]` — en CP-014.
14. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.generacion_archivo.servicio_caido)]` — en CP-021.
15. `[SUPUESTO: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil. (ver P-8)]` — en CP-022.
16. `[SUPUESTO: Navegable por teclado con foco visible.]` — laguna menor `context.a11y` no preguntada (tope de preguntas).

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
| O2 — ≥1 negativo/borde cada 2 positivos | No | ✓ 7 negativos/bordes vs 12 funcionales (ratio 0.58) |
| O3 — Subset de humo marcado | No | ✓ CP-001, CP-015 |
| O4 — Sin casos duplicados (mismo título) | No | ✓ |
| O5 — Dependencias entre casos apuntan a casos existentes (referenciar por frame_id F-…) | No | ✓ |

**Gate: APROBADO.**

## 8. Trazabilidad técnica

**Lint de la HU** (Requirements Smells — Femmer et al. 2017; Quality User Story — Lucassen et al. 2016):

- `smell.subjective_language` en CA-4: «adecuado» — Lenguaje subjetivo: su verificación depende de la opinión de quien prueba.
- `smell.ambiguous_adverbs_adjectives` en CA-2: «rápidamente» — Adverbios/adjetivos ambiguos: no fijan un umbral verificable.

**Técnicas de diseño por caso:** ac-happy-path: 2 · error-choice: 6 · pairwise: 10 · rule: 4.

- `ac-happy-path` / `each-choice` / `pairwise`: Category-Partition (Ostrand & Balcer 1988) + cobertura 2-wise (Kuhn et al. 2004).
- `error-choice`: elecciones `[error]` de TSL, un caso cada una sin combinar.
- `bva`: análisis de valores límite (mín-1, mín, mín+1, máx-1, máx, máx+1).
- `rule:<id>`: heurística de `rules/gaps.yaml`.
