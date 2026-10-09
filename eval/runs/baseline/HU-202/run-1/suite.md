# Suite de pruebas — HU-202: Exportación de movimientos de cuenta

## 1. Resumen del análisis

**F0 — Validación de entrada**: el texto es una HU con 4 criterios de aceptación; no hay contradicciones entre CAs. Se ejecuta en modo completo (F3): hay CAs suficientes y ningún gap es BLOQUEANTE para el happy path.

| Elemento | Detalle |
|---|---|
| **Rol** | Cliente de home banking |
| **Funcionalidad** | Exportar los movimientos de una cuenta, en un rango de fechas, en formato CSV, XLSX o PDF, desde la pantalla "Movimientos" |
| **Objetivo de negocio** | Conciliar los movimientos con el sistema contable del cliente (implica que el contenido debe ser exacto, parseable y completo) |
| **Entidades y datos** | Cliente autenticado; Cuenta (ARS o USD); Movimiento (fecha, descripción, importe, saldo); Rango de fechas (desde/hasta); Formato (CSV/XLSX/PDF); Archivo exportado (`movimientos_<cuenta>_<desde>_<hasta>.<ext>`) |

**Criterios de aceptación (textuales)**

- **CA-1**: Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar".
- **CA-2**: El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo.
- **CA-3**: El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`.
- **CA-4**: Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado.
- **Nota del equipo**: los importes se muestran en la moneda de la cuenta (ARS o USD).

**Gaps detectados (F2, clasificación)**

| Gap | Categoría | Clase |
|---|---|---|
| CA-2 "rápidamente" no es verificable (sin umbral) | A | IMPORTANTE |
| CA-4 "mensaje adecuado": sin texto ni definición de si se descarga un archivo vacío | A / C | IMPORTANTE |
| CA-3: qué es `<cuenta>` (número, CBU, alias) y el formato de `<desde>`/`<hasta>` | B | IMPORTANTE |
| Límites del rango: inclusivo/exclusivo, máximo, futuro, desde > hasta; obligatoriedad y formato de fecha | B | IMPORTANTE |
| Contenido del archivo: columnas, encabezados, formato de importes y fechas, encoding, moneda dentro del archivo (la nota solo dice que "se muestran" en la moneda de la cuenta) | B | IMPORTANTE |
| Semántica del saldo, orden, movimientos no contabilizados y volumen máximo | B / E | IMPORTANTE |
| Permisos: solo cuentas propias, cuentas cerradas, descarga autenticada, inyección de fórmulas en CSV/XLSX | D / F | IMPORTANTE |
| Errores de generación/red, doble click, sesión expirada, canal soportado | C / G / J | IMPORTANTE |
| El objetivo "conciliar" exige exactitud del contenido pero los CAs no definen ejemplos de formato | A | MENOR (queda cubierto con supuestos de P-1) |

No hay gaps BLOQUEANTES: se generan casos con `[SUPUESTO: ...]` explícito para todo lo no definido.

## 2. Preguntas para el PO

Ninguna es BLOQUEANTE. Ordenadas por impacto en el diseño de casos.

**P-1. [B. Datos y validaciones] ¿Qué formato de contenido tiene el archivo? Propuesta cerrada: columnas `Fecha`, `Descripción`, `Importe (<moneda>)`, `Saldo (<moneda>)`; fechas `AAAA-MM-DD`; importes con punto decimal, 2 decimales, sin separador de miles y con signo `-` para débitos; CSV con coma como separador y UTF-8 con BOM; XLSX con fecha e importes como celdas numéricas; PDF con importes en formato es-AR (`1.250.000,00`)**
- **Por qué importa**: la HU pide "fecha, descripción, importe y saldo" y que los importes "se muestren en la moneda de la cuenta", pero no define cómo. Sin esto no hay resultado esperado assertable y el objetivo (conciliar contablemente) puede fallar por formato (decimal coma/punto, signo, encoding).
- **Default propuesto**: el indicado arriba. Queda como `[SUPUESTO: (P-1) ...]` en los casos.

**P-2. [B. Datos y validaciones] ¿Qué reglas tiene el rango de fechas? Propuesta cerrada: ambos extremos inclusivos; `desde` <= `hasta`; `hasta` <= fecha de hoy; máximo 365 días de diferencia entre `desde` y `hasta`; cuenta, desde, hasta y formato obligatorios, sin valores por defecto; fechas visibles en formato `dd/mm/aaaa`**
- **Por qué importa**: define todos los bordes (extremos, futuro, rango máximo) y los negativos de validación; un error de ±1 día omite movimientos y rompe la conciliación.
- **Default propuesto**: el indicado arriba. Si el PO prefiere otro máximo (p. ej. 12 meses calendario o sin máximo) se ajustan CP-010 y CP-019.

**P-3. [B. Datos y validaciones] En el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`, ¿`<cuenta>` es el número de cuenta de 10 dígitos (con ceros a la izquierda) y las fechas van como `AAAA-MM-DD`?**
- **Por qué importa**: CA-3 no se puede verificar sin el formato exacto de cada componente (CBU vs. número vs. alias; `AAAA-MM-DD` vs. `DDMMAAAA`); además, un número con ceros puede perder los ceros.
- **Default propuesto**: `<cuenta>` = número de cuenta de 10 dígitos con ceros a la izquierda; fechas `AAAA-MM-DD`; extensión en minúsculas (`csv`, `xlsx`, `pdf`). Ej.: `movimientos_0012345678_2026-09-01_2026-09-30.csv`.

**P-4. [A. Criterios de aceptación] CA-2 dice "rápidamente": ¿cuál es el umbral? Propuesta: hasta 5 segundos para exportar hasta 1.000 movimientos y hasta 30 segundos para el máximo (ver P-6)**
- **Por qué importa**: "rápidamente" no es verificable; sin umbral no se puede aprobar ni fallar un caso de performance.
- **Default propuesto**: 5 s (hasta 1.000 movimientos) y 30 s (hasta 10.000 movimientos), medidos desde tocar "Exportar" hasta que el navegador inicia la descarga.

**P-5. [A/C. Criterios de aceptación / errores] CA-4: ¿cuál es el texto del mensaje y se descarga o no un archivo vacío? Propuesta: se muestra "No hay movimientos para el rango seleccionado." en pantalla y NO se descarga ningún archivo**
- **Por qué importa**: "mensaje adecuado" no es assertable; descargar un archivo sin filas cambia el resultado esperado de los 3 formatos.
- **Default propuesto**: el indicado arriba, mismo comportamiento para CSV, XLSX y PDF.

**P-6. [B/E. Datos / estados] ¿Qué significa `Saldo` y qué entra en el período? Propuesta: `Saldo` = saldo de la cuenta luego de aplicar cada movimiento; orden cronológico ascendente; solo movimientos contabilizados; máximo 10.000 movimientos por exportación (si se excede, se rechaza con mensaje de límite y no se genera archivo)**
- **Por qué importa**: define el resultado esperado de cada fila y de las exportaciones masivas; sin límite el riesgo es timeout/memoria (XLSX/PDF).
- **Default propuesto**: el indicado arriba. El texto del mensaje de límite queda a definir; se asume que menciona el máximo (10.000).

**P-7. [D/F. Permisos y seguridad] ¿Se confirma que: (a) solo se pueden exportar cuentas propias del cliente autenticado y las cuentas cerradas no se listan; (b) un pedido sobre una cuenta ajena o sin sesión se rechaza (401/403/404) sin datos; (c) el archivo solo lo puede descargar la sesión que lo pidió; (d) las descripciones que empiezan con `=`, `+`, `-`, `@` se exportan como texto literal (no como fórmula)?**
- **Por qué importa**: es una funcionalidad de datos personales y dinero (seguridad obligatoria); la HU no define permisos ni protección contra autorización rota ni inyección de fórmulas, que impacta directamente al sistema contable del cliente.
- **Default propuesto**: (a)-(d) como se indica; se asume rechazo 403 (o 404) sin cuerpo con datos y neutralización de fórmulas prefijando `'`.

**P-8. [C/G/J. Errores, concurrencia y contexto] ¿Qué ve el cliente si falla la generación y qué pasa con el doble click y la sesión vencida? Propuesta: mensaje genérico "No pudimos generar el archivo. Intentá nuevamente." sin detalle técnico, sin archivo parcial, selección conservada; el segundo click mientras se genera se ignora (1 sola descarga); sesión vencida redirige al login sin descargar; canal a probar: web (navegador de escritorio)**
- **Por qué importa**: la HU no define ningún camino de error; sin esto los casos de excepción no tienen resultado esperado y la compatibilidad (móvil/otro navegador) queda sin definir.
- **Default propuesto**: el indicado arriba.

## 3. Casos de prueba

### Datos maestros de prueba (referenciados desde cada caso)

Fecha de ejecución asumida: **HOY = 2026-10-09** (si se ejecuta otro día, ajustar los casos CP-009, CP-010, CP-018 y CP-019).

| ID | Dato | Valor |
|---|---|---|
| DM-1 | Cliente QA-01 | usuario `qa.cliente01` (cliente de home banking, acceso web) |
| DM-2 | Cuenta ARS con movimientos (de QA-01) | `0012345678` — Caja de ahorro ARS |
| DM-3 | Cuenta USD con movimientos (de QA-01) | `0087654321` — Caja de ahorro USD |
| DM-4 | Cuenta ARS sin movimientos en septiembre 2026 (de QA-01) | `0011112222` — último movimiento 2026-07-14 |
| DM-5 | Cuenta ARS con descripciones tipo fórmula (de QA-01) | `0033334444` |
| DM-6 | Cuenta cerrada (de QA-01) | `0022223333` — cerrada el 2026-08-20 |
| DM-7 | Cliente QA-02 y su cuenta | usuario `qa.cliente02`, cuenta `0099990000` |
| DM-8 | Cuentas de carga (de QA-01) | `0055550001` (1.000 movimientos), `0055550002` (10.000), `0055550003` (10.001); todos de importe +1.00, saldo inicial 0.00, fechas entre 2026-01-02 y 2026-09-29 |

**DM-2 `0012345678` — movimientos (saldo = saldo posterior al movimiento)**

| Fecha | Descripción | Importe | Saldo |
|---|---|---|---|
| 2026-08-31 | Pago tarjeta Visa | -25000.00 | 400000.00 |
| 2026-09-01 | Acreditación haberes | 850000.00 | 1250000.00 |
| 2026-09-03 | Débito automático Edenor | -48320.55 | 1201679.45 |
| 2026-09-10 | Pago a proveedor, "Ñoño" S.R.L. | -10000.00 | 1191679.45 |
| 2026-09-15 | Transferencia recibida Muñoz Ñandú S.A. | 120000.50 | 1311679.95 |
| 2026-09-30 | Compra débito Café & Té ☕ | -3500.00 | 1308179.95 |
| 2026-10-01 | Débito AFIP | -15000.00 | 1293179.95 |

Sin otros movimientos en la cuenta (ni entre 2025-10-09 y 2026-08-30, ni entre 2026-10-02 y 2026-10-09).

**DM-3 `0087654321` — movimientos**: 2026-09-05 "Compra de divisas" +1500.75 (saldo 2500.75; saldo previo 1000.00); 2026-09-20 "Débito suscripción Cloud" -19.99 (saldo 2480.76).

**DM-5 `0033334444` — movimientos**: 2026-09-12 `=HYPERLINK("http://evil.test","cobrar")` +5000.00 (saldo 5000.00); 2026-09-13 `@SUM(1+1)` +100.00 (saldo 5100.00); 2026-09-14 `-2+3` -50.00 (saldo 5050.00).

**Contenido CSV esperado (supuesto P-1) para DM-2, rango 2026-09-01 a 2026-09-30** (EXP-CSV-1):

```
Fecha,Descripción,Importe (ARS),Saldo (ARS)
2026-09-01,Acreditación haberes,850000.00,1250000.00
2026-09-03,Débito automático Edenor,-48320.55,1201679.45
2026-09-10,"Pago a proveedor, ""Ñoño"" S.R.L.",-10000.00,1191679.45
2026-09-15,Transferencia recibida Muñoz Ñandú S.A.,120000.50,1311679.95
2026-09-30,Compra débito Café & Té ☕,-3500.00,1308179.95
```

---

### CP-001 — Verificar que se exporta en CSV los movimientos de septiembre 2026 de una cuenta ARS con el nombre y contenido correctos

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta en CSV los movimientos de septiembre 2026 de una cuenta ARS con el nombre y contenido correctos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01` (DM-1); pantalla "Movimientos" abierta; cuenta DM-2 con los movimientos indicados; carpeta de descargas del navegador vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Movimientos", seleccionar la cuenta `0012345678` | La cuenta queda seleccionada y se muestra su moneda ARS |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` sin error |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` sin error |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | El navegador descarga un único archivo llamado `movimientos_0012345678_2026-09-01_2026-09-30.csv` [SUPUESTO: (P-3) formato del nombre] |
| 6 | Abrir el archivo en un editor de texto plano | El contenido es idéntico a EXP-CSV-1: 1 fila de encabezado y 5 filas de datos, en ese orden cronológico ascendente [SUPUESTO: (P-1)(P-6) columnas, formato de importes/fechas, orden] |
| 7 | Comparar la columna `Saldo (ARS)` fila a fila | Cada saldo es igual al saldo anterior más el importe de la fila (1250000.00; 1201679.45; 1191679.45; 1311679.95; 1308179.95) [SUPUESTO: (P-6) saldo posterior al movimiento] |
| 8 | Buscar en el archivo los movimientos del 2026-08-31 y del 2026-10-01 | Ninguno de los dos aparece en el archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la pantalla antes de exportar; captura del nombre del archivo descargado; archivo CSV adjunto |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. `[SUPUESTO: (P-1) estructura del archivo; (P-2) extremos inclusivos; (P-3) nombre; (P-6) saldo y orden]`. |

---

### CP-002 — Verificar que se exporta en XLSX los movimientos de septiembre 2026 con nombre, columnas y tipos de celda correctos

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta en XLSX los movimientos de septiembre 2026 con nombre, columnas y tipos de celda correctos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; DM-2; carpeta de descargas vacía; Excel (o LibreOffice Calc) instalado |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato XLSX |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "XLSX" | "XLSX" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga un único archivo llamado `movimientos_0012345678_2026-09-01_2026-09-30.xlsx` [SUPUESTO: (P-3)] |
| 6 | Abrir el archivo en Excel | El archivo abre sin mensaje de error ni de reparación |
| 7 | Leer la primera hoja | La fila 1 contiene `Fecha`, `Descripción`, `Importe (ARS)`, `Saldo (ARS)` y las filas 2 a 6 contienen los 5 movimientos de EXP-CSV-1 en el mismo orden [SUPUESTO: (P-1)] |
| 8 | Seleccionar la celda de importe de la fila 3 (-48320.55) | La celda es de tipo numérico (alineada a la derecha, aparece en la barra de fórmulas como -48320.55) y no texto [SUPUESTO: (P-1) celdas numéricas] |
| 9 | Aplicar `SUMA` sobre la columna Importe | El resultado es 908179.95 (850000.00 - 48320.55 - 10000.00 + 120000.50 - 3500.00) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de Excel con la hoja abierta; screenshot del resultado de la suma; archivo XLSX adjunto |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. `[SUPUESTO: (P-1) tipos numéricos y columnas]`. El total del paso 9 coincide con 1308179.95 - 400000.00 = 908179.95 (saldo final menos saldo previo al 01/09). |

---

### CP-003 — Verificar que se exporta en PDF los movimientos de septiembre 2026 con nombre y contenido correctos

| Campo | Valor |
|---|---|
| **Título** | Verificar que se exporta en PDF los movimientos de septiembre 2026 con nombre y contenido correctos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2, CA-3 |
| **Tipo** | Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; DM-2; carpeta de descargas vacía; lector de PDF instalado |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "PDF" | "PDF" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga un único archivo llamado `movimientos_0012345678_2026-09-01_2026-09-30.pdf` [SUPUESTO: (P-3)] |
| 6 | Abrir el PDF | El PDF abre sin error |
| 7 | Leer el encabezado del documento | Se identifica la cuenta `0012345678`, la moneda ARS y el período 01/09/2026 al 30/09/2026 [SUPUESTO: (P-1) contenido del encabezado del PDF] |
| 8 | Leer la tabla de movimientos | Hay exactamente 5 filas con fecha, descripción, importe y saldo: 850.000,00 / 1.250.000,00; -48.320,55 / 1.201.679,45; -10.000,00 / 1.191.679,45; 120.000,50 / 1.311.679,95; -3.500,00 / 1.308.179,95 [SUPUESTO: (P-1) formato es-AR en PDF] |
| 9 | Buscar los movimientos del 31/08/2026 y del 01/10/2026 | Ninguno aparece en el PDF |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del PDF (página completa); nombre del archivo descargado; PDF adjunto |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. `[SUPUESTO: (P-1) layout y formato numérico del PDF]`. |

---

### CP-004 — Verificar que una cuenta USD se exporta en CSV con importes y saldo en dólares y el número de cuenta correcto en el nombre

| Campo | Valor |
|---|---|
| **Título** | Verificar que una cuenta USD se exporta en CSV con importes y saldo en dólares y el número de cuenta correcto en el nombre |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2, CA-3 y Nota (moneda de la cuenta) |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; cuenta DM-3 con sus 2 movimientos; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0087654321`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0087654321` | La cuenta queda seleccionada y se muestra su moneda USD |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga `movimientos_0087654321_2026-09-01_2026-09-30.csv` [SUPUESTO: (P-3)] |
| 6 | Abrir el archivo en un editor de texto | Hay 1 fila de encabezado `Fecha,Descripción,Importe (USD),Saldo (USD)` y 2 filas: `2026-09-05,Compra de divisas,1500.75,2500.75` y `2026-09-20,Débito suscripción Cloud,-19.99,2480.76` [SUPUESTO: (P-1) moneda en encabezado de columnas] |
| 7 | Buscar el texto "ARS" en el archivo | No aparece en ninguna parte del archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del selector con la moneda USD; archivo CSV adjunto |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-1) la moneda se indica en el encabezado de las columnas Importe y Saldo]`. |

---

### CP-005 — Verificar que una cuenta USD se exporta en PDF mostrando la moneda USD

| Campo | Valor |
|---|---|
| **Título** | Verificar que una cuenta USD se exporta en PDF mostrando la moneda USD |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2, CA-3 y Nota (moneda de la cuenta) |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; cuenta DM-3; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0087654321`; desde `01/09/2026`; hasta `30/09/2026`; formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0087654321` | La cuenta queda seleccionada con moneda USD |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "PDF" | "PDF" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga `movimientos_0087654321_2026-09-01_2026-09-30.pdf` [SUPUESTO: (P-3)] |
| 6 | Abrir el PDF | El encabezado indica la cuenta `0087654321` y la moneda USD |
| 7 | Leer la tabla | Hay 2 filas: 05/09/2026 Compra de divisas 1.500,75 / 2.500,75 y 20/09/2026 Débito suscripción Cloud -19,99 / 2.480,76, con la moneda USD indicada en los encabezados de columna [SUPUESTO: (P-1) formato es-AR] |
| 8 | Buscar el texto "ARS" en el PDF | No aparece en el documento |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del PDF; archivo adjunto |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-1)]`. |

---

### CP-006 — Verificar que si se cambia la cuenta antes de exportar el archivo corresponde a la última cuenta seleccionada

| Campo | Valor |
|---|---|
| **Título** | Verificar que si se cambia la cuenta antes de exportar el archivo corresponde a la última cuenta seleccionada |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; DM-2 y DM-3; carpeta de descargas vacía |
| **Datos de prueba** | Primera cuenta `0012345678` (ARS); segunda cuenta `0087654321` (USD); desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Cambiar la cuenta seleccionada a `0087654321` | La cuenta mostrada es `0087654321` (USD) |
| 6 | Tocar "Exportar" | Se descarga `movimientos_0087654321_2026-09-01_2026-09-30.csv` |
| 7 | Abrir el archivo | Contiene solo los 2 movimientos de la cuenta USD (2026-09-05 y 2026-09-20) y ningún movimiento de la cuenta `0012345678` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la selección final antes de exportar; archivo CSV |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2) al cambiar de cuenta se conservan las fechas y el formato ya cargados]`. |

---

### CP-007 — Verificar que un rango de un solo día incluye el movimiento de ese día (extremos inclusivos, 1 fila)

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango de un solo día incluye el movimiento de ese día (extremos inclusivos, 1 fila) |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `30/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `30/09/2026` en "Desde" | El campo muestra `30/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` sin error de validación [SUPUESTO: (P-2) desde = hasta es válido] |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-30_2026-09-30.csv` |
| 6 | Abrir el archivo | Contiene el encabezado y exactamente 1 fila: `2026-09-30,Compra débito Café & Té ☕,-3500.00,1308179.95` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Archivo CSV; screenshot del rango cargado |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2) ambos extremos inclusivos]`. Verifica el error off-by-one por el límite superior. |

---

### CP-008 — Verificar que un rango que no incluye los días de los extremos excluye los movimientos del 01/09 y del 30/09

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango que no incluye los días de los extremos excluye los movimientos del 01/09 y del 30/09 |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `02/09/2026`; hasta `29/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `02/09/2026` en "Desde" | El campo muestra `02/09/2026` |
| 3 | Ingresar `29/09/2026` en "Hasta" | El campo muestra `29/09/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2026-09-02_2026-09-29.csv` |
| 6 | Abrir el archivo | Contiene encabezado y exactamente 3 filas: `2026-09-03,Débito automático Edenor,-48320.55,1201679.45`; `2026-09-10,"Pago a proveedor, ""Ñoño"" S.R.L.",-10000.00,1191679.45`; `2026-09-15,Transferencia recibida Muñoz Ñandú S.A.,120000.50,1311679.95` |
| 7 | Comprobar el saldo de la primera fila | Es 1201679.45 (el saldo real de la cuenta tras el movimiento) y no un saldo recalculado desde cero [SUPUESTO: (P-6) saldo = saldo real posterior al movimiento] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Archivo CSV; captura del rango cargado |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-6) semántica del saldo]`. |

---

### CP-009 — Verificar que se acepta exportar con "Hasta" igual a la fecha de hoy y se incluye el movimiento del 01/10/2026

| Campo | Valor |
|---|---|
| **Título** | Verificar que se acepta exportar con "Hasta" igual a la fecha de hoy y se incluye el movimiento del 01/10/2026 |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2; HOY = 2026-10-09 (si difiere, usar la fecha de hoy en "Hasta"); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/10/2026`; hasta `09/10/2026` (HOY); formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `01/10/2026` en "Desde" | El campo muestra `01/10/2026` |
| 3 | Ingresar `09/10/2026` en "Hasta" | El campo muestra `09/10/2026` sin error de validación [SUPUESTO: (P-2) hasta = hoy es válido] |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2026-10-01_2026-10-09.csv` |
| 6 | Abrir el archivo | Contiene encabezado y 1 fila: `2026-10-01,Débito AFIP,-15000.00,1293179.95` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Archivo CSV; captura del rango |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2) hasta <= hoy]`. |

---

### CP-010 — Verificar que se acepta un rango de exactamente 365 días de diferencia (máximo permitido)

| Campo | Valor |
|---|---|
| **Título** | Verificar que se acepta un rango de exactamente 365 días de diferencia (máximo permitido) |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2 (sin movimientos entre 2025-10-09 y 2026-08-30); HOY = 2026-10-09; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `09/10/2025`; hasta `09/10/2026`; formato CSV (diferencia = 365 días) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `09/10/2025` en "Desde" | El campo muestra `09/10/2025` |
| 3 | Ingresar `09/10/2026` en "Hasta" | El campo muestra `09/10/2026` sin error de validación [SUPUESTO: (P-2) máximo 365 días] |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Se descarga `movimientos_0012345678_2025-10-09_2026-10-09.csv` |
| 6 | Abrir el archivo | Contiene encabezado y 7 filas: los movimientos del 2026-08-31, 09-01, 09-03, 09-10, 09-15, 09-30 y 10-01 de DM-2, en orden cronológico ascendente |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Archivo CSV; captura del rango |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2) máximo 365 días]`. Complementa CP-019 (366 días, rechazo). |

---

### CP-011 — Verificar que un rango sin movimientos muestra el mensaje y no descarga ningún archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que un rango sin movimientos muestra el mensaje y no descarga ningún archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | Humo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; cuenta DM-4 sin movimientos entre 2026-09-01 y 2026-09-30; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0011112222`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0011112222` | La cuenta queda seleccionada |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Se muestra en pantalla el mensaje "No hay movimientos para el rango seleccionado." [SUPUESTO: (P-5) texto del mensaje] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo descargado (ni vacío ni con solo el encabezado) [SUPUESTO: (P-5) no se descarga archivo] |
| 7 | Revisar los campos del formulario | La cuenta, las fechas y el formato siguen cargados con los valores ingresados [SUPUESTO: (P-5) se conserva la selección] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; captura de la carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | Subset de humo (camino de CA-4). `[SUPUESTO: (P-5)]`. |

---

### CP-012 — Verificar que un día sin movimientos en una cuenta con movimientos en otros días muestra el mensaje en XLSX y PDF

| Campo | Valor |
|---|---|
| **Título** | Verificar que un día sin movimientos en una cuenta con movimientos en otros días muestra el mensaje en XLSX y PDF |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-4 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2 (sin movimiento el 2026-09-02); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `02/09/2026`; hasta `02/09/2026`; formatos XLSX y luego PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `02/09/2026` en "Desde" | El campo muestra `02/09/2026` |
| 3 | Ingresar `02/09/2026` en "Hasta" | El campo muestra `02/09/2026` |
| 4 | Seleccionar el formato "XLSX" | "XLSX" queda seleccionado |
| 5 | Tocar "Exportar" | Se muestra el mensaje "No hay movimientos para el rango seleccionado." [SUPUESTO: (P-5)] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo |
| 7 | Seleccionar el formato "PDF" | "PDF" queda seleccionado |
| 8 | Tocar "Exportar" | Se muestra el mensaje "No hay movimientos para el rango seleccionado." [SUPUESTO: (P-5)] |
| 9 | Revisar la carpeta de descargas | No hay ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de ambos mensajes; carpeta de descargas vacía |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-5) mismo comportamiento en los 3 formatos]`. |

---

### CP-013 — Verificar que no se puede exportar sin seleccionar el formato

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se puede exportar sin seleccionar el formato |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" recién abierta (ningún formato elegido); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato sin seleccionar |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Tocar "Exportar" sin elegir formato | Aparece un mensaje de validación visible junto al campo "Formato" indicando que es obligatorio [SUPUESTO: (P-2) el formato es obligatorio y no tiene valor por defecto; texto exacto a definir] |
| 5 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje de validación |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2) obligatoriedad y ausencia de default]`. Si el producto preselecciona un formato, este caso pasa a "No aplicable" (ver respuesta a P-2). |

---

### CP-014 — Verificar que no se puede exportar sin seleccionar la cuenta

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se puede exportar sin seleccionar la cuenta |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" sin cuenta seleccionada; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta sin seleccionar; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 2 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 3 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 4 | Tocar "Exportar" sin cuenta seleccionada | Aparece un mensaje de validación visible junto al campo "Cuenta" indicando que es obligatorio [SUPUESTO: (P-2) cuenta obligatoria; texto exacto a definir] |
| 5 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje de validación |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2)]`. Si la pantalla preselecciona la primera cuenta, el caso pasa a "No aplicable". |

---

### CP-015 — Verificar que no se puede exportar con la fecha "Desde" vacía

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se puede exportar con la fecha "Desde" vacía |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde vacío; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Dejar vacío el campo "Desde" | El campo está vacío |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Aparece un mensaje de validación visible junto al campo "Desde" indicando que es obligatorio [SUPUESTO: (P-2) texto exacto a definir] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje de validación |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2) fechas obligatorias]`. |

---

### CP-016 — Verificar que no se puede exportar con la fecha "Hasta" vacía

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se puede exportar con la fecha "Hasta" vacía |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta vacío; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `01/09/2026` en "Desde" | El campo muestra `01/09/2026` |
| 3 | Dejar vacío el campo "Hasta" | El campo está vacío |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Aparece un mensaje de validación visible junto al campo "Hasta" indicando que es obligatorio [SUPUESTO: (P-2) texto exacto a definir] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje de validación |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2)]`. |

---

### CP-017 — Verificar que se rechaza un rango con "Desde" posterior a "Hasta"

| Campo | Valor |
|---|---|
| **Título** | Verificar que se rechaza un rango con "Desde" posterior a "Hasta" |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `30/09/2026`; hasta `01/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `30/09/2026` en "Desde" | El campo muestra `30/09/2026` |
| 3 | Ingresar `01/09/2026` en "Hasta" | El campo muestra `01/09/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Aparece un mensaje de error de validación indicando que "Desde" no puede ser posterior a "Hasta" [SUPUESTO: (P-2) desde <= hasta; texto exacto a definir] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo descargado y no se muestra el mensaje de "sin movimientos" |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje de error |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2)]`. El paso 6 verifica que no se confunda este error con CA-4. |

---

### CP-018 — Verificar que se rechaza un "Hasta" posterior a la fecha de hoy

| Campo | Valor |
|---|---|
| **Título** | Verificar que se rechaza un "Hasta" posterior a la fecha de hoy |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; HOY = 2026-10-09; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/10/2026`; hasta `10/10/2026` (HOY + 1); formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `01/10/2026` en "Desde" | El campo muestra `01/10/2026` |
| 3 | Ingresar `10/10/2026` en "Hasta" | El campo muestra `10/10/2026` o el calendario impide seleccionarlo (deshabilitado) |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Aparece un mensaje de error de validación indicando que "Hasta" no puede ser futura, o el botón no inicia la exportación [SUPUESTO: (P-2) hasta <= hoy; texto exacto a definir] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje o del calendario con el día deshabilitado |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2)]`. Complementa CP-009 (hasta = hoy, aceptado). |

---

### CP-019 — Verificar que se rechaza un rango de 366 días (mayor al máximo permitido)

| Campo | Valor |
|---|---|
| **Título** | Verificar que se rechaza un rango de 366 días (mayor al máximo permitido) |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; HOY = 2026-10-09; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `08/10/2025`; hasta `09/10/2026`; formato CSV (diferencia = 366 días) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Ingresar `08/10/2025` en "Desde" | El campo muestra `08/10/2025` |
| 3 | Ingresar `09/10/2026` en "Hasta" | El campo muestra `09/10/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Aparece un mensaje de error de validación que indica el rango máximo permitido (365 días) [SUPUESTO: (P-2) máximo 365 días; texto exacto a definir] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje de error |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2)]`. Complementa CP-010 (365 días, aceptado). |

---

### CP-020 — Verificar que una fecha inexistente (29/02/2026) se rechaza

| Campo | Valor |
|---|---|
| **Título** | Verificar que una fecha inexistente (29/02/2026) se rechaza |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; el campo de fecha admite tipeo manual [SUPUESTO: (P-2) formato `dd/mm/aaaa` ingresable por teclado]; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `29/02/2026` (2026 no es bisiesto); hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Seleccionar la cuenta `0012345678` | La cuenta queda seleccionada |
| 2 | Tipear `29/02/2026` en "Desde" | El campo no acepta el valor o lo marca como inválido |
| 3 | Ingresar `30/09/2026` en "Hasta" | El campo muestra `30/09/2026` |
| 4 | Seleccionar el formato "CSV" | "CSV" queda seleccionado |
| 5 | Tocar "Exportar" | Aparece un mensaje de validación de fecha inválida junto a "Desde" [SUPUESTO: (P-2) texto exacto a definir] |
| 6 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del campo y del mensaje |
| **Estado** | Pendiente |
| **Notas** | Si el componente solo permite elegir fecha desde calendario, el caso pasa a "No aplicable". `[SUPUESTO: (P-2)]`. |

---

### CP-021 — Verificar que no se puede exportar una cuenta ajena modificando el pedido de exportación

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se puede exportar una cuenta ajena modificando el pedido de exportación |
| **Módulo** | Home banking / Movimientos / Exportación (seguridad) |
| **Origen** | HU-202 · CA-1 (seguridad: datos personales y dinero) |
| **Tipo** | No funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01` (DM-1); la cuenta `0099990000` pertenece a `qa.cliente02` (DM-7) y tiene movimientos; herramienta de interceptación de requests (DevTools, Burp o Postman) disponible |
| **Datos de prueba** | Cuenta propia `0012345678`; cuenta ajena `0099990000`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Con la herramienta abierta, exportar `0012345678`, desde `01/09/2026`, hasta `30/09/2026`, CSV | Se descarga el archivo de `0012345678` y el pedido de exportación queda registrado en la herramienta |
| 2 | Copiar el pedido de exportación y reemplazar el identificador de la cuenta por `0099990000` | El pedido modificado queda listo para reenviar con la sesión de `qa.cliente01` |
| 3 | Reenviar el pedido modificado | La respuesta es un rechazo 403 (o 404) [SUPUESTO: (P-7) código de rechazo] sin contenido de movimientos |
| 4 | Revisar el cuerpo de la respuesta | No contiene datos de `0099990000` ni del titular (nombre, saldo, movimientos) |
| 5 | Revisar la carpeta de descargas | No hay ningún archivo nuevo de `0099990000` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Request y response (código y cuerpo) de los pasos 1 y 3 |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-7) rechazo 403/404 sin datos]`. Autorización rota (IDOR). |

---

### CP-022 — Verificar que el pedido de exportación sin sesión es rechazado

| Campo | Valor |
|---|---|
| **Título** | Verificar que el pedido de exportación sin sesión es rechazado |
| **Módulo** | Home banking / Movimientos / Exportación (seguridad) |
| **Origen** | HU-202 · CA-1 (seguridad) |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Pedido de exportación válido capturado previamente con `qa.cliente01` (como en CP-021 paso 1); la sesión de `qa.cliente01` fue cerrada con "Cerrar sesión" |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV; pedido sin cookie/token de sesión |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Reenviar el pedido capturado sin cookie ni token de autenticación | La respuesta es 401 o redirección al login [SUPUESTO: (P-7) rechazo sin sesión] |
| 2 | Revisar el cuerpo de la respuesta | No contiene movimientos ni datos de cuenta |
| 3 | Reenviar el pedido con el token de la sesión ya cerrada | La respuesta es 401 o redirección al login y no se devuelve ningún archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Request y response de los pasos 1 y 3 |
| **Estado** | Pendiente |
| **Notas** | Depende de haber ejecutado CP-021 paso 1 (o capturar el pedido de forma equivalente). `[SUPUESTO: (P-7)]`. |

---

### CP-023 — Verificar que la URL de descarga del archivo no sirve para otra sesión de otro cliente

| Campo | Valor |
|---|---|
| **Título** | Verificar que la URL de descarga del archivo no sirve para otra sesión de otro cliente |
| **Módulo** | Home banking / Movimientos / Exportación (seguridad) |
| **Origen** | HU-202 · CA-3 (seguridad) |
| **Tipo** | No funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Dos navegadores o perfiles distintos: A con sesión de `qa.cliente01`, B con sesión de `qa.cliente02`; la descarga se hace por una URL que se puede observar en DevTools [SUPUESTO: (P-7) la descarga es vía URL; si es por blob/stream local el caso es "No aplicable"] |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En el navegador A (DevTools > Network abierto), exportar `0012345678` en CSV para septiembre 2026 | Se descarga el archivo y la URL de descarga queda visible en Network |
| 2 | Copiar la URL de descarga | La URL está copiada |
| 3 | Pegar la URL en el navegador B (sesión de `qa.cliente02`) | Se rechaza el acceso (403/404 o redirección) y no se descarga el archivo [SUPUESTO: (P-7) archivo solo descargable por su sesión] |
| 4 | Pegar la URL en una ventana sin sesión | Se rechaza el acceso (401 o redirección al login) y no se descarga el archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | URL, código de respuesta y screenshot en cada navegador |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-7)]`. |

---

### CP-024 — Verificar que el servidor valida formato y rango y rechaza pedidos inválidos enviados directamente

| Campo | Valor |
|---|---|
| **Título** | Verificar que el servidor valida formato y rango y rechaza pedidos inválidos enviados directamente |
| **Módulo** | Home banking / Movimientos / Exportación (seguridad) |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión válida de `qa.cliente01`; pedido de exportación capturado (como en CP-021 paso 1) y reenviable desde Postman con el token de esa sesión; HOY = 2026-10-09 |
| **Datos de prueba** | Cuenta `0012345678`; variantes: (a) formato `docx`; (b) desde `2026-09-30` hasta `2026-09-01`; (c) desde `2025-09-01` hasta `2026-10-09` (403 días); (d) desde `2026-10-01` hasta `2026-10-10` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Reenviar el pedido con formato `docx` | Respuesta 4xx (400/422) sin archivo [SUPUESTO: (P-7)(P-2) validación server-side] |
| 2 | Reenviar el pedido con desde `2026-09-30` y hasta `2026-09-01` | Respuesta 4xx sin archivo |
| 3 | Reenviar el pedido con desde `2025-09-01` y hasta `2026-10-09` | Respuesta 4xx sin archivo |
| 4 | Reenviar el pedido con hasta `2026-10-10` | Respuesta 4xx sin archivo |
| 5 | Revisar el cuerpo de las 4 respuestas | Ninguna contiene stack trace, consulta SQL ni datos de otras cuentas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Request y response de cada variante |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-2)(P-7) las reglas de rango/formato también se aplican en el servidor]`. Campos del front no son confiables. |

---

### CP-025 — Verificar que las descripciones que empiezan con =, @ o - se exportan como texto y no se ejecutan como fórmulas

| Campo | Valor |
|---|---|
| **Título** | Verificar que las descripciones que empiezan con =, @ o - se exportan como texto y no se ejecutan como fórmulas |
| **Módulo** | Home banking / Movimientos / Exportación (seguridad) |
| **Origen** | HU-202 · CA-2 (seguridad) |
| **Tipo** | No funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; cuenta DM-5 con sus 3 movimientos; Excel instalado con la configuración de seguridad por defecto; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0033334444`; desde `01/09/2026`; hasta `30/09/2026`; formatos CSV y XLSX; descripciones `=HYPERLINK("http://evil.test","cobrar")`, `@SUM(1+1)`, `-2+3` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Exportar `0033334444` en CSV para septiembre 2026 | Se descarga `movimientos_0033334444_2026-09-01_2026-09-30.csv` |
| 2 | Abrir el CSV en un editor de texto | Las 3 descripciones aparecen prefijadas con `'` (p. ej. `'=HYPERLINK(...)`) o equivalente que impida su evaluación [SUPUESTO: (P-7) neutralización prefijando `'`] |
| 3 | Abrir el CSV con Excel | Las 3 celdas de descripción muestran el texto literal; no hay hipervínculo activo, no se calcula `2` ni `1` y no aparece advertencia de DDE/enlaces externos |
| 4 | Exportar `0033334444` en XLSX para septiembre 2026 | Se descarga `movimientos_0033334444_2026-09-01_2026-09-30.xlsx` |
| 5 | Abrir el XLSX con Excel | Las 3 celdas de descripción están almacenadas como texto, muestran el literal y no evalúan fórmulas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de Excel con las celdas; contenido del CSV en texto plano |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-7)(d) las descripciones se exportan como texto literal]`. CSV/formula injection: afecta al sistema contable del cliente. |

---

### CP-026 — Verificar que el selector de cuentas lista solo las cuentas propias activas

| Campo | Valor |
|---|---|
| **Título** | Verificar que el selector de cuentas lista solo las cuentas propias activas |
| **Módulo** | Home banking / Movimientos / Exportación (seguridad) |
| **Origen** | HU-202 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2 a DM-8; la cuenta `0022223333` cerrada; la cuenta `0099990000` pertenece a `qa.cliente02` |
| **Datos de prueba** | Selector de cuenta de "Movimientos" |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el selector de cuenta en "Movimientos" | Se despliega la lista de cuentas |
| 2 | Revisar la lista | Aparecen `0012345678`, `0087654321`, `0011112222`, `0033334444`, `0055550001`, `0055550002` y `0055550003` |
| 3 | Buscar `0099990000` en la lista | No aparece |
| 4 | Buscar `0022223333` en la lista | No aparece [SUPUESTO: (P-7) las cuentas cerradas no se listan] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la lista desplegada |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-7)(a)]`. |

---

### CP-027 — Verificar que ante un error 500 del servicio de generación se muestra un mensaje genérico y no se descarga un archivo

| Campo | Valor |
|---|---|
| **Título** | Verificar que ante un error 500 del servicio de generación se muestra un mensaje genérico y no se descarga un archivo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 (excepción) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2; herramienta para forzar una respuesta 500 en el pedido de exportación (DevTools > Local overrides, proxy o mock); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato PDF; respuesta forzada 500 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0012345678`, desde `01/09/2026`, hasta `30/09/2026` y formato PDF | Los datos quedan cargados |
| 2 | Activar el mock que responde 500 al pedido de exportación | El mock queda activo |
| 3 | Tocar "Exportar" | Se muestra el mensaje "No pudimos generar el archivo. Intentá nuevamente." [SUPUESTO: (P-8) texto del mensaje] |
| 4 | Revisar la carpeta de descargas | No hay ningún archivo (ni vacío ni parcial) |
| 5 | Revisar el mensaje en pantalla | No contiene stack trace, códigos internos ni detalles de la consulta |
| 6 | Revisar los campos del formulario | Cuenta, fechas y formato siguen cargados [SUPUESTO: (P-8) selección conservada] |
| 7 | Desactivar el mock y tocar "Exportar" otra vez | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.pdf` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; request/response 500; carpeta de descargas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-8)]`. |

---

### CP-028 — Verificar que si se pierde la red al exportar se informa el error y no se descarga un archivo parcial

| Campo | Valor |
|---|---|
| **Título** | Verificar que si se pierde la red al exportar se informa el error y no se descarga un archivo parcial |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 (excepción) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato XLSX; DevTools > Network > "Offline" |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0012345678`, desde `01/09/2026`, hasta `30/09/2026` y formato XLSX | Los datos quedan cargados |
| 2 | Activar el modo "Offline" en DevTools | El navegador queda sin red |
| 3 | Tocar "Exportar" | Se muestra un mensaje de error de conexión/generación [SUPUESTO: (P-8) mismo mensaje genérico "No pudimos generar el archivo. Intentá nuevamente."] |
| 4 | Revisar la carpeta de descargas | No hay ningún archivo, ni parcial (`.crdownload`) |
| 5 | Desactivar el modo "Offline" | La red se restablece |
| 6 | Tocar "Exportar" otra vez | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.xlsx` con 5 filas de movimientos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de descargas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-8)]`. |

---

### CP-029 — Verificar que un doble click rápido en "Exportar" genera una sola descarga

| Campo | Valor |
|---|---|
| **Título** | Verificar que un doble click rápido en "Exportar" genera una sola descarga |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 (concurrencia) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; DM-2; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0012345678`, desde `01/09/2026`, hasta `30/09/2026` y formato CSV | Los datos quedan cargados |
| 2 | Hacer doble click rápido (menos de 300 ms entre clicks) en "Exportar" | Se inicia una exportación |
| 3 | Revisar la carpeta de descargas | Hay exactamente 1 archivo `movimientos_0012345678_2026-09-01_2026-09-30.csv` (no existe `...(1).csv`) [SUPUESTO: (P-8) el segundo click se ignora] |
| 4 | Presionar Enter con el foco en "Exportar" y hacer click casi simultáneamente | No se descarga un segundo archivo |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Carpeta de descargas; pestaña Network con el número de pedidos de exportación |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-8)]`. |

---

### CP-030 — Verificar que refrescar la página mientras se genera la exportación no deja archivos corruptos y permite reintentar

| Campo | Valor |
|---|---|
| **Título** | Verificar que refrescar la página mientras se genera la exportación no deja archivos corruptos y permite reintentar |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 (excepción) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; cuenta DM-8 `0055550002` (10.000 movimientos); DevTools > Network con throttling "Slow 3G"; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0055550002`; desde `01/01/2026`; hasta `30/09/2026`; formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0055550002`, desde `01/01/2026`, hasta `30/09/2026` y formato PDF | Los datos quedan cargados |
| 2 | Tocar "Exportar" | Se inicia la generación (indicador de progreso o botón deshabilitado) [SUPUESTO: (P-8)] |
| 3 | Refrescar la página (F5) antes de que termine | La pantalla "Movimientos" se recarga sin error y la sesión sigue activa |
| 4 | Revisar la carpeta de descargas | No hay ningún archivo corrupto ni parcial |
| 5 | Quitar el throttling, cargar de nuevo los datos y tocar "Exportar" | Se descarga el PDF `movimientos_0055550002_2026-01-01_2026-09-30.pdf` y abre sin error |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot tras el refresh; carpeta de descargas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-8)]`. |

---

### CP-031 — Verificar que con la sesión vencida al tocar "Exportar" se redirige al login y no se descarga nada

| Campo | Valor |
|---|---|
| **Título** | Verificar que con la sesión vencida al tocar "Exportar" se redirige al login y no se descarga nada |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-1 (sesión) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" con la exportación cargada; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV; sesión invalidada (esperar el timeout de inactividad o borrar la cookie/token de sesión en DevTools) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0012345678`, desde `01/09/2026`, hasta `30/09/2026` y formato CSV | Los datos quedan cargados |
| 2 | Invalidar la sesión (borrar la cookie/token de sesión desde DevTools) | La sesión queda invalidada |
| 3 | Tocar "Exportar" | La aplicación redirige a la pantalla de login o muestra el aviso de sesión expirada [SUPUESTO: (P-8) redirección al login] |
| 4 | Revisar la carpeta de descargas | No hay ningún archivo descargado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la pantalla de login; request/response |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-8)]`. |

---

### CP-032 — Verificar que dos exportaciones simultáneas de cuentas distintas en dos pestañas generan archivos independientes y correctos

| Campo | Valor |
|---|---|
| **Título** | Verificar que dos exportaciones simultáneas de cuentas distintas en dos pestañas generan archivos independientes y correctos |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2, CA-3 (concurrencia) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01` en dos pestañas del mismo navegador; DM-2 y DM-3; carpeta de descargas vacía |
| **Datos de prueba** | Pestaña 1: cuenta `0012345678`, formato CSV; pestaña 2: cuenta `0087654321`, formato XLSX; ambas con desde `01/09/2026` y hasta `30/09/2026` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En la pestaña 1, cargar cuenta `0012345678`, fechas `01/09/2026` a `30/09/2026` y formato CSV | Los datos quedan cargados |
| 2 | En la pestaña 2, cargar cuenta `0087654321`, fechas `01/09/2026` a `30/09/2026` y formato XLSX | Los datos quedan cargados |
| 3 | Tocar "Exportar" en la pestaña 1 y, sin esperar, en la pestaña 2 | Ambas exportaciones se inician |
| 4 | Revisar la carpeta de descargas | Hay exactamente 2 archivos: `movimientos_0012345678_2026-09-01_2026-09-30.csv` y `movimientos_0087654321_2026-09-01_2026-09-30.xlsx` |
| 5 | Abrir el CSV | Contiene los 5 movimientos de la cuenta ARS y ninguno de la cuenta USD |
| 6 | Abrir el XLSX | Contiene los 2 movimientos de la cuenta USD y ninguno de la cuenta ARS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Carpeta de descargas; ambos archivos |
| **Estado** | Pendiente |
| **Notas** | Sin supuesto de comportamiento: se espera independencia entre exportaciones. |

---

### CP-033 — Verificar que el CSV con comillas, comas, ñ, acentos y emoji se interpreta correctamente en Excel y en un parser CSV

| Campo | Valor |
|---|---|
| **Título** | Verificar que el CSV con comillas, comas, ñ, acentos y emoji se interpreta correctamente en Excel y en un parser CSV |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | No funcional |
| **Prioridad** | Alta |
| **Precondiciones** | CP-001 ejecutado con éxito (archivo `movimientos_0012345678_2026-09-01_2026-09-30.csv` disponible); Excel y Python 3 instalados |
| **Datos de prueba** | Archivo CSV de CP-001; fila 3 con descripción `Pago a proveedor, "Ñoño" S.R.L.`; fila 5 con `Compra débito Café & Té ☕` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el CSV con doble click en Excel | Se muestran 4 columnas y 5 filas de datos; los acentos, `Ñ` y `ñ` se ven bien (sin `Ã±`) [SUPUESTO: (P-1) UTF-8 con BOM] |
| 2 | Leer la celda de descripción de la fila 3 | Muestra `Pago a proveedor, "Ñoño" S.R.L.` en una sola celda |
| 3 | Leer la celda de descripción de la fila 5 | Muestra `Compra débito Café & Té ☕` |
| 4 | Leer el archivo con `python -c "import csv;print([len(r) for r in csv.reader(open('<ruta>',encoding='utf-8-sig',newline=''))])"` | Imprime `[4, 4, 4, 4, 4, 4]` (encabezado + 5 filas, todas con 4 campos) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de Excel; salida del comando |
| **Estado** | Pendiente |
| **Notas** | Depende de CP-001. `[SUPUESTO: (P-1) separador coma y UTF-8 con BOM]`. |

---

### CP-034 — Verificar que XLSX y PDF muestran correctamente ñ, acentos, comillas y emoji en las descripciones

| Campo | Valor |
|---|---|
| **Título** | Verificar que XLSX y PDF muestran correctamente ñ, acentos, comillas y emoji en las descripciones |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | CP-002 y CP-003 ejecutados con éxito (XLSX y PDF disponibles) |
| **Datos de prueba** | Archivos de CP-002 y CP-003; descripciones `Pago a proveedor, "Ñoño" S.R.L.`, `Transferencia recibida Muñoz Ñandú S.A.`, `Compra débito Café & Té ☕` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el XLSX y leer las 3 descripciones | Se ven exactamente como en los datos de prueba, incluido `☕` |
| 2 | Abrir el PDF y leer las 3 descripciones | `Ñoño`, `Muñoz Ñandú` y `Café & Té` se ven correctamente; ninguna aparece cortada ni como `?` o recuadro |
| 3 | Leer la descripción `Compra débito Café & Té ☕` en el PDF | Se ve el emoji `☕` o, si la fuente no lo soporta, el comportamiento queda registrado como hallazgo exploratorio [SUPUESTO: (P-1) soporte de emoji en PDF no definido] |
| 4 | Revisar que ninguna descripción se superponga con la columna Importe en el PDF | Cada texto largo se ajusta (salto de línea o truncado visible) sin pisar otras columnas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots del XLSX y del PDF |
| **Estado** | Pendiente |
| **Notas** | Depende de CP-002 y CP-003. El paso 3 es exploratorio para el caso emoji en PDF. |

---

### CP-035 — Verificar que una cuenta con 1.000 movimientos se exporta en los 3 formatos dentro del umbral de tiempo

| Campo | Valor |
|---|---|
| **Título** | Verificar que una cuenta con 1.000 movimientos se exporta en los 3 formatos dentro del umbral de tiempo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; cuenta DM-8 `0055550001` (1.000 movimientos de +1.00, saldo final 1000.00); red sin throttling; cronómetro disponible |
| **Datos de prueba** | Cuenta `0055550001`; desde `01/01/2026`; hasta `30/09/2026`; formatos CSV, XLSX y PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0055550001`, fechas `01/01/2026` a `30/09/2026` y formato CSV | Los datos quedan cargados |
| 2 | Tocar "Exportar" y medir hasta que inicia la descarga | La descarga inicia en 5 segundos o menos [SUPUESTO: (P-4) umbral de 5 s] |
| 3 | Abrir el CSV y contar las filas de datos | Hay 1.000 filas y la última tiene saldo `1000.00` |
| 4 | Cambiar el formato a "XLSX", tocar "Exportar" y medir | La descarga inicia en 5 segundos o menos [SUPUESTO: (P-4)] |
| 5 | Abrir el XLSX y contar las filas de datos | Hay 1.000 filas y la última tiene saldo `1000.00` |
| 6 | Cambiar el formato a "PDF", tocar "Exportar" y medir | La descarga inicia en 5 segundos o menos [SUPUESTO: (P-4)] |
| 7 | Abrir el PDF y leer el saldo de la última fila | Es `1.000,00` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Tiempos medidos por formato; archivos |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-4) umbral de 5 s para 1.000 movimientos]`. |

---

### CP-036 — Verificar que una cuenta con exactamente 10.000 movimientos se exporta en CSV (máximo permitido)

| Campo | Valor |
|---|---|
| **Título** | Verificar que una cuenta con exactamente 10.000 movimientos se exporta en CSV (máximo permitido) |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; cuenta DM-8 `0055550002` (10.000 movimientos de +1.00, saldo final 10000.00); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0055550002`; desde `01/01/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0055550002`, fechas `01/01/2026` a `30/09/2026` y formato CSV | Los datos quedan cargados |
| 2 | Tocar "Exportar" y medir hasta que inicia la descarga | La descarga inicia en 30 segundos o menos [SUPUESTO: (P-4) umbral de 30 s] |
| 3 | Revisar el nombre del archivo | Es `movimientos_0055550002_2026-01-01_2026-09-30.csv` |
| 4 | Contar las líneas del archivo | Hay 10.001 líneas (1 encabezado + 10.000 movimientos) [SUPUESTO: (P-6) máximo 10.000 inclusivo] |
| 5 | Leer la última fila | Su saldo es `10000.00` |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Tiempo medido; conteo de líneas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-4)(P-6)]`. |

---

### CP-037 — Verificar que una cuenta con 10.001 movimientos (sobre el máximo) se rechaza con mensaje de límite

| Campo | Valor |
|---|---|
| **Título** | Verificar que una cuenta con 10.001 movimientos (sobre el máximo) se rechaza con mensaje de límite |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; cuenta DM-8 `0055550003` (10.001 movimientos de +1.00); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0055550003`; desde `01/01/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0055550003`, fechas `01/01/2026` a `30/09/2026` y formato CSV | Los datos quedan cargados |
| 2 | Tocar "Exportar" | Se muestra un mensaje que informa que se superó el máximo de 10.000 movimientos y sugiere acotar el rango [SUPUESTO: (P-6) límite y texto del mensaje a definir] |
| 3 | Revisar la carpeta de descargas | No hay ningún archivo (ni truncado a 10.000 filas) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje; carpeta de descargas |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-6) máximo 10.000 y rechazo sin archivo]`. Importante: un truncado silencioso sería un defecto grave para la conciliación. |

---

### CP-038 — Verificar que una cuenta con 10.000 movimientos se exporta en PDF paginado y completo

| Campo | Valor |
|---|---|
| **Título** | Verificar que una cuenta con 10.000 movimientos se exporta en PDF paginado y completo |
| **Módulo** | Home banking / Movimientos / Exportación |
| **Origen** | HU-202 · CA-2 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; cuenta `0055550002` (10.000 movimientos de +1.00); carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0055550002`; desde `01/01/2026`; hasta `30/09/2026`; formato PDF |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Cargar cuenta `0055550002`, fechas `01/01/2026` a `30/09/2026` y formato PDF | Los datos quedan cargados |
| 2 | Tocar "Exportar" y medir | La descarga inicia en 30 segundos o menos [SUPUESTO: (P-4)] |
| 3 | Abrir el PDF | Abre sin error de lectura |
| 4 | Ir a la última página | La última fila tiene saldo `10.000,00` |
| 5 | Revisar los encabezados de columna en la segunda página | Se repiten los encabezados de columna en cada página [SUPUESTO: (P-1) layout del PDF] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Tiempo; screenshots de primera y última página |
| **Estado** | Pendiente |
| **Notas** | `[SUPUESTO: (P-1)(P-4)]`. Encabezados repetidos es un supuesto de usabilidad, no un requisito de la HU: si no se confirma, ignorar el paso 5. |

---

### CP-039 — Verificar que el flujo completo de exportación se puede realizar solo con teclado

| Campo | Valor |
|---|---|
| **Título** | Verificar que el flujo completo de exportación se puede realizar solo con teclado |
| **Módulo** | Home banking / Movimientos / Exportación (accesibilidad) |
| **Origen** | Exploratorio (accesibilidad, relacionado con CA-1) |
| **Tipo** | No funcional |
| **Prioridad** | Baja |
| **Precondiciones** | Sesión iniciada con `qa.cliente01`; pantalla "Movimientos" abierta; sin usar el mouse; carpeta de descargas vacía |
| **Datos de prueba** | Cuenta `0012345678`; desde `01/09/2026`; hasta `30/09/2026`; formato CSV |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Presionar Tab hasta llegar al selector de cuenta | El foco es visible y el orden de tabulación es: cuenta, desde, hasta, formato, "Exportar" |
| 2 | Elegir `0012345678` con las flechas y Enter | La cuenta queda seleccionada |
| 3 | Tipear `01/09/2026` en "Desde" y `30/09/2026` en "Hasta" | Ambos campos muestran los valores |
| 4 | Elegir "CSV" con teclado | "CSV" queda seleccionado |
| 5 | Llevar el foco a "Exportar" y presionar Enter | Se descarga `movimientos_0012345678_2026-09-01_2026-09-30.csv` |
| 6 | Repetir con la cuenta `0011112222` hasta presionar Enter en "Exportar" | El mensaje "No hay movimientos para el rango seleccionado." es visible y el foco no queda atrapado |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Grabación de pantalla del recorrido |
| **Estado** | Pendiente |
| **Notas** | Exploratorio: la HU no define accesibilidad. Anunciar el mensaje a lectores de pantalla queda a definir. |

---

## 4. Priorización por riesgo

Matriz (F5): Prob. Alta/Media × Impacto Alto = Alta; Prob. Alta × Impacto Medio = Alta; Prob. Media × Impacto Medio = Media; Prob. Baja × Impacto Alto/Medio = Media; Prob. Alta × Impacto Bajo = Media; Prob. Media/Baja × Impacto Bajo = Baja.

| Caso | Prob. del defecto | Impacto si falla | Prioridad | Humo |
|---|---|---|---|---|
| CP-001 | Media | Alto | Alta | Sí |
| CP-002 | Media | Alto | Alta | Sí |
| CP-003 | Media | Alto | Alta | Sí |
| CP-004 | Media | Alto | Alta | |
| CP-005 | Media | Alto | Alta | |
| CP-006 | Media | Medio | Media | |
| CP-007 | Alta | Alto | Alta | |
| CP-008 | Media | Alto | Alta | |
| CP-009 | Media | Medio | Media | |
| CP-010 | Media | Medio | Media | |
| CP-011 | Media | Medio | Media | Sí |
| CP-012 | Media | Medio | Media | |
| CP-013 | Media | Bajo | Baja | |
| CP-014 | Baja | Bajo | Baja | |
| CP-015 | Media | Bajo | Baja | |
| CP-016 | Media | Bajo | Baja | |
| CP-017 | Media | Medio | Media | |
| CP-018 | Media | Bajo | Baja | |
| CP-019 | Media | Medio | Media | |
| CP-020 | Baja | Bajo | Baja | |
| CP-021 | Media | Alto | Alta | |
| CP-022 | Baja | Alto | Media | |
| CP-023 | Media | Alto | Alta | |
| CP-024 | Media | Medio | Media | |
| CP-025 | Media | Alto | Alta | |
| CP-026 | Baja | Alto | Media | |
| CP-027 | Media | Medio | Media | |
| CP-028 | Media | Medio | Media | |
| CP-029 | Media | Medio | Media | |
| CP-030 | Baja | Medio | Media | |
| CP-031 | Media | Medio | Media | |
| CP-032 | Baja | Medio | Media | |
| CP-033 | Alta | Alto | Alta | |
| CP-034 | Media | Medio | Media | |
| CP-035 | Media | Medio | Media | |
| CP-036 | Media | Medio | Media | |
| CP-037 | Media | Medio | Media | |
| CP-038 | Media | Medio | Media | |
| CP-039 | Baja | Bajo | Baja | |

**Subset de humo (4 casos)**: CP-001 (CSV), CP-002 (XLSX), CP-003 (PDF) y CP-011 (rango sin movimientos).

**Orden de ejecución sugerido**

1. Humo: CP-001, CP-002, CP-003, CP-011.
2. Prioridad Alta: CP-004, CP-005, CP-007, CP-008, CP-033 (depende de CP-001), CP-021, CP-023, CP-025.
3. Prioridad Media: CP-006, CP-009, CP-010, CP-012, CP-017, CP-019, CP-022 (después de CP-021), CP-024, CP-026, CP-027, CP-028, CP-029, CP-030, CP-031, CP-032, CP-034 (después de CP-002 y CP-003), CP-035, CP-036, CP-037, CP-038.
4. Prioridad Baja: CP-013, CP-014, CP-015, CP-016, CP-018, CP-020, CP-039.

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Seleccionar cuenta, rango de fechas y formato, y tocar "Exportar" | CP-001, CP-002, CP-003, CP-006, CP-007, CP-009, CP-010, CP-013, CP-014, CP-015, CP-016, CP-017, CP-018, CP-019, CP-020, CP-021, CP-022, CP-024, CP-026, CP-029, CP-031, CP-039 | ✓ Cubierta |
| CA-2 | Se genera el archivo rápidamente con fecha, descripción, importe y saldo del período | CP-001, CP-002, CP-003, CP-004, CP-005, CP-007, CP-008, CP-009, CP-010, CP-025, CP-027, CP-028, CP-030, CP-032, CP-033, CP-034, CP-035, CP-036, CP-037, CP-038 | ✓ Cubierta (el criterio "rápidamente" depende del supuesto P-4) |
| CA-3 | Nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>` | CP-001, CP-002, CP-003, CP-004, CP-005, CP-023, CP-032 | ✓ Cubierta (formato del nombre depende del supuesto P-3) |
| CA-4 | Rango sin movimientos muestra un mensaje adecuado | CP-011, CP-012, CP-039 | ✓ Cubierta (texto del mensaje depende del supuesto P-5) |
| Nota | Importes en la moneda de la cuenta (ARS o USD) | CP-001, CP-003, CP-004, CP-005 | ✓ Cubierta |

**Cobertura: 4 CAs cubiertas / 4 CAs totales = 100 %.** CAs sin cubrir: ninguna.

## 6. Supuestos asumidos

Todos figuran como `[SUPUESTO: ...]` en los casos y tienen su pregunta con default.

| Pregunta | Supuesto | Casos afectados |
|---|---|---|
| P-1 | Columnas `Fecha`, `Descripción`, `Importe (<moneda>)`, `Saldo (<moneda>)`; fechas `AAAA-MM-DD`; importes con punto decimal, 2 decimales, sin miles, `-` en débitos; CSV con coma y UTF-8 con BOM; XLSX con celdas numéricas; PDF con formato es-AR, encabezado con cuenta, moneda y período, encabezados repetidos por página; la moneda se indica en los encabezados | CP-001 a CP-005, CP-033, CP-034, CP-038 |
| P-2 | Extremos inclusivos; desde <= hasta; hasta <= hoy; máximo 365 días; cuenta, desde, hasta y formato obligatorios y sin default; fechas `dd/mm/aaaa` ingresables por teclado; conservar selección al cambiar de cuenta | CP-006 a CP-010, CP-013 a CP-020, CP-024 |
| P-3 | `<cuenta>` = número de 10 dígitos con ceros; fechas `AAAA-MM-DD`; extensión en minúsculas | CP-001 a CP-010 y los demás que verifican nombre de archivo |
| P-4 | "Rápidamente" = 5 s hasta 1.000 movimientos y 30 s hasta 10.000, medido hasta el inicio de descarga | CP-035, CP-036, CP-038 |
| P-5 | Mensaje "No hay movimientos para el rango seleccionado."; no se descarga archivo; se conserva la selección; igual en los 3 formatos | CP-011, CP-012, CP-039 |
| P-6 | Saldo = saldo posterior al movimiento; orden cronológico ascendente; solo movimientos contabilizados; máximo 10.000 movimientos con rechazo y mensaje si se excede | CP-001, CP-008, CP-036, CP-037 |
| P-7 | Solo cuentas propias; cuentas cerradas no listadas; rechazo 401/403/404 sin datos; descarga solo por la sesión que la pidió (si es por URL); validación server-side; descripciones tipo fórmula neutralizadas con `'` | CP-021 a CP-026 |
| P-8 | Mensaje genérico "No pudimos generar el archivo. Intentá nuevamente."; sin archivo parcial; selección conservada; segundo click ignorado; sesión vencida redirige al login; canal web | CP-027 a CP-031 |

## 7. Auto-revisión

Se ejecutó `checklist-auto-revision.md` (sección Casos de prueba). Durante la corrida se detectó y corrigió un cálculo erróneo en CP-002 (ver abajo).

**Críticos**

- [x] **Cada CA tiene ≥1 caso**: CA-1 (22 casos), CA-2 (20), CA-3 (7), CA-4 (3). Ningún CA en "sin cobertura".
- [x] **Cero comportamiento inventado**: todo resultado esperado no definido por la HU (formato, nombre, mensajes, límites, errores, seguridad) lleva `[SUPUESTO: ...]` con referencia a P-N; CP-039 está marcado como exploratorio.
- [x] **Pasos reproducibles por terceros**: pasos atómicos con cuentas, fechas, formatos y datos exactos (DM-1 a DM-8 y tabla de movimientos).
- [x] **Resultados esperados observables**: nombre de archivo, contenido fila por fila, mensajes, conteo de archivos/líneas, códigos de respuesta.
- [x] **IDs únicos y secuenciales**: CP-001 a CP-039 sin huecos (39 casos).
- [x] **Matriz de cobertura completa**: 4/4 = 100 %, verificada contra los casos listados.
- [x] **Preguntas al PO ≤ 8**: 8 preguntas, todas con default propuesto, ninguna trivial.

**Observaciones**

- [x] ≥1 negativo/borde por funcionalidad de riesgo: hay 7 positivos (CP-001 a CP-006 y CP-011) frente a más de 30 casos negativos, de borde, de excepción y no funcionales; supera la guía de 1 negativo/borde cada 2 positivos.
- [x] Prioridades derivadas de la matriz prob × impacto (sección 4).
- [x] Subset de humo marcado: CP-001, CP-002, CP-003, CP-011.
- [x] Sin casos duplicados: CP-001/CP-007/CP-008 usan rangos y assertions distintos; CP-013 a CP-016 validan campos distintos; CP-033 valida el parseo, no el contenido textual de CP-001.
- [x] Dependencias declaradas en Precondiciones: CP-022 (CP-021), CP-033 (CP-001), CP-034 (CP-002 y CP-003).
- [x] Supuestos consolidados en la sección 6.

**Falla detectada y corregida en la corrida**: en CP-002, paso 9, la primera redacción tenía un total mal calculado (906679.95). Se verificó la suma (850000.00 + 120000.50 - 48320.55 - 10000.00 - 3500.00 = 908179.95) y el caso quedó con el valor correcto.

**Observaciones conocidas no corregidas**

- Compatibilidad de navegadores y dispositivos móviles no está cubierta: el canal soportado no está definido (P-8), se asumió web de escritorio.
- Los casos CP-013, CP-014, CP-020 y CP-023 pueden pasar a "No aplicable" según la respuesta a P-2 y P-7.
- Fechas relativas a HOY (2026-10-09) en CP-009, CP-010, CP-018, CP-019 y CP-024: deben recalcularse si se ejecutan otro día.
