# Suite de pruebas — HU-202: Exportación de movimientos de cuenta

Fecha de generación: 2026-10-09 · Modo: completo (F3) · Casos: 32

## 1. Resumen del análisis

**Texto original (referencia textual):** "Como cliente de home banking, quiero exportar los movimientos de mi cuenta en un rango de fechas, para conciliarlos con mi sistema contable."

| Elemento | Detalle |
|---|---|
| **Rol** | Cliente de home banking (autenticado, titular de una o más cuentas) |
| **Funcionalidad** | Exportar los movimientos de una cuenta propia, en un rango de fechas y en formato CSV, XLSX o PDF, desde la pantalla "Movimientos" |
| **Objetivo de negocio** | Conciliar los movimientos con el sistema contable del cliente |

**Criterios de aceptación (tal como están escritos):**

- **CA-1**: Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar".
- **CA-2**: El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo.
- **CA-3**: El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`.
- **CA-4**: Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado.
- **Nota del equipo (NT-1)**: los importes se muestran en la moneda de la cuenta (ARS o USD).

**Entidades y datos:** Cliente; Cuenta (número, moneda ARS/USD, titular); Movimiento (fecha, descripción, importe, saldo); entradas del usuario: cuenta, fecha desde, fecha hasta, formato (CSV/XLSX/PDF); salida: archivo descargable con nombre derivado.

**Gaps detectados (F2):** ninguno es BLOQUEANTE (el happy path es diseñable); todos son IMPORTANTES, por lo que se generan casos con `[SUPUESTO]` y pregunta al PO.

| Gap | Clase | CA / categoría |
|---|---|---|
| "rápidamente" no es verificable | IMPORTANTE | CA-2 / A |
| Rango máximo / volumen máximo no definido | IMPORTANTE | B |
| Inclusividad de extremos, desde > hasta, fechas futuras, formato de fecha en el nombre | IMPORTANTE | CA-1, CA-3 / B |
| Qué es `<cuenta>` en el nombre (número completo, enmascarado, alias) | IMPORTANTE | CA-3 / B, F |
| Estructura del contenido (formato de fecha/importe, signo, orden, saldo, indicación de moneda, encoding CSV) | IMPORTANTE | CA-2, NT-1 / B |
| "mensaje adecuado": texto y si se genera o no un archivo vacío | IMPORTANTE | CA-4 / A |
| Comportamiento ante fallo de generación / red | IMPORTANTE | C |
| Autorización, sesión, doble pedido, neutralización de contenido (inyección de fórmulas) | IMPORTANTE | D, F, G |
| Cuenta cerrada/bloqueada; nombre de archivo repetido; navegadores soportados | MENOR | E, J |

## 2. Preguntas para el PO

**P-1. [A. Criterios de aceptación] CA-2 dice "rápidamente": ¿el umbral es 5 s o 10 s para un export típico (hasta 1.000 movimientos)?**
- **Por qué importa**: sin umbral no se puede dar un resultado pasa/falla en performance ni decidir si hace falta generación asíncrona (por ejemplo, "te avisamos cuando esté listo").
- **Default propuesto**: máximo 5 s desde "Exportar" hasta el inicio de la descarga, para hasta 1.000 movimientos. (S-1)

**P-2. [B. Datos y validaciones] ¿Cuál es el rango máximo permitido entre desde y hasta: 365 días o sin límite? ¿Hay tope de movimientos por archivo?**
- **Por qué importa**: define los casos de borde (máx, máx+1) y el comportamiento ante rangos enormes (timeout, archivos gigantes).
- **Default propuesto**: máximo 365 días corridos (ambos extremos incluidos); si se excede, se bloquea la exportación con un mensaje de error y no se genera archivo. Sin tope adicional de movimientos. (S-2)

**P-3. [B. Datos y validaciones] Fechas: ¿"desde" y "hasta" son inclusivas? ¿Se permite desde > hasta o fechas posteriores a hoy? ¿En qué formato van en el nombre del archivo (AAAA-MM-DD, AAAAMMDD, DD-MM-AAAA)?**
- **Por qué importa**: cambia qué movimientos entran (conciliación incorrecta) y los resultados esperados de los casos de borde y de nombre de archivo (CA-3).
- **Default propuesto**: ambos extremos inclusivos (día calendario completo); desde > hasta y fechas posteriores a hoy se bloquean con mensaje de validación; hoy sí se permite; formato en el nombre AAAA-MM-DD. (S-3, S-4, S-5, S-6)

**P-4. [B. Datos y validaciones / F. Seguridad] En el nombre del archivo, ¿`<cuenta>` es el número de cuenta completo (10 dígitos) o una versión enmascarada/alias?**
- **Por qué importa**: el nombre viaja en descargas, historial del navegador y mails del cliente; si debe enmascararse, el resultado esperado de CA-3 cambia.
- **Default propuesto**: número de cuenta de 10 dígitos sin separadores, tal como se muestra en "Movimientos". (S-6)

**P-5. [B. Datos y validaciones] Contenido de los archivos: ¿columnas exactas Fecha, Descripción, Importe, Saldo? ¿Formato de fecha e importes (punto/coma decimal, miles), signo de débitos, orden de filas, saldo posterior al movimiento, cómo se indica ARS/USD, codificación y delimitador del CSV?**
- **Por qué importa**: sin estas definiciones no hay resultado esperado assertable para CA-2 ni para la nota de moneda, y el cliente no puede importar el archivo a su sistema contable de forma confiable.
- **Default propuesto**: 4 columnas exactas (Fecha, Descripción, Importe, Saldo); CSV UTF-8 con encabezado, delimitador coma, fecha AAAA-MM-DD, importes con punto decimal, 2 decimales y sin separador de miles, débitos en negativo; XLSX con celdas de tipo fecha y numérico; PDF con tabla y fecha DD/MM/AAAA; orden cronológico ascendente; saldo = saldo de la cuenta posterior a cada movimiento (no recalculado desde el inicio del rango); sin conversión de moneda y con el código ARS/USD visible en XLSX y PDF. (S-7, S-8, S-9)

**P-6. [A. Criterios de aceptación] CA-4: ¿cuál es el texto exacto del mensaje y se descarga o no un archivo vacío cuando no hay movimientos?**
- **Por qué importa**: "mensaje adecuado" no es verificable y generar un archivo vacío cambia el resultado esperado y el riesgo de confusión en la conciliación.
- **Default propuesto**: mensaje informativo (no de error técnico) "No hay movimientos en el período seleccionado" y NO se descarga ningún archivo. (S-10)

**P-7. [C. Comportamiento ante errores] Si falla la generación del archivo (error del servicio, timeout, red caída), ¿qué ve el cliente y puede reintentar sin volver a cargar los datos?**
- **Por qué importa**: sin definición, los casos de excepción no tienen resultado esperado y puede quedar un archivo parcial o corrupto que el cliente concilie sin darse cuenta.
- **Default propuesto**: mensaje genérico "No pudimos generar el archivo. Intentá nuevamente." sin detalles técnicos, selección de cuenta/fechas/formato conservada, sin archivo parcial y con reintento posible. (S-12)

**P-8. [D. Permisos, F. Seguridad, G. Concurrencia] ¿Se confirma que solo se pueden exportar cuentas propias, que sin sesión no se descarga nada, que un doble clic en "Exportar" genera una sola descarga, y que el texto de los movimientos que podría empezar con `=`, `+`, `-` o `@` se neutraliza en CSV/XLSX (inyección de fórmulas)?**
- **Por qué importa**: es una función de dinero y datos personales (seguridad obligatoria); las descripciones pueden contener texto controlado por terceros (conceptos de transferencias recibidas) que Excel interpretaría como fórmula.
- **Default propuesto**: solo cuentas propias (pedido sobre cuenta ajena rechazado sin devolver datos); sin sesión, redirección al login; doble clic = una sola descarga; las descripciones que empiezan con `=`, `+`, `-` o `@` se escriben como texto literal (prefijadas con apóstrofo). (S-13, S-14, S-15, S-16)

## 3. Casos de prueba

### Datos base de la suite (referenciados por los casos)

Usuario principal: **qa.cliente01@flockbank.test** (cliente QA-01). Usuario secundario: **qa.cliente02@flockbank.test** (titular de la cuenta ajena H). Fecha de ejecución = "hoy" (a la fecha de generación: 2026-10-09).

| ID | Cuenta | Moneda | Titular | Movimientos (fecha · descripción · importe · saldo posterior) |
|---|---|---|---|---|
| **A** | 0012345678 | ARS | QA-01 | 2025-11-20 · Depósito en efectivo · +100000.00 · 100000.00 / 2026-09-01 · Acreditación haberes · +850000.00 · 950000.00 / 2026-09-05 · Débito automático Edenor · -45230.50 · 904769.50 / 2026-09-15 · Transferencia recibida Pérez Ana · +120000.00 · 1024769.50 / 2026-09-30 23:59:59 · Compra débito Café Ñandú · -3150.75 · 1021618.75. Sin otros movimientos (en particular, ninguno entre 2026-10-01 y 2026-10-05) |
| **B** | 0087654321 | USD | QA-01 | 2026-09-10 · Compra de divisas · +500.00 · 1500.00 / 2026-09-20 · Pago servicio exterior · -49.99 · 1450.01 (saldo previo 1000.00) |
| **C** | 0011112222 | ARS | QA-01 | Sin movimientos entre 2026-01-01 y 2026-01-31; tiene un movimiento el 2026-02-10 (Depósito en efectivo · +5000.00 · 5000.00) |
| **D** | 0013572468 | ARS | QA-01 | 2026-09-12 · `Transf. a Muñoz & Hijos, "Pago #1" ñandú 🎁` · -2500.00 · 7500.00 (saldo previo 10000.00) |
| **E** | 0024681357 | ARS | QA-01 | 2026-09-08 · `=1+1` · +100.00 · 1100.00 / 2026-09-09 · `@SUM(1+1)` · +200.00 · 1300.00 (saldo previo 1000.00) |
| **F** | 0036925814 | ARS | QA-01 | 2026-09-03 · Ajuste mínimo · +0.01 · 0.01 / 2026-09-04 · Acreditación extraordinaria · +9999999999.99 · 10000000000.00 (saldo previo 0.00) |
| **G** | 0099998888 | ARS | QA-01 | 1.000 movimientos "Mov QA 0001" a "Mov QA 1000", cronológicos entre 2026-09-01 y 2026-09-30, importe +1.00 cada uno, saldo posterior = N × 1.00 (saldo previo 0.00). Se crean con script/seed de QA |
| **H** | 0098765432 | ARS | QA-02 | Cuenta ajena a QA-01, con ≥1 movimiento (2026-09-02 · Depósito en efectivo · +1000.00 · 1000.00) |

---

### CP-001 — Exportar movimientos en CSV de una cuenta ARS y descargar con el nombre esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar en CSV la cuenta 0012345678 del 2026-09-01 al 2026-09-30 descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A cargada según Datos base; carpeta de descargas del navegador vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-01; hasta 2026-09-30; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar a "Movimientos" | Se muestra la pantalla Movimientos con los controles de cuenta, desde, hasta, formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta 0012345678 | La cuenta 0012345678 queda seleccionada |
| 3 | Ingresar desde 2026-09-01 | El campo "desde" muestra 2026-09-01 |
| 4 | Ingresar hasta 2026-09-30 | El campo "hasta" muestra 2026-09-30 |
| 5 | Abrir el selector de formato | Se ofrecen exactamente las opciones CSV, XLSX y PDF |
| 6 | Seleccionar CSV | CSV queda seleccionado |
| 7 | Tocar "Exportar" | El navegador inicia la descarga de un archivo |
| 8 | Verificar el nombre del archivo en la carpeta de descargas | El archivo se llama exactamente `movimientos_0012345678_2026-09-01_2026-09-30.csv` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del paso 5 (opciones de formato) y del paso 8 (nombre del archivo) |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: fechas en el nombre con formato AAAA-MM-DD y `<cuenta>` = número de 10 dígitos (S-6)]. Subset de humo. |

---

### CP-002 — Contenido del CSV: columnas, filas, importes y saldos de la cuenta ARS

| Campo | Valor |
|---|---|
| **Título** | Verificar que el CSV exportado contiene los 4 movimientos de septiembre 2026 con fecha, descripción, importe y saldo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | CP-001 ejecutado con éxito (archivo `movimientos_0012345678_2026-09-01_2026-09-30.csv` descargado) |
| **Datos de prueba** | Archivo de CP-001; abrir con un editor de texto (por ejemplo Notepad++) en modo UTF-8 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el CSV en un editor de texto | El archivo abre sin error |
| 2 | Verificar la primera línea | Es un encabezado con las columnas `Fecha,Descripción,Importe,Saldo` (4 columnas, en ese orden) |
| 3 | Contar las líneas de datos | Hay exactamente 4 líneas de datos |
| 4 | Verificar la línea 1 de datos | `2026-09-01,Acreditación haberes,850000.00,950000.00` |
| 5 | Verificar la línea 2 de datos | `2026-09-05,Débito automático Edenor,-45230.50,904769.50` |
| 6 | Verificar la línea 3 de datos | `2026-09-15,Transferencia recibida Pérez Ana,120000.00,1024769.50` |
| 7 | Verificar la línea 4 de datos | `2026-09-30,Compra débito Café Ñandú,-3150.75,1021618.75` |
| 8 | Verificar que no existen movimientos de otros meses | No aparece el movimiento del 2025-11-20 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del archivo abierto en el editor; copia del CSV |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: 4 columnas exactas, delimitador coma, UTF-8, fecha AAAA-MM-DD, punto decimal con 2 decimales sin miles, débitos negativos, orden cronológico ascendente, saldo posterior al movimiento (S-7, S-8)]. El movimiento del 2026-09-30 23:59:59 con hasta=2026-09-30 valida además que el extremo "hasta" es inclusivo [SUPUESTO: S-3]. Subset de humo. |

---

### CP-003 — Exportar en XLSX: nombre, columnas y tipos de celda

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar en XLSX descarga `movimientos_0012345678_2026-09-01_2026-09-30.xlsx` con celdas de fecha e importes numéricos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; Microsoft Excel instalado (o LibreOffice Calc); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-01; hasta 2026-09-30; formato XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 y hasta 2026-09-30 | Ambos campos muestran los valores ingresados |
| 3 | Seleccionar el formato XLSX | XLSX queda seleccionado |
| 4 | Tocar "Exportar" | Se inicia la descarga de un archivo |
| 5 | Verificar el nombre del archivo | Es exactamente `movimientos_0012345678_2026-09-01_2026-09-30.xlsx` |
| 6 | Abrir el archivo en Excel | Abre sin mensajes de error ni de reparación |
| 7 | Verificar la fila de encabezado | Contiene `Fecha`, `Descripción`, `Importe`, `Saldo` en ese orden |
| 8 | Verificar las filas de datos | Hay 4 filas con los mismos valores de fecha, descripción, importe y saldo que los movimientos de septiembre de la cuenta A (ver CP-002) |
| 9 | Seleccionar la celda de importe 850000.00 y mirar su tipo | La celda es de tipo numérico (alineada a la derecha, suma con la fórmula `=SUM`), no texto |
| 10 | Seleccionar la celda de fecha de la primera fila | La celda es de tipo fecha (se puede reformatear a DD/MM/AAAA), no texto |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del archivo en Excel; copia del XLSX |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: XLSX con celdas de tipo fecha y numérico, mismas 4 columnas que el CSV (S-7)]. Importante para la conciliación contable. |

---

### CP-004 — Exportar en PDF: nombre, columnas y contenido

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar en PDF descarga `movimientos_0012345678_2026-09-01_2026-09-30.pdf` con los 4 movimientos de septiembre |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; visor de PDF disponible; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-01; hasta 2026-09-30; formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 y hasta 2026-09-30 | Ambos campos muestran los valores ingresados |
| 3 | Seleccionar el formato PDF | PDF queda seleccionado |
| 4 | Tocar "Exportar" | Se inicia la descarga de un archivo |
| 5 | Verificar el nombre del archivo | Es exactamente `movimientos_0012345678_2026-09-01_2026-09-30.pdf` |
| 6 | Abrir el archivo en el visor de PDF | Abre sin error |
| 7 | Verificar las columnas de la tabla | Se muestran los encabezados Fecha, Descripción, Importe y Saldo |
| 8 | Verificar las filas | Hay 4 filas: 01/09/2026 Acreditación haberes 850000.00 950000.00; 05/09/2026 Débito automático Edenor -45230.50 904769.50; 15/09/2026 Transferencia recibida Pérez Ana 120000.00 1024769.50; 30/09/2026 Compra débito Café Ñandú -3150.75 1021618.75 |
| 9 | Verificar que el texto es legible (ñ, acentos, importes completos) | No hay caracteres truncados ni reemplazados por símbolos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la página del PDF; copia del PDF |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: tabla con los 4 encabezados, fecha DD/MM/AAAA; el separador decimal y de miles exacto en el PDF no está definido (S-7), validar que el valor numérico coincida con el del CSV sin importar el separador]. Subset de humo. |

---

### CP-005 — Exportar una cuenta USD: importes en la moneda de la cuenta, sin conversión

| Campo | Valor |
|---|---|
| **Título** | Verificar que el export de la cuenta USD 0087654321 muestra los importes en USD sin conversión a ARS |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2, CA-3, NT-1 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta B (USD) según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0087654321; desde 2026-09-01; hasta 2026-09-30; formatos CSV y PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0087654321 | Cuenta USD seleccionada |
| 2 | Ingresar desde 2026-09-01 y hasta 2026-09-30 | Campos con los valores ingresados |
| 3 | Seleccionar CSV y tocar "Exportar" | Se descarga `movimientos_0087654321_2026-09-01_2026-09-30.csv` |
| 4 | Abrir el CSV en un editor de texto | Hay 2 líneas de datos: `2026-09-10,Compra de divisas,500.00,1500.00` y `2026-09-20,Pago servicio exterior,-49.99,1450.01` |
| 5 | Seleccionar PDF y tocar "Exportar" | Se descarga `movimientos_0087654321_2026-09-01_2026-09-30.pdf` |
| 6 | Abrir el PDF | Muestra los mismos 2 movimientos con importes 500.00 y -49.99 y saldos 1500.00 y 1450.01 |
| 7 | Buscar el código de moneda en el PDF | Se ve el código USD en el documento y no aparece ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Copia de ambos archivos; screenshot del PDF |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: sin conversión de moneda; el PDF (y el XLSX) muestran el código de moneda de la cuenta; el CSV no incluye la moneda y se identifica por la cuenta del nombre (S-9)]. |

---

### CP-006 — Consistencia de datos entre los tres formatos

| Campo | Valor |
|---|---|
| **Título** | Verificar que CSV, XLSX y PDF de la misma exportación contienen los mismos movimientos, importes y saldos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | CP-002, CP-003 y CP-004 ejecutados con éxito (los tres archivos de la cuenta 0012345678, 2026-09-01 a 2026-09-30, disponibles) |
| **Datos de prueba** | Los tres archivos descargados en CP-002, CP-003 y CP-004 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Anotar la cantidad de filas de datos de cada archivo | Los tres tienen 4 filas |
| 2 | Comparar la suma de la columna Importe de cada archivo | La suma es 921618.75 en los tres (850000.00 - 45230.50 + 120000.00 - 3150.75 = 921618.75) |
| 3 | Comparar el saldo de la última fila de cada archivo | Es 1021618.75 en los tres |
| 4 | Comparar el orden de las filas | Las fechas están en el mismo orden en los tres: 09-01, 09-05, 09-15, 09-30 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de los tres archivos lado a lado |
| **Estado** | Pendiente |
| **Notas** | Detecta que un formato use otra fuente de datos o lógica de redondeo. |

---

### CP-007 — Rango sin movimientos en CSV: mensaje y sin archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango sin movimientos muestra un mensaje informativo y no descarga archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta C (0011112222) según Datos base, sin movimientos en enero 2026; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0011112222; desde 2026-01-01; hasta 2026-01-31; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0011112222 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-01-01 y hasta 2026-01-31 | Campos con los valores ingresados |
| 3 | Seleccionar CSV | CSV seleccionado |
| 4 | Tocar "Exportar" | Se muestra un mensaje que indica que no hay movimientos en el período, por ejemplo "No hay movimientos en el período seleccionado" |
| 5 | Verificar la carpeta de descargas | No se descargó ningún archivo (ni vacío ni con solo encabezado) |
| 6 | Verificar el tipo de mensaje | Es un mensaje informativo, no un error técnico ni un código de error |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; captura de la carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: texto "No hay movimientos en el período seleccionado" y sin archivo (S-10); la HU solo dice "mensaje adecuado"]. Subset de humo. |

---

### CP-008 — Rango sin movimientos en PDF en una cuenta que sí tiene movimientos en otros períodos

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango vacío en PDF muestra el mismo mensaje y no genera un PDF vacío |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base (sin movimientos entre 2026-10-01 y 2026-10-05); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-10-01; hasta 2026-10-05; formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-10-01 y hasta 2026-10-05 | Campos con los valores ingresados |
| 3 | Seleccionar PDF y tocar "Exportar" | Se muestra el mismo mensaje informativo de CP-007 |
| 4 | Verificar la carpeta de descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje y carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: S-10]. Un PDF puede generarse con una tabla vacía aunque el CSV no. |

---

### CP-009 — Rango de un solo día (desde = hasta) con un movimiento

| Campo | Valor |
|---|---|
| **Título** | Verificar que desde = hasta = 2026-09-15 exporta solo el movimiento de ese día |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-15; hasta 2026-09-15; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-15 y hasta 2026-09-15 | Campos con la misma fecha |
| 3 | Seleccionar CSV y tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-15_2026-09-15.csv` |
| 4 | Abrir el CSV | Contiene el encabezado y exactamente 1 línea de datos: `2026-09-15,Transferencia recibida Pérez Ana,120000.00,1024769.50` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Copia del CSV y screenshot del nombre del archivo |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: desde = hasta es un rango válido de 1 día e inclusivo (S-3)]. |

---

### CP-010 — Extremos excluidos (mín+1 / máx-1) y saldo real en rango parcial

| Campo | Valor |
|---|---|
| **Título** | Verificar que el rango 2026-09-02 a 2026-09-29 excluye los movimientos del 09-01 y 09-30 y conserva el saldo real de la cuenta |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-02; hasta 2026-09-29; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-02 y hasta 2026-09-29 | Campos con los valores ingresados |
| 3 | Seleccionar CSV y tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-02_2026-09-29.csv` |
| 4 | Abrir el CSV y contar las líneas de datos | Hay exactamente 2 líneas de datos |
| 5 | Verificar la línea 1 de datos | `2026-09-05,Débito automático Edenor,-45230.50,904769.50` |
| 6 | Verificar la línea 2 de datos | `2026-09-15,Transferencia recibida Pérez Ana,120000.00,1024769.50` |
| 7 | Verificar que no aparecen los movimientos del 2026-09-01 ni del 2026-09-30 | Ninguna fila tiene esas fechas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Copia del CSV |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: el saldo es el saldo de la cuenta posterior al movimiento (904769.50), no un saldo recalculado desde 0 al inicio del rango (S-8)]. Un saldo recalculado rompe la conciliación. |

---

### CP-011 — Rango máximo permitido (365 días)

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango de exactamente 365 días (2025-10-01 a 2026-09-30) se exporta correctamente |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2025-10-01; hasta 2026-09-30 (365 días con ambos extremos incluidos); formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2025-10-01 y hasta 2026-09-30 | Campos con los valores ingresados, sin mensaje de error |
| 3 | Seleccionar CSV y tocar "Exportar" | Se descarga `movimientos_0012345678_2025-10-01_2026-09-30.csv` |
| 4 | Abrir el CSV y contar las líneas de datos | Hay 5 líneas de datos (la del 2025-11-20 más las 4 de septiembre 2026) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Copia del CSV; screenshot sin mensaje de error |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: rango máximo 365 días con ambos extremos incluidos (S-2)]. |

---

### CP-012 — Rango superior al máximo (366 días) es rechazado

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango de 366 días (2025-09-30 a 2026-09-30) se bloquea con un mensaje y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2025-09-30; hasta 2026-09-30 (366 días); formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2025-09-30 y hasta 2026-09-30 | Campos con los valores ingresados |
| 3 | Seleccionar CSV y tocar "Exportar" | Se muestra un mensaje de validación que indica el rango máximo permitido (365 días) |
| 4 | Verificar la carpeta de descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: S-2, incluyendo el texto del mensaje]. Si el PO responde "sin límite", este caso pasa a ser exploratorio de rango grande (timeout/volumen). |

---

### CP-013 — Desde posterior a hasta es rechazado

| Campo | Valor |
|---|---|
| **Título** | Verificar que desde 2026-09-30 y hasta 2026-09-01 muestra un error de validación y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-30; hasta 2026-09-01; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-30 | Campo con 2026-09-30 |
| 3 | Ingresar hasta 2026-09-01 | Campo con 2026-09-01 |
| 4 | Seleccionar CSV y tocar "Exportar" | Se muestra un mensaje de validación que indica que la fecha desde no puede ser posterior a la fecha hasta |
| 5 | Verificar la carpeta de descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: S-4, texto del mensaje no definido por la HU]. |

---

### CP-014 — Hasta = hoy es permitido

| Campo | Valor |
|---|---|
| **Título** | Verificar que hasta = fecha de hoy se acepta y descarga un archivo con esa fecha en el nombre |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; carpeta de descargas vacía; conocer la fecha de hoy (HOY, por ejemplo 2026-10-09 si se ejecuta ese día) |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-01; hasta HOY (2026-10-09 si se ejecuta ese día); formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 | Campo con 2026-09-01 |
| 3 | Ingresar hasta HOY | Campo con la fecha de hoy, sin mensaje de error |
| 4 | Seleccionar CSV y tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-01_<HOY>.csv`, por ejemplo `movimientos_0012345678_2026-09-01_2026-10-09.csv` |
| 5 | Abrir el CSV y contar las líneas de datos | Hay 4 líneas de datos (movimientos de septiembre 2026 de la cuenta A) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del nombre del archivo; copia del CSV |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: hoy es una fecha válida para "hasta" (S-5)]. |

---

### CP-015 — Hasta posterior a hoy es rechazado

| Campo | Valor |
|---|---|
| **Título** | Verificar que hasta = mañana muestra un error de validación y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta A según Datos base; carpeta de descargas vacía; conocer la fecha de mañana (MAÑANA, por ejemplo 2026-10-10 si se ejecuta el 2026-10-09) |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-01; hasta MAÑANA (2026-10-10 si se ejecuta el 2026-10-09); formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 | Campo con 2026-09-01 |
| 3 | Ingresar hasta MAÑANA | Campo con esa fecha o el selector la rechaza |
| 4 | Seleccionar CSV y tocar "Exportar" | Se muestra un mensaje de validación que indica que la fecha hasta no puede ser futura |
| 5 | Verificar la carpeta de descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: S-5; si el selector de fechas impide elegir fechas futuras, registrar ese comportamiento como resultado válido del paso 3]. |

---

### CP-016 — Fechas desde/hasta vacías

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar con las fechas vacías muestra errores de campo obligatorio y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; en "Movimientos" con los campos desde y hasta vacíos; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde (vacío); hasta (vacío); formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Seleccionar el formato CSV | CSV seleccionado |
| 3 | Dejar desde y hasta vacíos y tocar "Exportar" | Se marcan ambos campos como obligatorios con un mensaje de validación |
| 4 | Verificar la carpeta de descargas | No se descargó ningún archivo |
| 5 | Completar solo desde con 2026-09-01 y tocar "Exportar" | Se marca hasta como obligatorio y no se descarga archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de los mensajes en pasos 3 y 5 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: fechas obligatorias sin valor por defecto (S-11)]. |

---

### CP-017 — Formato no seleccionado

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar sin elegir un formato muestra un error de campo obligatorio y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; en "Movimientos" sin formato elegido (pantalla recién cargada); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; desde 2026-09-01; hasta 2026-09-30; formato (sin seleccionar) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 y hasta 2026-09-30 | Campos con los valores ingresados |
| 3 | Tocar "Exportar" sin elegir formato | Se muestra un mensaje de validación que indica que hay que elegir un formato |
| 4 | Verificar la carpeta de descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: no hay formato preseleccionado (S-11)]. Si hubiera un formato por defecto, el caso no aplica. |

---

### CP-018 — Descripción con comas, comillas, ñ y emoji en CSV

| Campo | Valor |
|---|---|
| **Título** | Verificar que una descripción con coma, comillas dobles, ñ y emoji se exporta íntegra y el CSV mantiene 4 columnas |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta D (0013572468) según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0013572468; desde 2026-09-01; hasta 2026-09-30; formato CSV; descripción `Transf. a Muñoz & Hijos, "Pago #1" ñandú 🎁` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0013572468 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 y hasta 2026-09-30 | Campos con los valores ingresados |
| 3 | Seleccionar CSV y tocar "Exportar" | Se descarga `movimientos_0013572468_2026-09-01_2026-09-30.csv` |
| 4 | Abrir el CSV en un editor de texto en modo UTF-8 | La línea de datos muestra la descripción entre comillas con las comillas internas duplicadas: `2026-09-12,"Transf. a Muñoz & Hijos, ""Pago #1"" ñandú 🎁",-2500.00,7500.00` |
| 5 | Abrir el CSV con un parser CSV (por ejemplo Python `csv.reader`) | La fila de datos tiene exactamente 4 campos y el campo descripción es `Transf. a Muñoz & Hijos, "Pago #1" ñandú 🎁` |
| 6 | Verificar caracteres ñ y emoji | No aparecen caracteres corruptos (por ejemplo `Ã±`) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del editor y salida del parser |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: CSV en UTF-8 con escape estándar RFC 4180 (S-7)]. |

---

### CP-019 — Importes extremos (0.01 y 9999999999.99) sin pérdida de precisión

| Campo | Valor |
|---|---|
| **Título** | Verificar que los importes 0.01 y 9999999999.99 y el saldo 10000000000.00 se exportan exactos en CSV y XLSX |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta F (0036925814) según Datos base; Excel instalado; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0036925814; desde 2026-09-01; hasta 2026-09-30; formatos CSV y XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0036925814 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 y hasta 2026-09-30 | Campos con los valores ingresados |
| 3 | Seleccionar CSV y tocar "Exportar" | Se descarga `movimientos_0036925814_2026-09-01_2026-09-30.csv` |
| 4 | Abrir el CSV en un editor de texto | Línea 1: `2026-09-03,Ajuste mínimo,0.01,0.01`; línea 2: `2026-09-04,Acreditación extraordinaria,9999999999.99,10000000000.00` (sin notación científica) |
| 5 | Seleccionar XLSX y tocar "Exportar" | Se descarga `movimientos_0036925814_2026-09-01_2026-09-30.xlsx` |
| 6 | Abrir el XLSX en Excel y seleccionar la celda de importe 9999999999.99 | Se ve el valor 9999999999.99 con sus 2 decimales (no 1E+10 ni redondeado) |
| 7 | Seleccionar la celda de importe 0.01 | Se ve el valor 0.01 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del CSV y de las celdas en Excel |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: no hay tope de importe definido en la HU; el valor extremo es de prueba (S-7)]. Riesgo típico: coma flotante / notación científica. |

---

### CP-020 — Performance: 1.000 movimientos en CSV dentro del umbral

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar 1.000 movimientos en CSV inicia la descarga en 5 segundos o menos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta G (0099998888) con 1.000 movimientos según Datos base; cronómetro o pestaña Network de DevTools abierta |
| **Datos de prueba** | Cuenta 0099998888; desde 2026-09-01; hasta 2026-09-30; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0099998888 | Cuenta seleccionada |
| 2 | Ingresar desde 2026-09-01 y hasta 2026-09-30 y seleccionar CSV | Campos y formato completos |
| 3 | Iniciar el cronómetro y tocar "Exportar" | Empieza la generación |
| 4 | Detener el cronómetro cuando comienza la descarga | Transcurrieron 5 s o menos |
| 5 | Abrir el CSV y contar las líneas de datos | Hay exactamente 1.000 líneas de datos; la primera es `Mov QA 0001` y la última `Mov QA 1000` con saldo 1000.00 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pestaña Network con el tiempo del request; copia del CSV |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: umbral de 5 s para hasta 1.000 movimientos (S-1)]; la HU solo dice "rápidamente". Repetir 3 veces y tomar el peor tiempo. |

---

### CP-021 — PDF con 1.000 movimientos: paginado completo sin truncar filas

| Campo | Valor |
|---|---|
| **Título** | Verificar que el PDF de 1.000 movimientos incluye todas las filas, desde Mov QA 0001 hasta Mov QA 1000 |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta G (0099998888) con 1.000 movimientos según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0099998888; desde 2026-09-01; hasta 2026-09-30; formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0099998888, desde 2026-09-01, hasta 2026-09-30 y formato PDF | Campos completos |
| 2 | Tocar "Exportar" | Se descarga `movimientos_0099998888_2026-09-01_2026-09-30.pdf` |
| 3 | Abrir el PDF e ir a la última página | La última fila es `Mov QA 1000` con importe 1.00 y saldo 1000.00 |
| 4 | Buscar el texto `Mov QA 0500` en el PDF | Se encuentra una única vez, con saldo 500.00 |
| 5 | Buscar el texto `Mov QA 0001` en el PDF | Se encuentra en la primera página |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de la primera y última página; copia del PDF |
| **Estado** | Pendiente |
| **Notas** | Dependencia: usa los datos de la cuenta G (CP-020). El tiempo de generación del PDF no se valida acá: [SUPUESTO: el umbral de S-1 aplica a CSV; para PDF se registra el tiempo como observación]. |

---

### CP-022 — Seguridad: inyección de fórmulas en descripciones (CSV y XLSX)

| Campo | Valor |
|---|---|
| **Título** | Verificar que descripciones que empiezan con `=` o `@` no se ejecutan como fórmula al abrir el CSV o el XLSX |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio (seguridad; deriva de CA-2) |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta E (0024681357) según Datos base; Excel instalado; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0024681357; desde 2026-09-01; hasta 2026-09-30; formatos CSV y XLSX; descripciones `=1+1` y `@SUM(1+1)` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0024681357, desde 2026-09-01, hasta 2026-09-30 y formato CSV | Campos completos |
| 2 | Tocar "Exportar" | Se descarga `movimientos_0024681357_2026-09-01_2026-09-30.csv` |
| 3 | Abrir el CSV con Excel (doble clic) | En la columna Descripción se ve el texto literal `=1+1` y `@SUM(1+1)`; no se ve `2` ni se evalúa ninguna fórmula |
| 4 | Seleccionar formato XLSX y tocar "Exportar" | Se descarga `movimientos_0024681357_2026-09-01_2026-09-30.xlsx` |
| 5 | Abrir el XLSX en Excel | En la columna Descripción se ve el texto literal `=1+1` y `@SUM(1+1)` como texto, no como fórmula |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de Excel con ambas celdas |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: las descripciones que empiezan con `=`, `+`, `-` o `@` se neutralizan como texto (S-15)]. Si el PO no lo confirma, el caso queda como hallazgo de riesgo. Fuente típica: concepto de una transferencia recibida escrito por un tercero. |

---

### CP-023 — Seguridad: exportar una cuenta ajena por request directo

| Campo | Valor |
|---|---|
| **Título** | Verificar que pedir el export de la cuenta 0098765432 (titular QA-02) con la sesión de QA-01 es rechazado sin devolver datos |
| **Módulo** | Home banking / Movimientos / Exportación (API) |
| **Origen** | Exploratorio (seguridad; deriva de CA-1) |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta H (0098765432, titular QA-02) según Datos base; herramienta de proxy/HTTP (Burp, DevTools o Postman) para repetir requests |
| **Datos de prueba** | Cuenta ajena 0098765432; desde 2026-09-01; hasta 2026-09-30; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Exportar la cuenta propia 0012345678 en CSV (2026-09-01 a 2026-09-30) con DevTools abierto | Se descarga el archivo y se captura el request de exportación |
| 2 | Copiar el request y reemplazar el identificador de cuenta por el de 0098765432 | Request modificado listo para enviar |
| 3 | Enviar el request modificado con la sesión de QA-01 | La respuesta es un rechazo (403 o 404) |
| 4 | Revisar el cuerpo de la respuesta | No contiene ningún movimiento ni dato de la cuenta 0098765432 ni del titular QA-02 |
| 5 | Verificar que no se descargó archivo | No hay archivo con la cuenta 0098765432 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Request y response capturados (status y cuerpo) |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la exportación solo se permite sobre cuentas del cliente autenticado; código de rechazo 403 o 404 (S-14)]. El mecanismo exacto del request (parámetro de cuenta) depende de la implementación. |

---

### CP-024 — Seguridad: descarga sin sesión activa

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar luego de cerrar la sesión desde otra pestaña redirige al login y no entrega archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio (seguridad; deriva de CA-1) |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test en las pestañas 1 y 2; pestaña 1 en "Movimientos" con cuenta 0012345678, desde 2026-09-01, hasta 2026-09-30 y formato CSV ya completados; carpeta de descargas vacía |
| **Datos de prueba** | Usuario qa.cliente01@flockbank.test; cuenta 0012345678; rango 2026-09-01 a 2026-09-30; CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En la pestaña 2, cerrar sesión | La pestaña 2 muestra el login |
| 2 | Volver a la pestaña 1 | Sigue mostrando "Movimientos" con los datos completados |
| 3 | En la pestaña 1, tocar "Exportar" | Se redirige al login o se muestra un aviso de sesión vencida |
| 4 | Verificar la carpeta de descargas | No se descargó ningún archivo |
| 5 | Pegar en una pestaña nueva (sin sesión) la URL de descarga del request capturado | Se redirige al login y no se entrega archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del login/aviso; carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: sin sesión se redirige al login (S-14)]. |

---

### CP-025 — Seguridad: parámetros de fecha manipulados en el request (validación del servidor)

| Campo | Valor |
|---|---|
| **Título** | Verificar que el servidor rechaza fechas con inyección SQL o formato inválido enviadas por request directo |
| **Módulo** | Home banking / Movimientos / Exportación (API) |
| **Origen** | Exploratorio (seguridad; deriva de CA-1) |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; request de exportación de la cuenta 0012345678 capturado (como en CP-023 paso 1); herramienta de proxy/HTTP |
| **Datos de prueba** | Valores para el parámetro "desde": `2026-09-01' OR 1=1 --`; `<script>alert(1)</script>`; `2026-02-30`; `01/09/2026` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Reenviar el request con desde = `2026-09-01' OR 1=1 --` | Respuesta de rechazo (400) con mensaje genérico; no se devuelve archivo |
| 2 | Reenviar el request con desde = `<script>alert(1)</script>` | Respuesta de rechazo (400) con mensaje genérico; el valor no se refleja sin escapar en la respuesta |
| 3 | Reenviar el request con desde = `2026-02-30` (fecha inexistente) | Respuesta de rechazo (400); no se devuelve archivo |
| 4 | Reenviar el request con desde = `01/09/2026` (formato alternativo) | Respuesta de rechazo (400) o interpretación documentada; no se devuelve un archivo con movimientos de otro rango |
| 5 | Revisar el cuerpo de todas las respuestas | No contienen stack trace, consulta SQL ni nombres de tablas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Requests y responses capturados |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: validación de parámetros en el servidor, rechazo con 400 y mensaje genérico (S-16)]. El formato `01/09/2026` es ambiguo (DD/MM vs MM/DD); ver P-3. |

---

### CP-026 — Seguridad: formato fuera de la lista (CSV, XLSX, PDF) enviado por request directo

| Campo | Valor |
|---|---|
| **Título** | Verificar que el servidor rechaza el formato `docx` y `exe` aunque el front solo ofrezca CSV, XLSX y PDF |
| **Módulo** | Home banking / Movimientos / Exportación (API) |
| **Origen** | Exploratorio (seguridad; deriva de CA-1) |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; request de exportación de la cuenta 0012345678 capturado; herramienta de proxy/HTTP |
| **Datos de prueba** | Parámetro de formato: `docx`, `exe`, vacío |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Reenviar el request con formato = `docx` | Respuesta de rechazo (400); no se devuelve archivo |
| 2 | Reenviar el request con formato = `exe` | Respuesta de rechazo (400); no se devuelve archivo |
| 3 | Reenviar el request con formato vacío | Respuesta de rechazo (400); no se devuelve archivo |
| 4 | Revisar el cuerpo de las respuestas | Mensaje genérico, sin stack trace |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Requests y responses capturados |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: S-16]. Evita archivos con extensión arbitraria en el nombre (`movimientos_..._.exe`). |

---

### CP-027 — Doble clic en "Exportar"

| Campo | Valor |
|---|---|
| **Título** | Verificar que un doble clic rápido en "Exportar" genera una sola descarga |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio (concurrencia; deriva de CA-1) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; carpeta de descargas vacía; formulario completo con cuenta 0012345678, desde 2026-09-01, hasta 2026-09-30, formato CSV |
| **Datos de prueba** | Cuenta 0012345678; 2026-09-01 a 2026-09-30; CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Hacer doble clic rápido sobre "Exportar" | Se inicia una descarga |
| 2 | Esperar 10 segundos y revisar la carpeta de descargas | Existe un único archivo `movimientos_0012345678_2026-09-01_2026-09-30.csv`; no existe `movimientos_..._(1).csv` |
| 3 | Revisar el estado del botón durante la generación | El botón queda deshabilitado o muestra un indicador de progreso hasta terminar |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la carpeta de descargas; pestaña Network con la cantidad de requests |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: un doble clic produce una sola descarga (S-13)]. |

---

### CP-028 — Error del servicio de generación (500)

| Campo | Valor |
|---|---|
| **Título** | Verificar que un error 500 en la generación muestra un mensaje genérico, conserva el formulario y permite reintentar |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio (excepción; deriva de CA-2) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; en ambiente de QA, el servicio de exportación configurado para responder 500 (con mock o proxy que intercepta el request); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; 2026-09-01 a 2026-09-30; CSV; respuesta simulada HTTP 500 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Completar cuenta 0012345678, desde 2026-09-01, hasta 2026-09-30 y formato CSV | Formulario completo |
| 2 | Tocar "Exportar" con el 500 activo | Se muestra el mensaje "No pudimos generar el archivo. Intentá nuevamente." sin código de error ni stack trace |
| 3 | Verificar la carpeta de descargas | No se descargó ningún archivo (ni parcial) |
| 4 | Verificar el formulario | Conserva cuenta, fechas y formato |
| 5 | Desactivar el 500 y tocar "Exportar" otra vez | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` con 4 líneas de datos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; request/response con el 500 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: texto del mensaje, formulario conservado y reintento posible (S-12)]. |

---

### CP-029 — Red caída durante la generación

| Campo | Valor |
|---|---|
| **Título** | Verificar que cortar la red durante la exportación no deja un archivo parcial ni corrupto y permite reintentar |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio (excepción; deriva de CA-2) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuenta G (0099998888) con 1.000 movimientos según Datos base; DevTools con throttling "Slow 3G" disponible; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0099998888; 2026-09-01 a 2026-09-30; PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Completar cuenta 0099998888, desde 2026-09-01, hasta 2026-09-30 y formato PDF | Formulario completo |
| 2 | Activar "Slow 3G" en DevTools y tocar "Exportar" | Se inicia la generación/descarga lenta |
| 3 | Pasar la red a "Offline" durante la descarga | La descarga falla |
| 4 | Verificar la carpeta de descargas | No hay un `.pdf` incompleto que se pueda abrir como válido (solo archivo temporal de descarga fallida, por ejemplo `.crdownload`) |
| 5 | Verificar la pantalla | Se muestra un mensaje de error o la descarga figura como fallida, sin mensaje de éxito |
| 6 | Volver la red a "Online" y tocar "Exportar" | Se descarga el PDF completo con 1.000 filas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la carpeta de descargas y del estado de la descarga |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: S-12]. |

---

### CP-030 — Accesibilidad: exportar solo con teclado

| Campo | Valor |
|---|---|
| **Título** | Verificar que el flujo completo de exportación puede hacerse solo con teclado |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio (accesibilidad; deriva de CA-1) |
| **Tipo** | No funcional (accesibilidad) |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test en "Movimientos"; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; 2026-09-01 a 2026-09-30; CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Recorrer con Tab desde el inicio de la pantalla hasta el selector de cuenta | El foco es visible en cada control y el orden es lógico (cuenta, desde, hasta, formato, Exportar) |
| 2 | Seleccionar la cuenta 0012345678, escribir 2026-09-01 y 2026-09-30 y elegir CSV solo con teclado | Los valores quedan cargados |
| 3 | Llegar al botón "Exportar" con Tab y pulsar Enter | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` |
| 4 | Repetir con un rango sin movimientos (cuenta 0011112222, 2026-01-01 a 2026-01-31) | El mensaje de CP-007 se muestra y es anunciado/visible sin usar el mouse |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Grabación de pantalla corta del recorrido |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: accesibilidad por teclado esperada, sin estándar declarado (S-18)]. |

---

### CP-031 — Exploratorio: descarga desde navegador móvil

| Campo | Valor |
|---|---|
| **Título** | Verificar cómo se comporta la descarga de CSV, XLSX y PDF en un navegador móvil |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio |
| **Tipo** | No funcional (compatibilidad) |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test en Chrome para Android y Safari para iOS (dispositivos reales o emuladores) |
| **Datos de prueba** | Cuenta 0012345678; 2026-09-01 a 2026-09-30; los tres formatos |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Exportar en CSV desde el móvil | Registrar si se descarga, con qué nombre y dónde queda guardado |
| 2 | Exportar en XLSX desde el móvil | Registrar si se descarga o se abre y con qué nombre |
| 3 | Exportar en PDF desde el móvil | Registrar si se descarga o se abre en el visor y con qué nombre |
| 4 | Comparar los nombres obtenidos con `movimientos_0012345678_2026-09-01_2026-09-30.<ext>` | Registrar cualquier diferencia |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de cada resultado |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: no se sabe si el producto soporta móvil ni qué navegadores (S-17)]. El resultado esperado queda abierto a observación (exploratorio). |

---

### CP-032 — Cambio de cuenta entre exportaciones sin recargar la pantalla

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar la cuenta A y luego la cuenta B sin recargar genera cada archivo con los datos de su propia cuenta |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como qa.cliente01@flockbank.test; cuentas A (ARS) y B (USD) según Datos base; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta 0012345678 y luego 0087654321; 2026-09-01 a 2026-09-30; CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0012345678, desde 2026-09-01, hasta 2026-09-30 y CSV | Formulario completo |
| 2 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` con 4 líneas de datos |
| 3 | Sin recargar la pantalla, cambiar la cuenta a 0087654321 | La cuenta seleccionada es 0087654321 |
| 4 | Tocar "Exportar" | Se descarga `movimientos_0087654321_2026-09-01_2026-09-30.csv` |
| 5 | Abrir el segundo CSV | Contiene solo 2 líneas de datos (`Compra de divisas`, `Pago servicio exterior`) con importes en USD; no contiene movimientos de la cuenta 0012345678 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Copia de ambos CSV; screenshot del selector de cuenta |
| **Estado** | Pendiente |
| **Notas** | Detecta estado "pegado" de la cuenta anterior en el request. |

---

## 4. Priorización por riesgo

Prioridad calculada con la matriz probabilidad × impacto de la fase F5 (Alta×Alto = Alta, Alta×Medio = Alta, Media×Alto = Alta, Media×Medio = Media, Baja×Alto = Media, Baja×Medio = Media, Media×Bajo = Baja, Baja×Bajo = Baja).

| Caso | Probabilidad | Impacto | Prioridad | Humo |
|---|---|---|---|---|
| CP-001 | Media | Alto | Alta | Sí |
| CP-002 | Media | Alto | Alta | Sí |
| CP-003 | Media | Alto | Alta | |
| CP-004 | Media | Alto | Alta | Sí |
| CP-005 | Media | Alto | Alta | |
| CP-006 | Media | Medio | Media | |
| CP-007 | Alta | Medio | Alta | Sí |
| CP-008 | Media | Medio | Media | |
| CP-009 | Media | Medio | Media | |
| CP-010 | Media | Alto | Alta | |
| CP-011 | Media | Medio | Media | |
| CP-012 | Alta | Medio | Alta | |
| CP-013 | Media | Medio | Media | |
| CP-014 | Media | Medio | Media | |
| CP-015 | Media | Medio | Media | |
| CP-016 | Baja | Bajo | Baja | |
| CP-017 | Baja | Bajo | Baja | |
| CP-018 | Media | Medio | Media | |
| CP-019 | Media | Alto | Alta | |
| CP-020 | Media | Medio | Media | |
| CP-021 | Media | Medio | Media | |
| CP-022 | Media | Alto | Alta | |
| CP-023 | Baja | Alto | Media | |
| CP-024 | Baja | Alto | Media | |
| CP-025 | Baja | Alto | Media | |
| CP-026 | Baja | Medio | Media | |
| CP-027 | Media | Medio | Media | |
| CP-028 | Media | Medio | Media | |
| CP-029 | Media | Medio | Media | |
| CP-030 | Media | Bajo | Baja | |
| CP-031 | Media | Bajo | Baja | |
| CP-032 | Media | Alto | Alta | |

**Subset de humo (4 casos):** CP-001, CP-002, CP-004, CP-007.

**Orden de ejecución sugerido:**
1. Humo: CP-001, CP-002, CP-004, CP-007.
2. Alta: CP-003, CP-005, CP-010, CP-012, CP-019, CP-022, CP-032.
3. Media: CP-006, CP-008, CP-009, CP-011, CP-013, CP-014, CP-015, CP-018, CP-020, CP-021, CP-023, CP-024, CP-025, CP-026, CP-027, CP-028, CP-029.
4. Baja: CP-016, CP-017, CP-030, CP-031.

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Seleccionar cuenta, rango de fechas y formato, tocar "Exportar" | CP-001, CP-003, CP-004, CP-009, CP-011, CP-012, CP-013, CP-014, CP-015, CP-016, CP-017, CP-023, CP-024, CP-025, CP-026, CP-027, CP-032 | ✓ Cubierta |
| CA-2 | Archivo con movimientos del período: fecha, descripción, importe y saldo; generado "rápidamente" | CP-002, CP-003, CP-004, CP-005, CP-006, CP-009, CP-010, CP-011, CP-018, CP-019, CP-020, CP-021, CP-028, CP-029, CP-032 | ✓ Cubierta (el umbral de "rápidamente" es supuesto, ver P-1) |
| CA-3 | Nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>` | CP-001, CP-003, CP-004, CP-005, CP-009, CP-014, CP-032 | ✓ Cubierta (formato de fecha y `<cuenta>` son supuestos, ver P-3, P-4) |
| CA-4 | Rango sin movimientos muestra un mensaje adecuado | CP-007, CP-008 | ✓ Cubierta (texto del mensaje es supuesto, ver P-6) |
| NT-1 | Importes en la moneda de la cuenta (ARS o USD) | CP-002, CP-005, CP-032 | ✓ Cubierta |

**Cobertura: 4 de 4 CAs cubiertas = 100%** (más la nota NT-1). CAs sin cubrir: ninguna.

**Verificación contra los casos listados:** 32 casos (CP-001 a CP-032): 22 con origen en un CA y 10 con origen "Exploratorio" (CP-023 a CP-029 y CP-022, CP-030, CP-031, todos con supuesto explícito); ningún caso sin origen.

## 6. Supuestos asumidos

| ID | Supuesto | Clase | Pregunta | Casos |
|---|---|---|---|---|
| S-1 | "Rápidamente" = máximo 5 s hasta el inicio de la descarga, hasta 1.000 movimientos | IMPORTANTE | P-1 | CP-020, CP-021 |
| S-2 | Rango máximo de 365 días (extremos incluidos); si se excede, mensaje de error y sin archivo | IMPORTANTE | P-2 | CP-011, CP-012 |
| S-3 | "Desde" y "hasta" son inclusivos (día calendario completo, hasta 23:59:59) | IMPORTANTE | P-3 | CP-002, CP-009, CP-010 |
| S-4 | Desde > hasta se bloquea con mensaje de validación y sin archivo | IMPORTANTE | P-3 | CP-013 |
| S-5 | Fechas posteriores a hoy se bloquean con mensaje; hoy se permite | IMPORTANTE | P-3 | CP-014, CP-015 |
| S-6 | `<cuenta>` = número de cuenta de 10 dígitos sin separadores; fechas en el nombre como AAAA-MM-DD | IMPORTANTE | P-3, P-4 | CP-001, CP-003, CP-004, CP-005 y casos con nombre de archivo |
| S-7 | Contenido: 4 columnas exactas (Fecha, Descripción, Importe, Saldo); CSV UTF-8 con encabezado, coma, fecha AAAA-MM-DD, punto decimal con 2 decimales sin miles, débitos negativos, escape RFC 4180; XLSX con celdas fecha/numérico; PDF con tabla y fecha DD/MM/AAAA | IMPORTANTE | P-5 | CP-002, CP-003, CP-004, CP-018, CP-019 |
| S-8 | Orden cronológico ascendente; saldo = saldo de la cuenta posterior al movimiento (no recalculado en el rango) | IMPORTANTE | P-5 | CP-002, CP-010 |
| S-9 | Sin conversión de moneda; XLSX/PDF muestran el código ARS/USD; el CSV no incluye moneda | IMPORTANTE | P-5 | CP-005 |
| S-10 | CA-4: mensaje informativo "No hay movimientos en el período seleccionado" y no se descarga archivo | IMPORTANTE | P-6 | CP-007, CP-008 |
| S-11 | Fechas obligatorias sin valor por defecto; formato sin preselección | MENOR | P-5 | CP-016, CP-017 |
| S-12 | Falla de generación/red: mensaje "No pudimos generar el archivo. Intentá nuevamente.", sin detalles técnicos ni archivo parcial, formulario conservado y reintento posible | IMPORTANTE | P-7 | CP-028, CP-029 |
| S-13 | Doble clic en "Exportar" produce una sola descarga | IMPORTANTE | P-8 | CP-027 |
| S-14 | Solo cuentas propias (pedido ajeno rechazado con 403/404 sin datos); sin sesión, redirección al login | IMPORTANTE | P-8 | CP-023, CP-024 |
| S-15 | Descripciones que empiezan con `=`, `+`, `-` o `@` se neutralizan como texto en CSV/XLSX | IMPORTANTE | P-8 | CP-022 |
| S-16 | El servidor valida fechas y formato y rechaza con 400 y mensaje genérico | IMPORTANTE | P-8 | CP-025, CP-026 |
| S-17 | Navegadores/dispositivos soportados desconocidos (móvil explorado, sin resultado esperado fijo) | MENOR | (no se pregunta: baja prioridad) | CP-031 |
| S-18 | Accesibilidad por teclado esperada del flujo, sin estándar declarado | MENOR | (no se pregunta: baja prioridad) | CP-030 |
| S-19 | Cuentas cerradas/bloqueadas y nombre de archivo repetido (el navegador agrega "(1)") quedan fuera de esta suite | MENOR | (no se pregunta) | Sin caso |

## 7. Auto-revisión

**Críticos**

- [x] **Cada CA tiene ≥1 caso**: CA-1 (CP-001, CP-003...), CA-2 (CP-002...), CA-3 (CP-001, CP-003, CP-004...), CA-4 (CP-007, CP-008); ninguna sin cobertura.
- [x] **Cero comportamiento inventado**: todo resultado esperado no definido por la HU lleva `[SUPUESTO: ...]` con ID S-n o el caso es exploratorio (CP-031).
- [x] **Pasos reproducibles por terceros**: pasos atómicos con datos concretos (cuentas, fechas, valores exactos); datos base con instrucción de creación (seed de CP-020/CP-021).
- [x] **Resultados esperados observables**: nombre de archivo exacto, líneas CSV literales, mensajes y códigos HTTP; los casos exploratorios (CP-031) indican qué registrar.
- [x] **IDs únicos y secuenciales**: CP-001 a CP-032, sin huecos.
- [x] **Matriz de cobertura completa**: 4/4 CAs = 100%, verificada contra los casos listados.
- [x] **Preguntas al PO ≤ 8**: 8 preguntas (P-1 a P-8), todas con default propuesto y ninguna trivial.

**Observaciones**

- [x] ≥1 negativo/borde por funcionalidad con riesgo: 6 Funcionales/Humo positivos de contenido y 12 negativos/bordes/seguridad/excepción (proporción mayor a 1 por cada 2 positivos).
- [x] Prioridades justificadas por la matriz de riesgo (sección 4).
- [x] Subset de humo marcado: CP-001, CP-002, CP-004, CP-007.
- [ ] Casos duplicados o casi-duplicados: CP-016 y CP-017 son similares en intención (validación de obligatorios) pero con distinto campo y assertion; se mantienen separados. Observación conocida.
- [x] Dependencias declaradas en Precondiciones (CP-002 depende de CP-001; CP-006 de CP-002, CP-003 y CP-004).
- [x] Supuestos consolidados en la sección 6.

Resultado del gate: sin fallas críticas.
