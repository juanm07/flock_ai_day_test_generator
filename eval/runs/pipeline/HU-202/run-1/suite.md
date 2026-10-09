# Suite de pruebas — HU-202: Exportación de movimientos de cuenta

> Generada por `tbg` (modelo `e72ed75c51b7`). Diseño de casos, IDs, prioridades, cobertura y auto-revisión
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
- **Parámetros modelados (Category-Partition)**: `cuenta` (3 particiones), `fecha_desde` (3 particiones), `fecha_hasta` (3 particiones), `movimientos_periodo` (2 particiones), `formato` (4 particiones), `disponibilidad_servicio` (2 particiones)
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

**P-8. [B. Datos] ¿Cuáles son los límites de «Fecha final del rango a exportar» (mínimo/máximo)?**
- **Por qué importa**: Sin límites no se pueden calcular los valores de borde (mín-1, mín, máx, máx+1).
- **Default propuesto**: Se prueba con valores típicos; los bordes quedan como exploratorios.

## 3. Casos de prueba

### CP-001 — Verificar que se exporta un archivo CSV con los movimientos de una cuenta en ARS para un rango válido

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta un archivo CSV con los movimientos de una cuenta en ARS para un rango válido |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Cliente autenticado en home banking, titular de la Cuenta en ARS 0001234567, con movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha y el selector de formato |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta "Cuenta en ARS 0001234567" queda seleccionada y sus importes se muestran en ARS |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | El sistema genera el archivo CSV con los movimientos del período 01/09/2026 a 30/09/2026 [SUPUESTO: no hay umbral definido para "rápidamente"; se usa el tiempo de espera estándar de la plataforma] |
| 7 | Verificar el nombre del archivo descargado | El archivo se descarga con el nombre movimientos_0001234567_01092026_30092026.csv [SUPUESTO: la HU no define el formato de las fechas ni el identificador de cuenta en el nombre; se asume DDMMAAAA y el número de cuenta] |
| 8 | Abrir el archivo descargado | El archivo contiene las columnas fecha, descripción, importe y saldo, con los importes en ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y del archivo movimientos_0001234567_01092026_30092026.csv abierto |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: ac-happy-path._ |

### CP-002 — Verificar que se exporta un archivo XLSX con los movimientos de una cuenta en USD para un rango válido

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta un archivo XLSX con los movimientos de una cuenta en USD para un rango válido |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de la Cuenta en USD 0007654321, con movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Cuenta en USD 0007654321 · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha y el selector de formato |
| 2 | Seleccionar la cuenta "Cuenta en USD 0007654321" | La cuenta "Cuenta en USD 0007654321" queda seleccionada y sus importes se muestran en USD |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "XLSX" | El formato "XLSX" queda seleccionado |
| 6 | Tocar "Exportar" | El sistema genera el archivo XLSX con los movimientos del período 01/09/2026 a 30/09/2026 [SUPUESTO: no hay umbral definido para "rápidamente"; se usa el tiempo de espera estándar de la plataforma] |
| 7 | Verificar el nombre del archivo descargado | El archivo se descarga con el nombre movimientos_0007654321_01092026_30092026.xlsx [SUPUESTO: la HU no define el formato de las fechas ni el identificador de cuenta en el nombre; se asume DDMMAAAA y el número de cuenta] |
| 8 | Abrir el archivo descargado | El archivo contiene las columnas fecha, descripción, importe y saldo, con los importes en USD |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y del archivo movimientos_0007654321_01092026_30092026.xlsx abierto |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-003 — Verificar que se exporta un archivo PDF con los movimientos de una cuenta en USD para un rango válido

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta un archivo PDF con los movimientos de una cuenta en USD para un rango válido |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de la Cuenta en USD 0007654321, con movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Cuenta en USD 0007654321 · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha y el selector de formato |
| 2 | Seleccionar la cuenta "Cuenta en USD 0007654321" | La cuenta "Cuenta en USD 0007654321" queda seleccionada y sus importes se muestran en USD |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "PDF" | El formato "PDF" queda seleccionado |
| 6 | Tocar "Exportar" | El sistema genera el archivo PDF con los movimientos del período 01/09/2026 a 30/09/2026 [SUPUESTO: no hay umbral definido para "rápidamente"; se usa el tiempo de espera estándar de la plataforma] |
| 7 | Verificar el nombre del archivo descargado | El archivo se descarga con el nombre movimientos_0007654321_01092026_30092026.pdf [SUPUESTO: la HU no define el formato de las fechas ni el identificador de cuenta en el nombre; se asume DDMMAAAA y el número de cuenta] |
| 8 | Abrir el archivo descargado | El archivo contiene las columnas fecha, descripción, importe y saldo, con los importes en USD |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y del archivo movimientos_0007654321_01092026_30092026.pdf abierto |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-004 — Verificar que se exporta un archivo PDF con los movimientos de una cuenta en ARS para un rango válido

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta un archivo PDF con los movimientos de una cuenta en ARS para un rango válido |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de la Cuenta en ARS 0001234567, con movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha y el selector de formato |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta "Cuenta en ARS 0001234567" queda seleccionada y sus importes se muestran en ARS |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "PDF" | El formato "PDF" queda seleccionado |
| 6 | Tocar "Exportar" | El sistema genera el archivo PDF con los movimientos del período 01/09/2026 a 30/09/2026 [SUPUESTO: no hay umbral definido para "rápidamente"; se usa el tiempo de espera estándar de la plataforma] |
| 7 | Verificar el nombre del archivo descargado | El archivo se descarga con el nombre movimientos_0001234567_01092026_30092026.pdf [SUPUESTO: la HU no define el formato de las fechas ni el identificador de cuenta en el nombre; se asume DDMMAAAA y el número de cuenta] |
| 8 | Abrir el archivo descargado | El archivo contiene las columnas fecha, descripción, importe y saldo, con los importes en ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y del archivo movimientos_0001234567_01092026_30092026.pdf abierto |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-005 — Verificar que se exporta un archivo XLSX con los movimientos de una cuenta en ARS para un rango válido

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta un archivo XLSX con los movimientos de una cuenta en ARS para un rango válido |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de la Cuenta en ARS 0001234567, con movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha y el selector de formato |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta "Cuenta en ARS 0001234567" queda seleccionada y sus importes se muestran en ARS |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "XLSX" | El formato "XLSX" queda seleccionado |
| 6 | Tocar "Exportar" | El sistema genera el archivo XLSX con los movimientos del período 01/09/2026 a 30/09/2026 [SUPUESTO: no hay umbral definido para "rápidamente"; se usa el tiempo de espera estándar de la plataforma] |
| 7 | Verificar el nombre del archivo descargado | El archivo se descarga con el nombre movimientos_0001234567_01092026_30092026.xlsx [SUPUESTO: la HU no define el formato de las fechas ni el identificador de cuenta en el nombre; se asume DDMMAAAA y el número de cuenta] |
| 8 | Abrir el archivo descargado | El archivo contiene las columnas fecha, descripción, importe y saldo, con los importes en ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y del archivo movimientos_0001234567_01092026_30092026.xlsx abierto |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-006 — Verificar que se exporta un archivo CSV con los movimientos de una cuenta en USD para un rango válido

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta un archivo CSV con los movimientos de una cuenta en USD para un rango válido |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de la Cuenta en USD 0007654321, con movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | `cuenta`: Cuenta en USD 0007654321 · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" con el selector de cuenta, los campos de fecha y el selector de formato |
| 2 | Seleccionar la cuenta "Cuenta en USD 0007654321" | La cuenta "Cuenta en USD 0007654321" queda seleccionada y sus importes se muestran en USD |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | El sistema genera el archivo CSV con los movimientos del período 01/09/2026 a 30/09/2026 [SUPUESTO: no hay umbral definido para "rápidamente"; se usa el tiempo de espera estándar de la plataforma] |
| 7 | Verificar el nombre del archivo descargado | El archivo se descarga con el nombre movimientos_0007654321_01092026_30092026.csv [SUPUESTO: la HU no define el formato de las fechas ni el identificador de cuenta en el nombre; se asume DDMMAAAA y el número de cuenta] |
| 8 | Abrir el archivo descargado | El archivo contiene las columnas fecha, descripción, importe y saldo, con los importes en USD |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" y del archivo movimientos_0007654321_01092026_30092026.csv abierto |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-007 — Verificar que no se exporta cuando no se selecciona ninguna cuenta

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta cuando no se selecciona ninguna cuenta |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de una cuenta en ARS 0001234567 con movimientos entre 01/09/2026 y 30/09/2026. Dato de prueba: cuenta '' (vacío). |
| **Datos de prueba** | `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: CSV · `cuenta`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Dejar el selector de cuenta vacío | El selector de cuenta no tiene ninguna cuenta seleccionada |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | No se genera ni se descarga ningún archivo y se muestra un mensaje de error que indica el campo inválido [SUPUESTO: la HU no define el comportamiento ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" con el mensaje mostrado y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «No se selecciona ninguna cuenta» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.cuenta.sin_cuenta)]` _Técnica: error-choice._ |

### CP-008 — Verificar que no se exporta cuando la fecha desde está vacía

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta cuando la fecha desde está vacía |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de una cuenta en ARS 0001234567 con movimientos entre 01/09/2026 y 30/09/2026. Dato de prueba: fecha desde '' (vacío). |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_hasta`: 30/09/2026 · `formato`: CSV · `fecha_desde`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta queda seleccionada |
| 3 | Dejar el campo fecha desde vacío | El campo "desde" no tiene valor |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | No se genera ni se descarga ningún archivo y se muestra un mensaje de error que indica el campo inválido [SUPUESTO: la HU no define el comportamiento ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" con el mensaje mostrado y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha desde sin completar» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_vacia)]` _Técnica: error-choice._ |

### CP-009 — Verificar que no se exporta cuando la fecha desde es posterior a hoy

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta cuando la fecha desde es posterior a hoy |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de una cuenta en ARS 0001234567 con movimientos entre 01/09/2026 y 30/09/2026. Dato de prueba: fecha desde 01/01/2030 (futura). |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_hasta`: 30/09/2026 · `formato`: CSV · `fecha_desde`: 01/01/2030 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde "01/01/2030" | El campo "desde" muestra 01/01/2030 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | No se genera ni se descarga ningún archivo y se muestra un mensaje de error que indica el campo inválido [SUPUESTO: la HU no define el comportamiento ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" con el mensaje mostrado y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha desde posterior a hoy» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_futura)]` _Técnica: error-choice._ |

### CP-010 — Verificar que no se exporta cuando la fecha hasta está vacía

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta cuando la fecha hasta está vacía |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de una cuenta en ARS 0001234567 con movimientos entre 01/09/2026 y 30/09/2026. Dato de prueba: fecha hasta '' (vacío). |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_desde`: 01/09/2026 · `formato`: CSV · `fecha_hasta`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Dejar el campo fecha hasta vacío | El campo "hasta" no tiene valor |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | No se genera ni se descarga ningún archivo y se muestra un mensaje de error que indica el campo inválido [SUPUESTO: la HU no define el comportamiento ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" con el mensaje mostrado y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha hasta sin completar» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_hasta.fecha_vacia)]` _Técnica: error-choice._ |

### CP-011 — Verificar que no se exporta cuando la fecha hasta es anterior a la fecha desde

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta cuando la fecha hasta es anterior a la fecha desde |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de una cuenta en ARS 0001234567 con movimientos entre 01/09/2026 y 30/09/2026. Dato de prueba: fecha hasta 15/08/2026 (anterior a desde). |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_desde`: 01/09/2026 · `formato`: CSV · `fecha_hasta`: 15/08/2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "15/08/2026" | El campo "hasta" muestra 15/08/2026 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | No se genera ni se descarga ningún archivo y se muestra un mensaje de error que indica el campo inválido [SUPUESTO: la HU no define el comportamiento ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" con el mensaje mostrado y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «Fecha hasta anterior a fecha desde» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_hasta.hasta_anterior_a_desde)]` _Técnica: error-choice._ |

### CP-012 — Verificar que no se exporta cuando no se selecciona formato

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se exporta cuando no se selecciona formato |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado en home banking, titular de una cuenta en ARS 0001234567 con movimientos entre 01/09/2026 y 30/09/2026. Dato de prueba: formato '' (vacío). |
| **Datos de prueba** | `cuenta`: Cuenta en ARS 0001234567 · `fecha_desde`: 01/09/2026 · `fecha_hasta`: 30/09/2026 · `formato`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Dejar el selector de formato sin seleccionar | El selector de formato no tiene ningún formato seleccionado |
| 6 | Tocar "Exportar" | No se genera ni se descarga ningún archivo y se muestra un mensaje de error que indica el campo inválido [SUPUESTO: la HU no define el comportamiento ni el texto del mensaje] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla "Movimientos" con el mensaje mostrado y verificación de que no se descargó ningún archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: «No se selecciona formato» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.formato.sin_formato)]` _Técnica: error-choice._ |

### CP-013 — Verificar que un usuario sin permiso no accede a los movimientos de una cuenta ajena

| Campo | Valor |
|---|---|
| **Título** | Verificar que un usuario sin permiso no accede a los movimientos de una cuenta ajena |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Usuario A autenticado, titular de la cuenta ARS 0001234567. Usuario B autenticado, no titular de esa cuenta, con otra cuenta propia. Se conoce el identificador de la cuenta de A. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Iniciar sesión como usuario B | Se muestra el home banking de B con solo sus cuentas |
| 2 | Ir a la sección "Movimientos" | El selector de cuenta lista únicamente las cuentas de B |
| 3 | Solicitar la exportación de la cuenta ARS 0001234567 (de A) modificando el identificador de cuenta en la solicitud de exportación | La solicitud es rechazada con respuesta 403 [SUPUESTO: solo el titular de la cuenta puede exportar; otro usuario autenticado recibe 403] |
| 4 | Verificar el resultado de la solicitud | No se descarga ningún archivo y no se exponen datos de la cuenta de A |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la respuesta 403 y del listado de cuentas de B |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Solo el titular de la cuenta; otro usuario autenticado recibe 403 y no ve datos ajenos. (ver roles.permissions)]` _Técnica: rule:roles.permissions._ |

### CP-014 — Verificar que la exportación de un rango sin datos informa que no hay movimientos y no genera archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que la exportación de un rango sin datos informa que no hay movimientos y no genera archivo |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Cliente autenticado, titular de la cuenta ARS 0001234567, sin movimientos entre 01/01/2020 y 31/01/2020. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde "01/01/2020" | El campo "desde" muestra 01/01/2020 |
| 4 | Ingresar la fecha hasta "31/01/2020" | El campo "hasta" muestra 31/01/2020 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" | Se muestra el mensaje "No hay movimientos para el período" y no se genera ni se descarga ningún archivo [SUPUESTO: texto del mensaje y comportamiento sin datos no definidos por la HU] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado y de la carpeta de descargas sin archivo nuevo |
| **Estado** | Pendiente |
| **Notas** | Volumen máximo exportable asumido en 10.000 filas (ver export.volume); no cubierto por este caso. `[SUPUESTO: Sin datos: mensaje 'No hay movimientos para el período' y no se genera archivo; máximo 10.000 filas. (ver export.volume)]` _Técnica: rule:export.volume._ |

### CP-015 — Verificar que un doble submit de "Exportar" no genera exportaciones duplicadas

| Campo | Valor |
|---|---|
| **Título** | Verificar que un doble submit de "Exportar" no genera exportaciones duplicadas |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | Cliente autenticado, titular de la cuenta ARS 0001234567 con movimientos entre 01/09/2026 y 30/09/2026. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta "Cuenta en ARS 0001234567" | La cuenta queda seleccionada |
| 3 | Ingresar la fecha desde "01/09/2026" | El campo "desde" muestra 01/09/2026 |
| 4 | Ingresar la fecha hasta "30/09/2026" | El campo "hasta" muestra 30/09/2026 |
| 5 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 6 | Tocar "Exportar" dos veces seguidas en menos de un segundo | Se registra una sola operación de exportación [SUPUESTO: la operación es idempotente; el segundo submit no genera una segunda exportación] |
| 7 | Verificar los archivos descargados | Se descargó un único archivo movimientos_0001234567_01092026_30092026.csv [SUPUESTO: formato del nombre no definido por la HU] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la carpeta de descargas con un único archivo |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: La operación es idempotente: el segundo submit no genera un segundo movimiento. (ver money.idempotency)]` _Técnica: rule:money.idempotency._ |

### CP-016 — Verificar que la exportación de un rango con movimientos incluye fecha, descripción, importe y saldo

| Campo | Valor |
|---|---|
| **Título** | Verificar que la exportación de un rango con movimientos incluye fecha, descripción, importe y saldo |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2, CA-4 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Servicio disponible. Cliente autenticado, titular de una cuenta con Rango con 12 movimientos. |
| **Datos de prueba** | `movimientos_periodo`: Rango con 12 movimientos · `disponibilidad_servicio`: Servicio disponible |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta y el rango con 12 movimientos | La cuenta y el rango quedan seleccionados |
| 3 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 4 | Tocar "Exportar" | Se descarga el archivo [SUPUESTO: sin umbral definido para "rápidamente"; se usa el tiempo de espera estándar de la plataforma] |
| 5 | Abrir el archivo descargado | El archivo contiene 12 filas de movimientos, cada una con fecha, descripción, importe y saldo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del archivo abierto con las 12 filas |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: ac-happy-path._ |

### CP-017 — Verificar que se muestra un mensaje cuando el rango elegido no tiene movimientos

| Campo | Valor |
|---|---|
| **Título** | Verificar que se muestra un mensaje cuando el rango elegido no tiene movimientos |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2, CA-4 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Servicio disponible. Cliente autenticado, titular de una cuenta con Rango sin movimientos. |
| **Datos de prueba** | `movimientos_periodo`: Rango sin movimientos · `disponibilidad_servicio`: Servicio disponible |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta y un rango sin movimientos | La cuenta y el rango quedan seleccionados |
| 3 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 4 | Tocar "Exportar" | El sistema muestra un mensaje indicando que el rango no tiene movimientos [SUPUESTO: la HU solo dice "un mensaje adecuado" sin texto ni criterio verificable] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: pairwise._ |

### CP-018 — Verificar que se informa un error cuando falla la generación del archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que se informa un error cuando falla la generación del archivo |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | Cliente autenticado, titular de una cuenta con un rango con 12 movimientos. Servicio de generación caído (simulado, error del servidor o timeout). |
| **Datos de prueba** | `movimientos_periodo`: Rango con 12 movimientos · `disponibilidad_servicio`: Servicio de generación caído |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a la sección "Movimientos" | Se muestra la pantalla "Movimientos" |
| 2 | Seleccionar la cuenta y el rango con 12 movimientos | La cuenta y el rango quedan seleccionados |
| 3 | Seleccionar el formato "CSV" | El formato "CSV" queda seleccionado |
| 4 | Tocar "Exportar" | No se descarga ningún archivo y se muestra un mensaje de error que indica que la exportación falló [SUPUESTO: la HU no define el comportamiento ni el texto del mensaje ante falla del servicio] |
| 5 | Verificar el estado de la pantalla | La pantalla "Movimientos" mantiene la cuenta, las fechas y el formato elegidos [SUPUESTO] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error |
| **Estado** | Pendiente |
| **Notas** |  `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.disponibilidad_servicio.falla_generacion)]` _Técnica: error-choice._ |

### CP-019 — Verificar que el flujo de exportación se completa en los navegadores soportados

| Campo | Valor |
|---|---|
| **Título** | Verificar que el flujo de exportación se completa en los navegadores soportados |
| **Módulo** | Movimientos |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Cliente autenticado con una cuenta con movimientos entre 01/09/2026 y 30/09/2026. Navegadores: Chrome, Firefox y Safari desktop y Chrome móvil. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el home banking en Chrome desktop e ir a "Movimientos" | Se muestra la pantalla "Movimientos" en español |
| 2 | Exportar la cuenta con el rango 01/09/2026 a 30/09/2026 en formato "CSV" | Se descarga un archivo con nombre movimientos_<cuenta>_<desde>_<hasta>.csv [SUPUESTO: navegadores soportados no definidos por la HU] |
| 3 | Repetir el paso anterior en Firefox desktop | Se descarga el archivo con el mismo resultado |
| 4 | Repetir el paso anterior en Safari desktop | Se descarga el archivo con el mismo resultado |
| 5 | Repetir el paso anterior en Chrome móvil | Se descarga el archivo con el mismo resultado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas del archivo descargado en cada navegador |
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
| CP-013 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-014 | Alta | Medio | Alta | Prob. Alta (tipo Borde) × Impacto Medio (tipo Borde en funcionalidad crítica) → Alta |
| CP-015 | Media | Alto | Alta | Prob. Media (tipo Excepción) × Impacto Alto (regla de G. Concurrencia) → Alta |
| CP-016 | Baja | Alto | Alta | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media; humo → Alta |
| CP-017 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-018 | Alta | Medio | Alta | Prob. Alta (tipo Excepción; depende de un servicio externo («timeout»)) × Impacto Medio (tipo Excepción en funcionalidad crítica) → Alta |
| CP-019 | Media | Medio | Media | Prob. Media (tipo No funcional) × Impacto Medio (tipo No funcional en funcionalidad crítica) → Media |

**Orden de ejecución sugerido:** CP-001 → CP-016 → CP-014 → CP-015 → CP-018 → CP-002 → CP-003 → CP-004 → CP-005 → CP-006 → CP-007 → CP-008 → CP-009 → CP-010 → CP-011 → CP-012 → CP-013 → CP-017 → CP-019

**Subset de humo:** CP-001, CP-016

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar". | CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008, CP-009, CP-010, CP-011, CP-012, CP-013, CP-014, CP-015 | ✓ Cubierta |
| CA-2 | El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo. | CP-016, CP-017, CP-018 | ✓ Cubierta |
| CA-3 | El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`. | CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008, CP-009, CP-010, CP-011, CP-012 | ✓ Cubierta |
| CA-4 | Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado. | CP-016, CP-017, CP-019 | ✓ Cubierta |

**Cobertura de CAs: 4/4 (100.0%).**
Cobertura 2-wise de particiones válidas: 36/36 pares (100.0%).
Cobertura de valores límite: 0/0 (100.0%) — ningún parámetro tiene límites definidos aún (ver preguntas sobre límites).

## 6. Supuestos asumidos

1. `[SUPUESTO: «No se selecciona ninguna cuenta» se considera inválido aunque la HU no lo dice]` — en CP-007.
2. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.cuenta.sin_cuenta)]` — en CP-007.
3. `[SUPUESTO: «Fecha desde sin completar» se considera inválido aunque la HU no lo dice]` — en CP-008.
4. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_vacia)]` — en CP-008.
5. `[SUPUESTO: «Fecha desde posterior a hoy» se considera inválido aunque la HU no lo dice]` — en CP-009.
6. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_desde.fecha_futura)]` — en CP-009.
7. `[SUPUESTO: «Fecha hasta sin completar» se considera inválido aunque la HU no lo dice]` — en CP-010.
8. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_hasta.fecha_vacia)]` — en CP-010.
9. `[SUPUESTO: «Fecha hasta anterior a fecha desde» se considera inválido aunque la HU no lo dice]` — en CP-011.
10. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.fecha_hasta.hasta_anterior_a_desde)]` — en CP-011.
11. `[SUPUESTO: «No se selecciona formato» se considera inválido aunque la HU no lo dice]` — en CP-012.
12. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.formato.sin_formato)]` — en CP-012.
13. `[SUPUESTO: Solo el titular de la cuenta; otro usuario autenticado recibe 403 y no ve datos ajenos. (ver P-4)]` — en CP-013.
14. `[SUPUESTO: Sin datos: mensaje 'No hay movimientos para el período' y no se genera archivo; máximo 10.000 filas. (ver P-5)]` — en CP-014.
15. `[SUPUESTO: La operación es idempotente: el segundo submit no genera un segundo movimiento. (ver P-3)]` — en CP-015.
16. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.disponibilidad_servicio.falla_generacion)]` — en CP-018.
17. `[SUPUESTO: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil. (ver context.platform_i18n)]` — en CP-019.
18. `[SUPUESTO: Navegable por teclado con foco visible.]` — laguna menor `context.a11y` no preguntada (tope de preguntas).

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
| O2 — ≥1 negativo/borde cada 2 positivos | No | ✓ 8 negativos/bordes vs 8 funcionales (ratio 1.00) |
| O3 — Subset de humo marcado | No | ✓ CP-001, CP-016 |
| O4 — Sin casos duplicados (mismo título) | No | ✓ |
| O5 — Dependencias entre casos apuntan a casos existentes (referenciar por frame_id F-…) | No | ✓ |

**Gate: APROBADO.**

## 8. Trazabilidad técnica

**Lint de la HU** (Requirements Smells — Femmer et al. 2017; Quality User Story — Lucassen et al. 2016):

- `smell.subjective_language` en CA-4: «adecuado» — Lenguaje subjetivo: su verificación depende de la opinión de quien prueba.
- `smell.ambiguous_adverbs_adjectives` en CA-2: «rápidamente» — Adverbios/adjetivos ambiguos: no fijan un umbral verificable.

**Técnicas de diseño por caso:** ac-happy-path: 2 · error-choice: 7 · pairwise: 6 · rule: 4.

- `ac-happy-path` / `each-choice` / `pairwise`: Category-Partition (Ostrand & Balcer 1988) + cobertura 2-wise (Kuhn et al. 2004).
- `error-choice`: elecciones `[error]` de TSL, un caso cada una sin combinar.
- `bva`: análisis de valores límite (mín-1, mín, mín+1, máx-1, máx, máx+1).
- `rule:<id>`: heurística de `rules/gaps.yaml`.
