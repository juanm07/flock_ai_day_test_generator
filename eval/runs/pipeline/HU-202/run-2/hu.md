## HU-202 — Exportación de movimientos de cuenta

**Como** cliente de home banking,
**quiero** exportar los movimientos de mi cuenta en un rango de fechas,
**para** conciliarlos con mi sistema contable.

**Criterios de aceptación:**

1. Desde "Movimientos", el cliente selecciona una cuenta, un rango de fechas (desde/hasta) y un formato (CSV, XLSX o PDF) y toca "Exportar".
2. El sistema genera el archivo rápidamente con los movimientos del período, incluyendo fecha, descripción, importe y saldo.
3. El archivo se descarga con el nombre `movimientos_<cuenta>_<desde>_<hasta>.<ext>`.
4. Si el rango no tiene movimientos, el sistema muestra un mensaje adecuado.

**Notas del equipo:** los importes se muestran en la moneda de la cuenta (ARS o USD).
