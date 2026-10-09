# Suite de pruebas — HU-202: Exportación de movimientos de cuenta

> Fecha de generación: 2026-10-09 · Modo: completo (F3) · Texto original de la HU tomado de `ejemplos/hu-202.md`.

## 1. Resumen del análisis

**Validación de entrada (F0):** es una HU con 4 criterios de aceptación. No se reenvía a otro flujo.

| Ítem | Detalle |
|---|---|
| **Rol** | Cliente de home banking |
| **Funcionalidad** | Exportar los movimientos de una cuenta, en un rango de fechas, en formato CSV, XLSX o PDF, desde la pantalla "Movimientos" |
| **Objetivo de negocio** | Conciliar los movimientos con el sistema contable del cliente |
| **Entidades y datos** | Cliente; cuentas (ARS y USD); movimientos (fecha, descripción, importe, saldo); rango de fechas (desde/hasta); formato (CSV/XLSX/PDF); archivo generado `movimientos_<cuenta>_<desde>_<hasta>.<ext>` |

**Criterios de aceptación (textuales):**

- **CA-1**: Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar".
- **CA-2**: El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo.
- **CA-3**: El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`.
- **CA-4**: Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado.
- **Nota del equipo**: los importes se muestran en la moneda de la cuenta (ARS o USD).

**Clasificación de gaps (F2, checklist de `preguntas-al-po.md`):**

| Gap | Categoría | Clase | Tratamiento |
|---|---|---|---|
| "Rápidamente" no es verificable (CA-2) | A | IMPORTANTE | Caso con `[SUPUESTO: <= 5 s]` (P-1) |
| "Mensaje adecuado" sin texto ni comportamiento de descarga (CA-4) | A / C | IMPORTANTE | `[SUPUESTO]` de texto y de "no se descarga archivo" (P-2) |
| Reglas del rango (inclusivo, futuro, desde > hasta, máximo), obligatoriedad y tipo de entrada de fechas | B | IMPORTANTE | `[SUPUESTO]` (P-3) |
| Volumen máximo de filas / masa de datos | B | IMPORTANTE | `[SUPUESTO]` (P-4) |
| Significado de `<cuenta>` y formato de `<desde>`/`<hasta>` en el nombre | B | IMPORTANTE | `[SUPUESTO]` (P-5) |
| Estructura del contenido (columnas, formato de fecha/importe, signo, moneda, encoding, orden) | B / J | IMPORTANTE | `[SUPUESTO]` (P-6) |
| Permisos, cuentas ajenas/cotitulares/cerradas, sesión expirada, inyección en archivos, auditoría (dinero + datos personales) | D / F | IMPORTANTE | `[SUPUESTO]` (P-7) |
| Errores del servicio, doble pedido, sesiones simultáneas | C / G | IMPORTANTE | `[SUPUESTO]` (P-8) |
| Alcance negativo: no se define envío por email ni historial de exportaciones | H | MENOR | Se anota como supuesto S-30 |
| Navegadores/dispositivos soportados y accesibilidad | J | MENOR | Se anota como supuesto S-27 / S-28 |

No hay gaps BLOQUEANTES (el happy path es diseñable con defaults), por lo que se genera la suite completa.

**Observación sobre el objetivo (A):** el objetivo "conciliar con mi sistema contable" exige que el archivo sea procesable por máquina (importes numéricos, fechas sin ambigüedad). Los CA no lo piden explícitamente; se cubre con `[SUPUESTO]` en P-6.

**Dataset de referencia** (todos los datos de prueba salen de acá; el equipo debe cargarlo en el ambiente QA):

- **Cliente QA-01**: usuario `qa.cliente01`, titular de las cuentas 0012345678 (caja de ahorro ARS), 0098765432 (caja de ahorro USD), 0011111111 (caja de ahorro ARS sin ningún movimiento), 0022222222 (ARS, 1.000 movimientos en agosto 2026), 0033333333 (ARS, 10.000 movimientos entre 01/06/2026 y 30/06/2026), 0044444444 (ARS, 10.001 movimientos entre 01/06/2026 y 30/06/2026) y 0055555555 (ARS, casos de texto especial).
- **Cliente QA-02**: usuario `qa.cliente02`, titular de la cuenta 0077777777. La cuenta 0099999999 no existe.
- **Cuenta 0012345678 (ARS)**, movimientos relevantes (orden cronológico):

| Fecha | Descripción | Importe | Saldo |
|---|---|---|---|
| 31/12/2025 | Pago Impuesto Sellos | -12.000,00 | 512.000,00 |
| 02/01/2026 | Acreditación Reintegro | 3.500,00 | 515.500,00 |
| 31/08/2026 | Pago tarjeta | -30.000,00 | 400.000,00 |
| 01/09/2026 | Acreditación haberes | 850.000,50 | 1.250.000,50 |
| 05/09/2026 | Compra Supermercado Ñandú | -45.320,75 | 1.204.679,75 |
| 15/09/2026 | Transferencia a Pérez José | -200.000,00 | 1.004.679,75 |
| 30/09/2026 | Débito Servicio Luz | -18.450,25 | 986.229,50 |
| 01/10/2026 | Interés | 1.200,00 | 987.429,50 |

  No existen movimientos de 0012345678 entre el 01/07/2026 y el 31/07/2026 (hay otros movimientos fuera de ese mes).
- **Cuenta 0098765432 (USD)**: 10/09/2026 "Depósito en efectivo USD" +1.500,00 (saldo 1.500,00); 20/09/2026 "Compra servicios Cloud" -49,99 (saldo 1.450,01).
- **Cuenta 0055555555 (ARS)**, saldo inicial 100.000,00: 12/09/2026 `=1+1` -100,00 (99.900,00); `+1+1` -200,00 (99.700,00); `@SUM(1+1)` -300,00 (99.400,00); `<script>alert(1)</script>` -400,00 (99.000,00). 13/09/2026 `Pago "Kiosco", S.A.` -1.500,00 (97.500,00); `Café Ñandú ☕ – Año Nuevo` -2.300,00 (95.200,00). 14/09/2026 un movimiento de -5.000,00 con una descripción de 200 caracteres (texto exacto en CP-028).
- **Fecha de referencia de ejecución**: 09/10/2026 (hoy). Si se ejecuta otro día, "fecha futura" = hoy + 1.

## 2. Preguntas para el PO

Todas son IMPORTANTES (ninguna bloqueante). Ordenadas por impacto en el diseño.

**P-1. [A. Criterios de aceptación] CA-2 dice "rápidamente": ¿el archivo debe comenzar a descargarse en <= 5 s para hasta 1.000 movimientos, o hay otro umbral?**
- **Por qué importa**: sin umbral, el CA no es verificable y no se puede declarar fallido un caso de performance.
- **Default propuesto**: <= 5 segundos desde "Exportar" hasta el inicio de la descarga, para hasta 1.000 movimientos y los tres formatos. Queda como `[SUPUESTO]` en CP-014.

**P-2. [A / C. CA-4] ¿Cuál es el texto exacto del mensaje de rango vacío y, en ese caso, se descarga o no un archivo (por ejemplo, uno con solo encabezados)?**
- **Por qué importa**: "mensaje adecuado" no es assertable; además un archivo vacío podría romper la conciliación contable.
- **Default propuesto**: se muestra "No hay movimientos para el período seleccionado." en pantalla (junto al formulario), no se genera ni descarga ningún archivo, y los filtros se conservan. Aplica igual a una cuenta sin ningún movimiento.

**P-3. [B. Datos y validaciones] ¿Cuáles son las reglas del rango de fechas y de los campos obligatorios?**
- **Por qué importa**: define todos los bordes y negativos del formulario (off-by-one, fechas inválidas, rangos enormes).
- **Default propuesto**: cuenta, desde, hasta y formato son obligatorios y no hay preselección; los extremos son inclusivos; desde <= hasta; hasta no puede ser futura; rango máximo 365 días corridos (inclusive); las fechas se ingresan en formato dd/mm/aaaa (tipeo o calendario). Mensajes: "Seleccioná una cuenta.", "Seleccioná un formato.", "Ingresá la fecha Desde.", "Ingresá la fecha Hasta.", "Ingresá una fecha válida.", "La fecha Desde no puede ser posterior a la fecha Hasta.", "La fecha Hasta no puede ser futura.", "El rango no puede superar los 365 días.".

**P-4. [B. Datos y validaciones] ¿Existe un máximo de movimientos por exportación y qué se muestra si se excede?**
- **Por qué importa**: sin límite hay riesgo de timeouts y de consumo de recursos; define el borde de volumen.
- **Default propuesto**: máximo 10.000 movimientos por archivo; si se supera se muestra "El período seleccionado supera el máximo de 10.000 movimientos. Reducí el rango de fechas." y no se descarga archivo.

**P-5. [B. Datos y validaciones] En el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`, ¿`<cuenta>` es el número de cuenta completo (no CBU ni alias) y las fechas van como aaaa-mm-dd?**
- **Por qué importa**: el nombre es parte del CA-3; además, el número de cuenta en el nombre es un dato personal.
- **Default propuesto**: `<cuenta>` = número de cuenta de 10 dígitos sin separadores; `<desde>` y `<hasta>` = aaaa-mm-dd; `<ext>` = `csv`, `xlsx` o `pdf` en minúsculas. Ejemplo: `movimientos_0012345678_2026-09-01_2026-09-30.csv`.

**P-6. [B / J. Datos, formatos e i18n] ¿Cuál es el formato exacto del contenido del archivo (columnas, fecha, importe, signo, moneda, encoding, orden)?**
- **Por qué importa**: el objetivo es conciliar con un sistema contable; un separador decimal o encoding distinto rompe la importación. CA-2 solo lista los campos.
- **Default propuesto**: columnas `Fecha`, `Descripción`, `Importe (<MON>)`, `Saldo (<MON>)` en ese orden, donde `<MON>` es ARS o USD según la cuenta (sin conversión de moneda); orden cronológico ascendente; CSV UTF-8 con BOM, separador coma, fecha aaaa-mm-dd, decimales con punto y 2 decimales, sin separador de miles, débitos con signo negativo, texto con comas o comillas entre comillas dobles (RFC 4180); XLSX con una hoja, encabezado en la fila 1, fecha como tipo fecha e importes/saldos como tipo numérico con 2 decimales; PDF con cuenta, moneda y período en el encabezado y importes con formato es-AR (1.250.000,50).

**P-7. [D / F. Permisos y seguridad] ¿Quién puede exportar qué cuenta y qué protecciones se esperan sobre el archivo y la acción?**
- **Por qué importa**: es dinero y datos personales; una falla de autorización expone movimientos de terceros, y un archivo con fórmulas maliciosas puede ejecutarse en el Excel del cliente.
- **Default propuesto**: solo el titular autenticado puede exportar sus propias cuentas activas (cualquier otra cuenta responde 403 sin revelar si existe); sin sesión válida se responde 401; cotitulares, apoderados y cuentas cerradas o bloqueadas quedan fuera de este alcance; las descripciones que empiezan con `=`, `+`, `-` o `@` se neutralizan en CSV/XLSX (prefijo `'`); cada exportación se registra en auditoría (usuario, cuenta, rango, formato, fecha y hora, sin el contenido).

**P-8. [C / G. Errores y concurrencia] ¿Qué ve el cliente si falla la generación y qué pasa con doble clic o con dos sesiones?**
- **Por qué importa**: define los resultados esperados de todas las excepciones; un doble clic podría generar descargas duplicadas.
- **Default propuesto**: si falla el servicio se muestra "No pudimos generar el archivo. Intentá nuevamente en unos minutos." sin detalles técnicos y se puede reintentar; sin red se muestra "No hay conexión. Verificá tu red e intentá nuevamente."; el botón "Exportar" se deshabilita mientras se genera, por lo que un doble clic produce una sola descarga; se permiten sesiones simultáneas del mismo cliente y cada exportación es independiente.

## 3. Casos de prueba

### CP-001 — Exportar en CSV los movimientos de septiembre de una cuenta en ARS

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar en CSV la cuenta 0012345678 del 01/09/2026 al 30/09/2026 descarga el archivo `movimientos_0012345678_2026-09-01_2026-09-30.csv` con 4 movimientos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; dataset de referencia cargado; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/09/2026; Hasta 30/09/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a "Movimientos" | Se muestra la pantalla con los selectores de cuenta, desde, hasta, formato y el botón "Exportar" |
| 2 | Seleccionar la cuenta 0012345678 | La cuenta 0012345678 queda seleccionada |
| 3 | Ingresar Desde = 01/09/2026 | El campo Desde muestra 01/09/2026 |
| 4 | Ingresar Hasta = 30/09/2026 | El campo Hasta muestra 30/09/2026 |
| 5 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 6 | Tocar "Exportar" | El navegador descarga un archivo llamado exactamente `movimientos_0012345678_2026-09-01_2026-09-30.csv` |
| 7 | Abrir el archivo con un editor de texto | El archivo contiene 1 fila de encabezado y 4 filas de movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del formulario completo (paso 5), captura de la barra/lista de descargas con el nombre (paso 6), screenshot del archivo abierto (paso 7) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: nombre con número de cuenta de 10 dígitos y fechas aaaa-mm-dd, ver P-5]`. El contenido campo por campo se verifica en CP-005. Subset de humo. |

### CP-002 — Exportar en XLSX los movimientos de septiembre de una cuenta en ARS

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar en XLSX la cuenta 0012345678 del 01/09/2026 al 30/09/2026 descarga `movimientos_0012345678_2026-09-01_2026-09-30.xlsx` que abre sin errores |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; dataset de referencia cargado; carpeta de Descargas vacía; Microsoft Excel instalado |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/09/2026; Hasta 30/09/2026; Formato XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a "Movimientos" | Se muestra el formulario de exportación |
| 2 | Seleccionar la cuenta 0012345678 | La cuenta queda seleccionada |
| 3 | Ingresar Desde = 01/09/2026 | El campo muestra 01/09/2026 |
| 4 | Ingresar Hasta = 30/09/2026 | El campo muestra 30/09/2026 |
| 5 | Seleccionar el formato XLSX | El formato XLSX queda seleccionado |
| 6 | Tocar "Exportar" | Se descarga un archivo llamado exactamente `movimientos_0012345678_2026-09-01_2026-09-30.xlsx` |
| 7 | Abrir el archivo en Excel | Excel abre el archivo sin mensajes de error ni de reparación |
| 8 | Contar las filas con datos de la hoja | La hoja tiene 1 fila de encabezado y 4 filas de movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Lista de descargas con el nombre (paso 6); screenshot de la hoja abierta (paso 8) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: XLSX con una hoja y encabezado en la fila 1, ver P-6]`. Subset de humo. Tipos de datos de las celdas en CP-006. |

### CP-003 — Exportar en PDF los movimientos de septiembre de una cuenta en ARS

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar en PDF la cuenta 0012345678 del 01/09/2026 al 30/09/2026 descarga `movimientos_0012345678_2026-09-01_2026-09-30.pdf` que abre sin errores |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; dataset de referencia cargado; carpeta de Descargas vacía; lector de PDF instalado |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/09/2026; Hasta 30/09/2026; Formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ir a "Movimientos" | Se muestra el formulario de exportación |
| 2 | Seleccionar la cuenta 0012345678 | La cuenta queda seleccionada |
| 3 | Ingresar Desde = 01/09/2026 | El campo muestra 01/09/2026 |
| 4 | Ingresar Hasta = 30/09/2026 | El campo muestra 30/09/2026 |
| 5 | Seleccionar el formato PDF | El formato PDF queda seleccionado |
| 6 | Tocar "Exportar" | Se descarga un archivo llamado exactamente `movimientos_0012345678_2026-09-01_2026-09-30.pdf` |
| 7 | Abrir el archivo en el lector de PDF | El PDF abre sin errores y muestra 4 movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Lista de descargas con el nombre (paso 6); screenshot del PDF (paso 7) |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. Detalle del contenido del PDF en CP-007. |

### CP-004 — Exportar los movimientos de una cuenta en USD mostrando importes en dólares

| Campo | Valor |
|---|---|
| **Título** | Verificar que exportar en CSV la cuenta USD 0098765432 muestra importes y saldos en USD sin conversión a ARS |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 (nota del equipo: moneda de la cuenta) |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0098765432 (USD); Desde 01/09/2026; Hasta 30/09/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta 0098765432 | La cuenta USD queda seleccionada |
| 2 | Ingresar Desde = 01/09/2026 | El campo muestra 01/09/2026 |
| 3 | Ingresar Hasta = 30/09/2026 | El campo muestra 30/09/2026 |
| 4 | Seleccionar el formato CSV | El formato CSV queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga `movimientos_0098765432_2026-09-01_2026-09-30.csv` |
| 6 | Abrir el archivo con un editor de texto | El encabezado es `Fecha,Descripción,Importe (USD),Saldo (USD)` |
| 7 | Leer la primera fila de datos | La fila es `2026-09-10,Depósito en efectivo USD,1500.00,1500.00` |
| 8 | Leer la segunda fila de datos | La fila es `2026-09-20,Compra servicios Cloud,-49.99,1450.01` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del archivo abierto (pasos 6 a 8) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: la moneda se indica en el encabezado "Importe (USD)"/"Saldo (USD)" y no hay conversión, ver P-6]`. Compara contra la cuenta ARS de CP-005. |

### CP-005 — Verificar el contenido exacto del CSV (campos, valores y saldo coherente)

| Campo | Valor |
|---|---|
| **Título** | Verificar que el CSV de la cuenta 0012345678 de septiembre 2026 contiene fecha, descripción, importe y saldo exactos y saldos coherentes |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | CP-001 ejecutado con éxito (archivo `movimientos_0012345678_2026-09-01_2026-09-30.csv` disponible) |
| **Datos de prueba** | Archivo de CP-001; dataset de la cuenta 0012345678 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el archivo con un editor de texto que muestre el encoding (UTF-8) | El archivo está codificado en UTF-8 con BOM |
| 2 | Leer la fila de encabezado | La fila es `Fecha,Descripción,Importe (ARS),Saldo (ARS)` |
| 3 | Leer la fila 2 | La fila es `2026-09-01,Acreditación haberes,850000.50,1250000.50` |
| 4 | Leer la fila 3 | La fila es `2026-09-05,Compra Supermercado Ñandú,-45320.75,1204679.75` |
| 5 | Leer la fila 4 | La fila es `2026-09-15,Transferencia a Pérez José,-200000.00,1004679.75` |
| 6 | Leer la fila 5 | La fila es `2026-09-30,Débito Servicio Luz,-18450.25,986229.50` |
| 7 | Verificar que no existen más filas | El archivo termina en la fila 5 (los movimientos del 31/08/2026 y del 01/10/2026 no aparecen) |
| 8 | Calcular saldo de la fila 2 + importe de la fila 4 | El resultado 1250000.50 + (-45320.75) = 1204679.75 coincide con el saldo de la fila 4 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del archivo abierto en el editor |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: columnas, orden cronológico ascendente, fecha aaaa-mm-dd, punto decimal, sin separador de miles, BOM UTF-8, ver P-6]`. |

### CP-006 — Verificar tipos de dato de las celdas del XLSX

| Campo | Valor |
|---|---|
| **Título** | Verificar que en el XLSX las fechas son tipo fecha e importes y saldos son numéricos con 2 decimales |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | CP-002 ejecutado con éxito (archivo `movimientos_0012345678_2026-09-01_2026-09-30.xlsx` disponible); Microsoft Excel instalado |
| **Datos de prueba** | Archivo de CP-002 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el archivo en Excel | Se ve una sola hoja con encabezados en la fila 1: `Fecha`, `Descripción`, `Importe (ARS)`, `Saldo (ARS)` |
| 2 | Seleccionar la celda A2 y mirar su formato en "Formato de celdas" | A2 contiene el 01/09/2026 y su categoría es Fecha |
| 3 | Seleccionar la celda C3 y mirar su formato | C3 vale -45320,75 (según configuración regional) y su categoría es Número con 2 decimales |
| 4 | Seleccionar la celda D5 y mirar su formato | D5 vale 986229,50 y su categoría es Número con 2 decimales |
| 5 | Ingresar en una celda libre la fórmula `=SUM(C2:C5)` | El resultado es 586229,50 (no 0 ni #VALOR!, por lo que los importes no son texto) |
| 6 | Comparar 586229,50 con (saldo final D5 - saldo inicial 400.000,00) | Ambos valores son iguales a 586229,50 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la celda C3 con el diálogo "Formato de celdas"; screenshot del resultado de la suma |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: XLSX con importes/saldos numéricos y fecha tipo fecha, ver P-6]`. No modificar ni guardar el archivo exportado. |

### CP-007 — Verificar el contenido del PDF

| Campo | Valor |
|---|---|
| **Título** | Verificar que el PDF muestra cuenta, período, los 4 movimientos y los importes con formato es-AR |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | CP-003 ejecutado con éxito (archivo `movimientos_0012345678_2026-09-01_2026-09-30.pdf` disponible) |
| **Datos de prueba** | Archivo de CP-003 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el PDF | El PDF abre y muestra un encabezado con la cuenta 0012345678, la moneda ARS y el período 01/09/2026 al 30/09/2026 |
| 2 | Leer la primera fila de movimientos | Muestra 01/09/2026, "Acreditación haberes", 850.000,50 y 1.250.000,50 |
| 3 | Leer la segunda fila | Muestra 05/09/2026, "Compra Supermercado Ñandú", -45.320,75 y 1.204.679,75 |
| 4 | Leer la tercera fila | Muestra 15/09/2026, "Transferencia a Pérez José", -200.000,00 y 1.004.679,75 |
| 5 | Leer la cuarta fila | Muestra 30/09/2026, "Débito Servicio Luz", -18.450,25 y 986.229,50 |
| 6 | Seleccionar con el cursor el texto de la descripción de la fila 2 | El texto "Compra Supermercado Ñandú" es seleccionable y la Ñ se ve correctamente |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del PDF completo |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: PDF con cuenta/moneda/período en el encabezado e importes con formato es-AR, ver P-6]`. |

### CP-008 — Exportar dos veces seguidas cambiando cuenta y formato sin recargar

| Campo | Valor |
|---|---|
| **Título** | Verificar que tras exportar la cuenta ARS en CSV, cambiar a la cuenta USD en PDF exporta la cuenta y el formato nuevos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | CP-001 ejecutado con éxito; sesión de `qa.cliente01` abierta en "Movimientos" con los datos de CP-001 todavía cargados; carpeta de Descargas vacía |
| **Datos de prueba** | Primera exportación: cuenta 0012345678, CSV, 01/09/2026 al 30/09/2026. Segunda: cuenta 0098765432, PDF, mismas fechas |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Tocar "Exportar" con la cuenta 0012345678 y el formato CSV | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` |
| 2 | Cambiar la cuenta a 0098765432 sin tocar las fechas | Las fechas siguen mostrando 01/09/2026 y 30/09/2026 |
| 3 | Cambiar el formato a PDF | El formato PDF queda seleccionado |
| 4 | Tocar "Exportar" | Se descarga `movimientos_0098765432_2026-09-01_2026-09-30.pdf` |
| 5 | Abrir el PDF descargado | Muestra los 2 movimientos de la cuenta USD (1.500,00 y -49,99) y ninguno de la cuenta ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Lista de descargas con los dos archivos; screenshot del PDF |
| **Estado** | Pendiente |
| **Notas** | Detecta estado "pegado" del formulario (filtros viejos reutilizados). |

### CP-009 — Los extremos del rango son inclusivos

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango 05/09/2026 al 15/09/2026 incluye los movimientos de ambos extremos y excluye los de fechas vecinas |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 05/09/2026; Hasta 15/09/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 05/09/2026, Hasta 15/09/2026 y formato CSV | Los cuatro campos muestran los valores indicados |
| 2 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-05_2026-09-15.csv` |
| 3 | Leer las filas de datos del archivo | Hay exactamente 2 filas: `2026-09-05,Compra Supermercado Ñandú,-45320.75,1204679.75` y `2026-09-15,Transferencia a Pérez José,-200000.00,1004679.75` |
| 4 | Verificar que el movimiento del 01/09/2026 (Acreditación haberes) no está | No hay ninguna fila con fecha 2026-09-01 |
| 5 | Verificar que el movimiento del 30/09/2026 (Débito Servicio Luz) no está | No hay ninguna fila con fecha 2026-09-30 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del archivo abierto |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: extremos inclusivos, ver P-3]`. |

### CP-010 — Rango de un solo día con un movimiento

| Campo | Valor |
|---|---|
| **Título** | Verificar que con Desde = Hasta = 15/09/2026 se exporta únicamente el movimiento de ese día |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 15/09/2026; Hasta 15/09/2026; Formato XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 15/09/2026, Hasta 15/09/2026 y formato XLSX | Los cuatro campos muestran los valores indicados y no aparece error de validación |
| 2 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-15_2026-09-15.xlsx` |
| 3 | Abrir el archivo en Excel | La hoja tiene 1 fila de encabezado y 1 fila de datos |
| 4 | Leer la fila de datos | Contiene 15/09/2026, "Transferencia a Pérez José", -200.000,00 y 1.004.679,75 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la hoja abierta |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: desde = hasta es un rango válido, ver P-3]`. |

### CP-011 — Rango que cruza el fin de año

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango del 31/12/2025 al 02/01/2026 exporta ambos movimientos y se refleja correctamente en el nombre del archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2, CA-3 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 31/12/2025; Hasta 02/01/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 31/12/2025, Hasta 02/01/2026 y formato CSV | Los campos muestran los valores indicados y no hay error de validación |
| 2 | Tocar "Exportar" | Se descarga exactamente `movimientos_0012345678_2025-12-31_2026-01-02.csv` |
| 3 | Leer las filas de datos | Hay 2 filas: `2025-12-31,Pago Impuesto Sellos,-12000.00,512000.00` y `2026-01-02,Acreditación Reintegro,3500.00,515500.00` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Lista de descargas; screenshot del archivo abierto |
| **Estado** | Pendiente |
| **Notas** | Verifica también que dd/mm/aaaa del formulario no se invierte a mm/dd en el nombre ni en el filtro (31/12 no puede ser mes). |

### CP-012 — Rango máximo permitido (365 días)

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango de exactamente 365 días (01/10/2025 al 30/09/2026) se exporta correctamente |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/10/2025; Hasta 30/09/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 01/10/2025, Hasta 30/09/2026 y formato CSV | Los campos muestran los valores indicados y no aparece ningún error de rango |
| 2 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2025-10-01_2026-09-30.csv` |
| 3 | Leer la primera y la última fila de datos | La última fila es `2026-09-30,Débito Servicio Luz,-18450.25,986229.50`; ninguna fila tiene fecha anterior a 2025-10-01 ni posterior a 2026-09-30 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del formulario; archivo abierto |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: máximo 365 días corridos inclusive, ver P-3]`. Si el PO define otro máximo, ajustar las fechas de este caso y de CP-013. |

### CP-013 — Rango que excede el máximo en un día

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango de 366 días (30/09/2025 al 30/09/2026) es rechazado con mensaje y sin archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 30/09/2025; Hasta 30/09/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 30/09/2025, Hasta 30/09/2026 y formato CSV | Los campos muestran los valores indicados |
| 2 | Tocar "Exportar" | Se muestra el mensaje "El rango no puede superar los 365 días." |
| 3 | Revisar la carpeta de Descargas | No hay ningún archivo descargado |
| 4 | Revisar los campos del formulario | Los valores ingresados se conservan |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de Descargas vacía |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: máximo 365 días y texto del mensaje, ver P-3]`. |

### CP-014 — Exportar 1.000 movimientos en los tres formatos dentro del tiempo esperado

| Campo | Valor |
|---|---|
| **Título** | Verificar que la exportación de 1.000 movimientos inicia la descarga en 5 segundos o menos en CSV, XLSX y PDF |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; cuenta 0022222222 con 1.000 movimientos entre 01/08/2026 y 31/08/2026; cronómetro disponible; red estable sin throttling |
| **Datos de prueba** | Cuenta 0022222222; Desde 01/08/2026; Hasta 31/08/2026; Formatos CSV, XLSX y PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0022222222, Desde 01/08/2026, Hasta 31/08/2026 y formato CSV | Los campos muestran los valores indicados |
| 2 | Tocar "Exportar" y medir hasta que comienza la descarga | El archivo `movimientos_0022222222_2026-08-01_2026-08-31.csv` inicia la descarga en 5 s o menos |
| 3 | Contar las filas de datos del CSV | Hay 1.000 filas de datos más 1 de encabezado |
| 4 | Cambiar el formato a XLSX y tocar "Exportar" midiendo el tiempo | El archivo `movimientos_0022222222_2026-08-01_2026-08-31.xlsx` inicia la descarga en 5 s o menos |
| 5 | Contar las filas de datos del XLSX | Hay 1.000 filas de datos más 1 de encabezado |
| 6 | Cambiar el formato a PDF y tocar "Exportar" midiendo el tiempo | El archivo `movimientos_0022222222_2026-08-01_2026-08-31.pdf` inicia la descarga en 5 s o menos |
| 7 | Ir a la última página del PDF | La última fila corresponde al movimiento número 1.000 y no hay filas cortadas entre páginas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Tiempos medidos (cronómetro o pestaña Network de DevTools); screenshot de la última página del PDF |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: umbral <= 5 s para hasta 1.000 movimientos, ver P-1]`. Si el tiempo supera 5 s, registrar el valor medido. |

### CP-015 — Límite de movimientos por archivo (10.000 vs 10.001)

| Campo | Valor |
|---|---|
| **Título** | Verificar que 10.000 movimientos se exportan y 10.001 son rechazados con mensaje y sin archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; cuenta 0033333333 con 10.000 movimientos y cuenta 0044444444 con 10.001 movimientos entre 01/06/2026 y 30/06/2026; carpeta de Descargas vacía |
| **Datos de prueba** | Cuentas 0033333333 y 0044444444; Desde 01/06/2026; Hasta 30/06/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0033333333, Desde 01/06/2026, Hasta 30/06/2026 y formato CSV | Los campos muestran los valores indicados |
| 2 | Tocar "Exportar" | Se descarga `movimientos_0033333333_2026-06-01_2026-06-30.csv` |
| 3 | Contar las filas de datos | Hay 10.000 filas de datos más 1 de encabezado |
| 4 | Cambiar la cuenta a 0044444444 manteniendo fechas y formato | La cuenta 0044444444 queda seleccionada |
| 5 | Tocar "Exportar" | Se muestra "El período seleccionado supera el máximo de 10.000 movimientos. Reducí el rango de fechas." |
| 6 | Revisar la carpeta de Descargas | No existe ningún archivo `movimientos_0044444444_...` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; conteo de filas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: límite de 10.000 movimientos y texto del mensaje, ver P-4]`. Si el PO define que no hay límite, convertir en caso de performance con masa. |

### CP-016 — Rango sin movimientos muestra mensaje y no descarga archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango sin movimientos (julio 2026) muestra el mensaje de rango vacío y no descarga ningún archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; la cuenta 0012345678 no tiene movimientos entre 01/07/2026 y 31/07/2026; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/07/2026; Hasta 31/07/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 01/07/2026, Hasta 31/07/2026 y formato CSV | Los campos muestran los valores indicados y no aparece error de validación |
| 2 | Tocar "Exportar" | Se muestra el mensaje "No hay movimientos para el período seleccionado." |
| 3 | Revisar la carpeta de Descargas | No se descargó ningún archivo |
| 4 | Revisar los campos del formulario | Cuenta, fechas y formato conservan los valores ingresados |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje (paso 2); carpeta de Descargas vacía (paso 3) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: texto del mensaje y ausencia de descarga, ver P-2]`. Subset de humo. |

### CP-017 — Cuenta sin ningún movimiento histórico

| Campo | Valor |
|---|---|
| **Título** | Verificar que una cuenta sin movimientos muestra el mensaje de rango vacío al exportar en PDF |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; la cuenta 0011111111 no tiene ningún movimiento; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0011111111; Desde 01/09/2026; Hasta 30/09/2026; Formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0011111111, Desde 01/09/2026, Hasta 30/09/2026 y formato PDF | Los campos muestran los valores indicados |
| 2 | Tocar "Exportar" | Se muestra el mensaje "No hay movimientos para el período seleccionado." |
| 3 | Revisar la carpeta de Descargas | No se descargó ningún archivo (tampoco un PDF vacío) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de Descargas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: mismo mensaje y comportamiento que el rango vacío de una cuenta con movimientos, ver P-2]`. |

### CP-018 — Fecha Desde posterior a Hasta

| Campo | Valor |
|---|---|
| **Título** | Verificar que Desde 30/09/2026 y Hasta 01/09/2026 muestra error de validación y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 30/09/2026; Hasta 01/09/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 30/09/2026, Hasta 01/09/2026 y formato CSV | Los campos muestran los valores indicados |
| 2 | Tocar "Exportar" | Se muestra "La fecha Desde no puede ser posterior a la fecha Hasta." |
| 3 | Revisar la carpeta de Descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: texto del mensaje y bloqueo, ver P-3]`. Verificar que no se muestre el mensaje de "sin movimientos" en su lugar. |

### CP-019 — Fecha Hasta futura

| Campo | Valor |
|---|---|
| **Título** | Verificar que Hasta = 10/10/2026 (mañana) muestra error de validación y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; fecha de ejecución 09/10/2026 (si es otra, usar hoy + 1); carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/10/2026; Hasta 10/10/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678, Desde 01/10/2026, Hasta 10/10/2026 y formato CSV | Los campos muestran los valores indicados |
| 2 | Tocar "Exportar" | Se muestra "La fecha Hasta no puede ser futura." |
| 3 | Revisar la carpeta de Descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: no se permiten fechas futuras, ver P-3]`. Si el PO acepta fechas futuras, este caso pasa a exportar con los movimientos existentes. |

### CP-020 — Fecha inexistente ingresada manualmente

| Campo | Valor |
|---|---|
| **Título** | Verificar que ingresar Desde = 31/02/2026 muestra error de fecha inválida y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; el campo de fecha admite tipeo; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 31/02/2026; Hasta 28/02/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678 y el formato CSV | Cuenta y formato quedan seleccionados |
| 2 | Escribir 31/02/2026 en Desde | El campo recibe el texto |
| 3 | Escribir 28/02/2026 en Hasta | El campo muestra 28/02/2026 |
| 4 | Tocar "Exportar" | Se muestra "Ingresá una fecha válida." asociado al campo Desde |
| 5 | Revisar la carpeta de Descargas | No se descargó ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: campo de fecha admite tipeo en dd/mm/aaaa y valida fechas inexistentes, ver P-3]`. Si el campo es solo calendario, el caso queda "No aplicable". |

### CP-021 — Exportar con fechas vacías

| Campo | Valor |
|---|---|
| **Título** | Verificar que "Exportar" con Desde y Hasta vacíos muestra los mensajes de campo obligatorio y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde vacío; Hasta vacío; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta 0012345678 y el formato CSV dejando Desde y Hasta vacíos | Cuenta y formato seleccionados; fechas vacías |
| 2 | Tocar "Exportar" | Se muestran "Ingresá la fecha Desde." y "Ingresá la fecha Hasta." junto a cada campo |
| 3 | Revisar la carpeta de Descargas | No se descargó ningún archivo |
| 4 | Ingresar solo Desde = 01/09/2026 y tocar "Exportar" | Se muestra "Ingresá la fecha Hasta." y no se descarga archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de los mensajes (pasos 2 y 4) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: campos obligatorios y textos, ver P-3]`. |

### CP-022 — Exportar sin seleccionar cuenta ni formato

| Campo | Valor |
|---|---|
| **Título** | Verificar que "Exportar" sin cuenta ni formato seleccionados muestra los mensajes de campo obligatorio y no genera archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; pantalla "Movimientos" recién abierta, sin cuenta ni formato preseleccionados; carpeta de Descargas vacía |
| **Datos de prueba** | Desde 01/09/2026; Hasta 30/09/2026; cuenta y formato sin seleccionar |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar Desde = 01/09/2026 | El campo muestra 01/09/2026 |
| 2 | Ingresar Hasta = 30/09/2026 | El campo muestra 30/09/2026 |
| 3 | Tocar "Exportar" | Se muestran "Seleccioná una cuenta." y "Seleccioná un formato." |
| 4 | Revisar la carpeta de Descargas | No se descargó ningún archivo |
| 5 | Seleccionar la cuenta 0012345678 y tocar "Exportar" | Desaparece el mensaje de cuenta, persiste "Seleccioná un formato." y no se descarga archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de los mensajes (pasos 3 y 5) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: no hay cuenta ni formato preseleccionados y ambos son obligatorios, ver P-3]`. Si hay preselección, el caso pasa a "No aplicable". |

### CP-023 — Intento de exportar una cuenta de otro cliente

| Campo | Valor |
|---|---|
| **Título** | Verificar que un cliente no puede exportar los movimientos de una cuenta ajena manipulando el request |
| **Módulo** | Home banking / Movimientos / Exportación (API) |
| **Origen** | HU-202 · CA-1 (seguridad: dinero y datos personales) |
| **Tipo** | No funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; la cuenta 0077777777 pertenece a `qa.cliente02`; la cuenta 0099999999 no existe; DevTools o cliente HTTP disponible |
| **Datos de prueba** | Cuenta propia 0012345678; cuenta ajena 0077777777; cuenta inexistente 0099999999; Desde 01/09/2026; Hasta 30/09/2026; Formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el selector de cuentas de "Movimientos" | Solo se listan las cuentas de `qa.cliente01`; 0077777777 no aparece |
| 2 | Exportar la cuenta 0012345678 y capturar el request en DevTools | Se captura el request de exportación con el identificador de la cuenta |
| 3 | Reenviar el request cambiando la cuenta por 0077777777 | La respuesta es 403 sin archivo adjunto |
| 4 | Revisar el cuerpo de la respuesta del paso 3 | No contiene movimientos, nombre del titular ni stack trace |
| 5 | Reenviar el request cambiando la cuenta por 0099999999 | La respuesta es idéntica en código y cuerpo a la del paso 3 (no revela si la cuenta existe) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Request y response de los pasos 3 y 5 (HAR o captura de DevTools) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: cuenta no propia responde 403 sin diferenciar inexistente, ver P-7]`. Anti-enumeración de cuentas. |

### CP-024 — Exportar sin sesión válida

| Campo | Valor |
|---|---|
| **Título** | Verificar que con la sesión expirada o sin cookie de sesión no se genera ni descarga ningún archivo |
| **Módulo** | Home banking / Movimientos / Exportación (sesión) |
| **Origen** | HU-202 · CA-1 (seguridad) |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01` en "Movimientos" con el formulario completo (cuenta 0012345678, 01/09/2026 al 30/09/2026, CSV); carpeta de Descargas vacía |
| **Datos de prueba** | Datos del formulario de CP-001; cliente HTTP para el paso 4 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Invalidar la sesión (borrar la cookie de sesión desde DevTools o cerrar la sesión en otra pestaña) | La sesión deja de ser válida |
| 2 | En la pestaña con el formulario, tocar "Exportar" | Se redirige al login o se muestra el aviso de sesión expirada |
| 3 | Revisar la carpeta de Descargas | No se descargó ningún archivo |
| 4 | Enviar con un cliente HTTP el mismo request de exportación sin cookie de sesión | La respuesta es 401 sin datos de movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la redirección (paso 2); response del paso 4 |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: sin sesión válida el servidor responde 401, ver P-7]`. |

### CP-025 — Validaciones replicadas en el servidor (formato, fecha futura y rango excesivo)

| Campo | Valor |
|---|---|
| **Título** | Verificar que el servidor rechaza requests con formato inválido, fecha futura o rango superior al máximo aunque el front no lo permita |
| **Módulo** | Home banking / Movimientos / Exportación (API) |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; cliente HTTP con la cookie de sesión; request válido de exportación de CP-001 como plantilla |
| **Datos de prueba** | (a) formato `docx`; (b) hasta `2099-12-31`; (c) desde `2020-01-01` y hasta `2026-09-30` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Enviar el request de CP-001 con formato `docx` | Respuesta 400 sin archivo y sin detalles técnicos internos |
| 2 | Enviar el request de CP-001 con hasta `2099-12-31` | Respuesta 400 sin archivo |
| 3 | Enviar el request de CP-001 con desde `2020-01-01` y hasta `2026-09-30` | Respuesta 400 sin archivo |
| 4 | Enviar el request de CP-001 sin ninguna modificación | Respuesta 200 con el archivo CSV (control) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Request y response de cada paso |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: códigos 400 y reglas de P-3; las validaciones del front no son confiables]`. |

### CP-026 — Descripciones con fórmulas y HTML (inyección en el archivo)

| Campo | Valor |
|---|---|
| **Título** | Verificar que descripciones que empiezan con `=`, `+` o `@` no se ejecutan como fórmula en CSV/XLSX y que el HTML se muestra como texto en el PDF |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 (seguridad: datos controlados por terceros) |
| **Tipo** | No funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; cuenta 0055555555 con los 4 movimientos del 12/09/2026 del dataset; Microsoft Excel instalado; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0055555555; Desde 12/09/2026; Hasta 12/09/2026; descripciones `=1+1`, `+1+1`, `@SUM(1+1)`, `<script>alert(1)</script>` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Exportar la cuenta 0055555555 del 12/09/2026 al 12/09/2026 en CSV | Se descarga `movimientos_0055555555_2026-09-12_2026-09-12.csv` |
| 2 | Abrir el CSV en un editor de texto | Las descripciones de las filas 2 a 4 empiezan con el prefijo `'` (`'=1+1`, `'+1+1`, `'@SUM(1+1)`) |
| 3 | Abrir el CSV en Excel | Las celdas de descripción muestran el texto literal y ninguna muestra el resultado 2 |
| 4 | Exportar la misma cuenta y fechas en XLSX y abrir en Excel | Las celdas de descripción de las 3 primeras filas son de tipo texto y muestran el texto literal |
| 5 | Exportar la misma cuenta y fechas en PDF y abrir | La cuarta descripción se muestra como el texto literal `<script>alert(1)</script>` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de Excel (pasos 3 y 4) y del PDF (paso 5) |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: neutralización con prefijo ', ver P-7]`. Si el PO define otra mitigación, ajustar el resultado esperado del paso 2. No habilitar la edición/macros si Excel muestra una advertencia, y registrar la advertencia. |

### CP-027 — Descripciones con comas, comillas, ñ, acentos y emoji en el CSV

| Campo | Valor |
|---|---|
| **Título** | Verificar que el CSV escapa comas y comillas y conserva ñ, acentos y emoji sin romper las columnas |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; cuenta 0055555555 con los 2 movimientos del 13/09/2026 del dataset; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0055555555; Desde 13/09/2026; Hasta 13/09/2026; Formato CSV; descripciones `Pago "Kiosco", S.A.` y `Café Ñandú ☕ – Año Nuevo` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Exportar la cuenta 0055555555 del 13/09/2026 al 13/09/2026 en CSV | Se descarga `movimientos_0055555555_2026-09-13_2026-09-13.csv` |
| 2 | Abrir el archivo con un editor de texto | La fila 2 es `2026-09-13,"Pago ""Kiosco"", S.A.",-1500.00,97500.00` |
| 3 | Leer la fila 3 | La fila 3 es `2026-09-13,Café Ñandú ☕ – Año Nuevo,-2300.00,95200.00` con ñ, acentos, emoji y guion largo legibles |
| 4 | Importar el archivo con un parser CSV (por ejemplo, Python `csv.reader`) | Cada fila se parsea en exactamente 4 columnas |
| 5 | Leer la descripción parseada de la fila 2 | El valor es `Pago "Kiosco", S.A.` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del archivo; salida del parser |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: CSV RFC 4180, UTF-8 con BOM, ver P-6]`. |

### CP-028 — Descripción de 200 caracteres en el PDF

| Campo | Valor |
|---|---|
| **Título** | Verificar que una descripción de 200 caracteres no se corta ni se superpone con otras columnas en el PDF |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; cuenta 0055555555 con un movimiento del 14/09/2026 de -5.000,00 (saldo 90.200,00) cuya descripción es el texto de Datos de prueba; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0055555555; Desde 14/09/2026; Hasta 14/09/2026; Formato PDF; descripción (200 caracteres): `Pago factura A-0001-00001234 a proveedor Servicios Integrales de Mantenimiento y Limpieza Ñuñoa S.R.L. por mantenimiento preventivo del edificio central, período agosto 2026, ref. contrato 2026-045789` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Exportar la cuenta 0055555555 del 14/09/2026 al 14/09/2026 en PDF | Se descarga `movimientos_0055555555_2026-09-14_2026-09-14.pdf` |
| 2 | Abrir el PDF y leer la descripción | El texto completo de 200 caracteres es legible hasta `2026-045789` |
| 3 | Revisar las columnas importe y saldo de esa fila | Muestran -5.000,00 y 90.200,00 sin superponerse con la descripción |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del PDF |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: la descripción se ajusta en varias líneas sin truncarse]`. Si el producto define truncado, ajustar el resultado esperado. |

### CP-029 — Falla del servicio de generación (error 500)

| Campo | Valor |
|---|---|
| **Título** | Verificar que ante un error 500 del servicio de exportación se muestra un mensaje genérico, no se descarga archivo y se puede reintentar |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 (manejo de errores) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; el servicio de generación configurado en QA para responder 500 (mock o apagado); carpeta de Descargas vacía |
| **Datos de prueba** | Datos del formulario de CP-001 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Completar el formulario con los datos de CP-001 | El formulario queda completo |
| 2 | Tocar "Exportar" | Se muestra "No pudimos generar el archivo. Intentá nuevamente en unos minutos." |
| 3 | Revisar el mensaje | No contiene stack trace, códigos internos ni nombres de servidores |
| 4 | Revisar la carpeta de Descargas | No se descargó ningún archivo (ni parcial ni de 0 bytes) |
| 5 | Restaurar el servicio y tocar "Exportar" otra vez | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` con 4 movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; response 500 en DevTools; carpeta de Descargas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: texto del mensaje y reintento posible, ver P-8]`. |

### CP-030 — Pérdida de conexión durante la generación

| Campo | Valor |
|---|---|
| **Título** | Verificar que si se corta la red al tocar "Exportar" se informa el error y no queda un archivo corrupto |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 (manejo de errores) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; navegador con DevTools; cuenta 0022222222 (1.000 movimientos) para que la generación demore; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0022222222; Desde 01/08/2026; Hasta 31/08/2026; Formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Completar el formulario con los datos indicados | El formulario queda completo |
| 2 | Tocar "Exportar" | Comienza la generación |
| 3 | Poner el navegador en modo Offline en DevTools | La conexión se corta |
| 4 | Esperar 10 segundos | Se muestra "No hay conexión. Verificá tu red e intentá nuevamente." |
| 5 | Revisar la carpeta de Descargas | No hay archivo, ni parcial (`.crdownload`) ni de 0 bytes |
| 6 | Volver a modo Online y tocar "Exportar" | Se descarga `movimientos_0022222222_2026-08-01_2026-08-31.pdf` completo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de Descargas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: texto del mensaje, ver P-8]`. Si la generación termina antes de poder cortar la red, usar throttling Slow 3G previo. |

### CP-031 — Doble clic en "Exportar"

| Campo | Valor |
|---|---|
| **Título** | Verificar que un doble clic rápido en "Exportar" produce una sola descarga |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; carpeta de Descargas vacía; formulario completo con los datos de CP-001 |
| **Datos de prueba** | Datos de CP-001 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Hacer doble clic en "Exportar" (dos clics con menos de 300 ms de diferencia) | Comienza una única generación y el botón queda deshabilitado mientras dura |
| 2 | Esperar a que termine la descarga | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` |
| 3 | Revisar la carpeta de Descargas | Hay un solo archivo y no existe `movimientos_0012345678_2026-09-01_2026-09-30 (1).csv` |
| 4 | Revisar la pestaña Network de DevTools | Se registró un solo request de exportación |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Carpeta de Descargas; lista de requests en Network |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: el botón se deshabilita durante la generación, ver P-8]`. |

### CP-032 — Recargar la página durante la generación

| Campo | Valor |
|---|---|
| **Título** | Verificar que recargar la pantalla mientras se genera el archivo no deja archivos parciales ni duplica exportaciones |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 (manejo de errores) |
| **Tipo** | Excepción |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01`; DevTools con throttling "Slow 3G"; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0022222222; Desde 01/08/2026; Hasta 31/08/2026; Formato XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Completar el formulario con los datos indicados | El formulario queda completo |
| 2 | Tocar "Exportar" | Comienza la generación |
| 3 | Presionar F5 antes de que termine | La pantalla "Movimientos" se recarga con la sesión activa |
| 4 | Esperar 30 segundos | No se descarga ningún archivo automáticamente |
| 5 | Revisar la carpeta de Descargas | No hay archivos parciales ni duplicados |
| 6 | Repetir la exportación completando el formulario | Se descarga `movimientos_0022222222_2026-08-01_2026-08-31.xlsx` completo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Carpeta de Descargas; screenshot de la pantalla recargada |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: una exportación interrumpida por recarga se descarta y no se reanuda, ver P-8]`. |

### CP-033 — Exportaciones simultáneas del mismo cliente en dos sesiones

| Campo | Valor |
|---|---|
| **Título** | Verificar que dos sesiones del mismo cliente exportando cuentas distintas a la vez reciben cada una su archivo correcto |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2 |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | `qa.cliente01` con sesión en Chrome (sesión A) y en Firefox (sesión B); carpetas de Descargas de ambos navegadores vacías |
| **Datos de prueba** | Sesión A: cuenta 0012345678, CSV, 01/09/2026 al 30/09/2026. Sesión B: cuenta 0098765432, PDF, 01/09/2026 al 30/09/2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En la sesión A, completar el formulario con sus datos | Formulario de A completo |
| 2 | En la sesión B, completar el formulario con sus datos | Formulario de B completo |
| 3 | Tocar "Exportar" en A y en B con menos de 2 segundos de diferencia | Ambas sesiones inician la generación |
| 4 | Revisar la descarga de A | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` con 4 movimientos de la cuenta ARS |
| 5 | Revisar la descarga de B | Se descarga `movimientos_0098765432_2026-09-01_2026-09-30.pdf` con 2 movimientos de la cuenta USD |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Descargas de ambos navegadores; screenshot de ambos archivos |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: se permiten sesiones concurrentes del mismo cliente, ver P-8]`. Si hay política de sesión única, el caso queda "No aplicable". |

### CP-034 — Descarga del PDF desde Chrome en Android

| Campo | Valor |
|---|---|
| **Título** | Verificar que en Chrome (última versión estable) sobre Android se exporta y descarga el PDF con el nombre correcto |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-3 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Dispositivo Android 14 con Chrome última versión estable; sesión iniciada como `qa.cliente01` |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/09/2026; Hasta 30/09/2026; Formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir "Movimientos" y completar el formulario con los datos indicados | El formulario se ve completo y sin elementos cortados ni superpuestos |
| 2 | Tocar "Exportar" | Chrome muestra la notificación de descarga de `movimientos_0012345678_2026-09-01_2026-09-30.pdf` |
| 3 | Abrir el archivo desde la notificación | El PDF abre y muestra 4 movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de cada paso en el dispositivo |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: Chrome móvil es plataforma soportada, ver S-27]`. |

### CP-035 — Accesibilidad por teclado y del mensaje de rango vacío

| Campo | Valor |
|---|---|
| **Título** | Verificar que el flujo de exportación se completa solo con teclado y que el mensaje de rango vacío es anunciado por un lector de pantalla |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-4 |
| **Tipo** | No funcional |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada como `qa.cliente01` en Chrome de escritorio; lector de pantalla NVDA activo; carpeta de Descargas vacía |
| **Datos de prueba** | Cuenta 0012345678; Desde 01/07/2026; Hasta 31/07/2026; Formato CSV (rango vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Con la tecla Tab, recorrer los controles de "Movimientos" | El foco pasa en orden por cuenta, desde, hasta, formato y "Exportar", con foco visible en cada uno |
| 2 | Seleccionar cuenta y formato con teclado e ingresar las fechas indicadas | Los cuatro campos quedan completos |
| 3 | Presionar Enter sobre "Exportar" | Se activa la exportación |
| 4 | Escuchar la salida de NVDA | NVDA anuncia "No hay movimientos para el período seleccionado." sin necesidad de mover el foco |
| 5 | Revisar el contraste del texto del mensaje | La relación de contraste es de al menos 4,5:1 |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Grabación de audio o transcripción de NVDA; medición de contraste |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: el producto apunta a WCAG 2.1 AA, ver S-28]`. |

### CP-036 — Exploratorio: abrir el CSV en Excel con configuración regional es-AR

| Campo | Valor |
|---|---|
| **Título** | Verificar que el CSV exportado se abre en Excel (es-AR) con columnas separadas, caracteres legibles e importes numéricos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | Exploratorio (objetivo de la HU: conciliar con sistema contable) |
| **Tipo** | No funcional |
| **Prioridad** | Alta |
| **Precondiciones** | CP-001 ejecutado con éxito; Windows con configuración regional "Español (Argentina)" (separador de lista `;`, decimal `,`); Microsoft Excel instalado |
| **Datos de prueba** | Archivo `movimientos_0012345678_2026-09-01_2026-09-30.csv` de CP-001 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el archivo con doble clic desde el Explorador de archivos | Excel abre el archivo |
| 2 | Observar el encabezado | Se ven 4 columnas separadas: Fecha, Descripción, Importe (ARS), Saldo (ARS) |
| 3 | Observar la descripción de la fila 3 | "Compra Supermercado Ñandú" se ve con la Ñ y los acentos correctos |
| 4 | Observar la celda de importe de la fila 3 | Se interpreta como número -45.320,75 alineado a la derecha y no como texto ni como fecha |
| 5 | Registrar cualquier desvío observado | Se documentan los desvíos con screenshot |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de Excel con el archivo abierto |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: criterio de aprobación de los pasos 2 a 4, porque la HU no define el CSV para Excel regional, ver P-6]`. Con separador coma y punto decimal en un Excel es-AR es probable que las columnas no se separen: si falla, reportar como defecto de diseño para P-6. |

### CP-037 — Exploratorio: registro de auditoría de la exportación

| Campo | Valor |
|---|---|
| **Título** | Verificar que cada exportación genera un registro de auditoría con usuario, cuenta, rango, formato y fecha/hora, sin el contenido de los movimientos |
| **Módulo** | Home banking / Movimientos / Exportación (auditoría) |
| **Origen** | Exploratorio (seguridad: dinero y datos personales) |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | CP-001 ejecutado con éxito; QA con acceso de lectura al registro de auditoría de QA |
| **Datos de prueba** | Exportación de CP-001 (usuario `qa.cliente01`, cuenta 0012345678, 01/09/2026 al 30/09/2026, CSV) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Buscar en el registro de auditoría las entradas de `qa.cliente01` posteriores a CP-001 | Existe exactamente 1 entrada de exportación |
| 2 | Revisar los campos de la entrada | Contiene usuario `qa.cliente01`, cuenta 0012345678, rango 2026-09-01 a 2026-09-30, formato CSV y fecha y hora de la acción |
| 3 | Buscar en la entrada y en los logs de aplicación el texto "Acreditación haberes" | No aparece el contenido de los movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la entrada de auditoría; búsqueda de logs vacía |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: la exportación se audita sin contenido, ver P-7]`. Caso exploratorio: el resultado esperado depende de la respuesta del PO. |

## 4. Priorización por riesgo

Matriz de F5 (probabilidad del defecto × impacto si falla).

| Caso | Prob. | Impacto | Prioridad | Humo | Justificación breve |
|---|---|---|---|---|---|
| CP-001 | Media | Alto | Alta | Sí | Flujo central CSV; sin él no hay feature |
| CP-002 | Media | Alto | Alta | Sí | Flujo central XLSX |
| CP-003 | Media | Alto | Alta | Sí | Flujo central PDF |
| CP-004 | Media | Alto | Alta | No | Moneda equivocada en dinero |
| CP-005 | Media | Alto | Alta | No | Importes y saldos erróneos rompen la conciliación |
| CP-006 | Media | Alto | Alta | No | Importes como texto rompen la conciliación |
| CP-007 | Media | Medio | Media | No | Contenido de PDF |
| CP-008 | Media | Medio | Media | No | Estado del formulario |
| CP-009 | Alta | Alto | Alta | No | Off-by-one en fechas muy probable y deja movimientos fuera |
| CP-010 | Media | Medio | Media | No | Borde desde = hasta |
| CP-011 | Media | Medio | Media | No | Borde de año / dd-mm |
| CP-012 | Media | Medio | Media | No | Borde de máximo de rango |
| CP-013 | Media | Medio | Media | No | Borde de máximo + 1 |
| CP-014 | Media | Medio | Media | No | Performance de la operación típica |
| CP-015 | Baja | Medio | Media | No | Límite de filas (supuesto) |
| CP-016 | Alta | Medio | Alta | Sí | CA-4: es probable que se genere un archivo vacío |
| CP-017 | Media | Bajo | Baja | No | Variante poco frecuente de CA-4 |
| CP-018 | Media | Medio | Media | No | Validación de rango invertido |
| CP-019 | Media | Bajo | Baja | No | Validación de fecha futura |
| CP-020 | Media | Bajo | Baja | No | Fecha inexistente |
| CP-021 | Media | Bajo | Baja | No | Campos obligatorios |
| CP-022 | Media | Bajo | Baja | No | Campos obligatorios |
| CP-023 | Media | Alto | Alta | No | Fuga de movimientos de terceros |
| CP-024 | Baja | Alto | Media | No | Sesión inválida |
| CP-025 | Media | Medio | Media | No | Validación solo en cliente |
| CP-026 | Media | Alto | Alta | No | Inyección de fórmulas en Excel del cliente |
| CP-027 | Alta | Medio | Alta | No | Comas y comillas rompen el CSV con frecuencia |
| CP-028 | Media | Bajo | Baja | No | Estética del PDF |
| CP-029 | Media | Medio | Media | No | Error del servicio |
| CP-030 | Baja | Medio | Media | No | Red caída |
| CP-031 | Media | Medio | Media | No | Doble envío |
| CP-032 | Baja | Bajo | Baja | No | Recarga durante generación |
| CP-033 | Baja | Medio | Media | No | Concurrencia |
| CP-034 | Media | Medio | Media | No | Compatibilidad móvil |
| CP-035 | Media | Bajo | Baja | No | Accesibilidad |
| CP-036 | Alta | Medio | Alta | No | CSV con coma/punto en Excel es-AR |
| CP-037 | Baja | Medio | Media | No | Auditoría |

**Resumen:** Alta = 12 (CP-001, 002, 003, 004, 005, 006, 009, 016, 023, 026, 027, 036); Media = 17; Baja = 8. Total = 37.

**Subset de humo (4 casos):** CP-001 (CSV), CP-002 (XLSX), CP-003 (PDF) y CP-016 (rango vacío, CA-4).

**Orden de ejecución sugerido:**

1. Humo: CP-001, CP-002, CP-003, CP-016
2. Alta: CP-004, CP-005, CP-006, CP-009, CP-023, CP-026, CP-027, CP-036
3. Media: CP-007, CP-008, CP-010, CP-011, CP-012, CP-013, CP-014, CP-015, CP-018, CP-024, CP-025, CP-029, CP-030, CP-031, CP-033, CP-034, CP-037
4. Baja: CP-017, CP-019, CP-020, CP-021, CP-022, CP-028, CP-032, CP-035

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Seleccionar cuenta, rango de fechas y formato y tocar "Exportar" | CP-001, 002, 003, 004, 008, 009, 010, 012, 013, 018, 019, 020, 021, 022, 023, 024, 025, 029, 030, 031, 032, 033, 034, 035 | ✓ Cubierta |
| CA-2 | Archivo generado rápidamente con fecha, descripción, importe y saldo del período | CP-001, 002, 003, 004, 005, 006, 007, 009, 010, 011, 014, 015, 026, 027, 028, 033 | ✓ Cubierta |
| CA-3 | Nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>` | CP-001, 002, 003, 004, 008, 011, 034 | ✓ Cubierta |
| CA-4 | Mensaje si el rango no tiene movimientos | CP-016, 017, 035 | ✓ Cubierta |

- **Cobertura: 4 de 4 CAs = 100 %.** No hay CAs sin cubrir.
- Casos con origen exploratorio (sin CA directo): CP-036 y CP-037.
- Nota del equipo (moneda ARS/USD): CP-004, CP-005, CP-007, CP-008, CP-033.

**Cobertura del piso mínimo por entrada de datos:**

| Entrada | Positivo | Negativo | Borde |
|---|---|---|---|
| Cuenta | CP-001, CP-004 | CP-022, CP-023, CP-025 | CP-017 (sin movimientos), CP-015 (máxima masa) |
| Desde | CP-001 | CP-018, CP-020, CP-021 | CP-009, CP-010, CP-011, CP-012 |
| Hasta | CP-001 | CP-019, CP-021, CP-025 | CP-009, CP-010, CP-013 |
| Formato | CP-001, CP-002, CP-003 | CP-022, CP-025 | CP-002 / CP-003 (los tres valores de la partición) |

## 6. Supuestos asumidos

| ID | Supuesto | Pregunta | Casos |
|---|---|---|---|
| S-1 | El archivo debe empezar a descargarse en <= 5 s para hasta 1.000 movimientos y los tres formatos | P-1 | CP-014 |
| S-2 | El mensaje de rango vacío es "No hay movimientos para el período seleccionado." | P-2 | CP-016, 017, 035 |
| S-3 | En rango vacío no se genera ni descarga ningún archivo y los filtros se conservan | P-2 | CP-016, 017 |
| S-4 | Cuenta, desde, hasta y formato son obligatorios y no hay preselección; textos de los mensajes de obligatoriedad | P-3 | CP-021, 022 |
| S-5 | Los extremos del rango son inclusivos | P-3 | CP-009 |
| S-6 | desde = hasta es un rango válido | P-3 | CP-010 |
| S-7 | desde > hasta se rechaza con "La fecha Desde no puede ser posterior a la fecha Hasta." | P-3 | CP-018 |
| S-8 | hasta no puede ser futura; mensaje "La fecha Hasta no puede ser futura." | P-3 | CP-019, 025 |
| S-9 | Rango máximo de 365 días corridos inclusive; mensaje "El rango no puede superar los 365 días." | P-3 | CP-012, 013, 025 |
| S-10 | Los campos de fecha admiten tipeo en dd/mm/aaaa y rechazan fechas inexistentes con "Ingresá una fecha válida." | P-3 | CP-020 |
| S-11 | Máximo de 10.000 movimientos por archivo; mensaje "El período seleccionado supera el máximo de 10.000 movimientos. Reducí el rango de fechas." | P-4 | CP-015 |
| S-12 | `<cuenta>` es el número de cuenta de 10 dígitos sin separadores | P-5 | CP-001 al 004, 008, 009 al 015 |
| S-13 | `<desde>` y `<hasta>` en el nombre van como aaaa-mm-dd y la extensión en minúsculas | P-5 | CP-001 al 004, 011 |
| S-14 | Columnas `Fecha`, `Descripción`, `Importe (<MON>)`, `Saldo (<MON>)`, en ese orden | P-6 | CP-004, 005, 006 |
| S-15 | La moneda se indica en los encabezados y no hay conversión a otra moneda | P-6 | CP-004, 005 |
| S-16 | Orden cronológico ascendente | P-6 | CP-005, 009, 011 |
| S-17 | CSV: UTF-8 con BOM, separador coma, fecha aaaa-mm-dd, punto decimal con 2 decimales, sin separador de miles, débitos negativos, RFC 4180 | P-6 | CP-005, 027 |
| S-18 | XLSX: una hoja, encabezado en fila 1, fecha tipo fecha, importes/saldos numéricos con 2 decimales | P-6 | CP-002, 006, 010 |
| S-19 | PDF: encabezado con cuenta, moneda y período; importes formato es-AR; descripciones largas se ajustan en varias líneas | P-6 | CP-007, 028 |
| S-20 | Criterio de aprobación de CP-036 (columnas, caracteres e importes legibles en Excel es-AR) | P-6 | CP-036 |
| S-21 | Solo el titular puede exportar sus cuentas; una cuenta no propia responde 403 sin diferenciar si existe | P-7 | CP-023 |
| S-22 | Sin sesión válida el servidor responde 401 y el front redirige al login o avisa sesión expirada | P-7 | CP-024 |
| S-23 | Las descripciones que empiezan con `=`, `+`, `-` o `@` se neutralizan con prefijo `'` en CSV/XLSX | P-7 | CP-026 |
| S-24 | Cada exportación se audita (usuario, cuenta, rango, formato, fecha/hora) sin el contenido | P-7 | CP-037 |
| S-25 | Texto del error del servicio "No pudimos generar el archivo. Intentá nuevamente en unos minutos."; el reintento es posible | P-8 | CP-029 |
| S-26 | Sin red se muestra "No hay conexión. Verificá tu red e intentá nuevamente."; "Exportar" se deshabilita mientras se genera; una exportación interrumpida por recarga no se reanuda; se permiten sesiones concurrentes del mismo cliente; el servidor responde 400 a requests inválidos | P-8 | CP-025, 030, 031, 032, 033 |
| S-27 | Navegadores y dispositivos soportados incluyen Chrome móvil en Android (MENOR) | (sin pregunta) | CP-034 |
| S-28 | Se espera accesibilidad nivel WCAG 2.1 AA (MENOR) | (sin pregunta) | CP-035 |
| S-29 | Cotitulares, apoderados y cuentas cerradas o bloqueadas quedan fuera de alcance de esta suite | P-7 | (sin casos) |
| S-30 | La exportación es una descarga directa: no hay envío por email ni historial de exportaciones (alcance negativo, MENOR) | (sin pregunta) | (sin casos) |

## 7. Auto-revisión

**Críticos**

- [x] **Cada CA tiene >= 1 caso**: CA-1, CA-2, CA-3 y CA-4 cubiertos (sección 5).
- [x] **Cero comportamiento inventado**: todo resultado no definido por la HU (textos de mensajes, límites, formato de contenido, códigos HTTP, auditoría) lleva `[SUPUESTO]` o el caso es exploratorio (CP-036 y CP-037); consolidado en la sección 6.
- [x] **Pasos reproducibles por terceros**: pasos atómicos con cuentas, fechas, formatos y valores exactos del dataset de referencia.
- [x] **Resultados esperados observables**: cada paso indica archivo, nombre, fila, mensaje o código de respuesta concreto.
- [x] **IDs únicos y secuenciales**: CP-001 a CP-037, sin huecos.
- [x] **Matriz de cobertura completa**: 4/4 = 100 %, verificada contra los casos listados.
- [x] **Preguntas al PO <= 8**: 8 preguntas (P-1 a P-8), todas con default propuesto, ninguna trivial.

**Observaciones**

- [x] Hay negativos, bordes y excepciones por funcionalidad con riesgo: 9 casos positivos/funcionales (CP-001 al 008 y CP-016) frente a 28 negativos, bordes, excepciones y no funcionales.
- [x] Prioridades derivadas de la matriz probabilidad × impacto (sección 4).
- [x] Subset de humo marcado: CP-001, CP-002, CP-003 y CP-016.
- [x] Sin casos duplicados: CP-016 (rango vacío con cuenta con datos) y CP-017 (cuenta sin movimientos, PDF) difieren en partición de datos y formato; CP-001 verifica descarga/nombre y CP-005 el contenido.
- [x] Dependencias entre casos declaradas en Precondiciones (CP-005, 006, 007, 008, 036, 037).
- [x] Supuestos consolidados en la sección 6.
- Observación conocida: CP-036 y CP-037 son exploratorios y su criterio depende de la respuesta del PO; CP-020 y CP-022 pueden quedar "No aplicable" según el diseño real del formulario (tipeo de fechas, preselección).
- Observación conocida: las validaciones de rango (CP-012, 013, 019) y el límite de 10.000 filas (CP-015) dependen por completo de las respuestas a P-3 y P-4; se ajustan con los valores que defina el PO.

**Resultado del gate:** sin fallas críticas; suite entregable.
