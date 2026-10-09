# Estabilidad de la extracción — HU-202

| Condición | Modelos | Frames por modelo | CV frames | Jaccard frame_id | Jaccard firmas tipo×CA×técnica |
|---|---|---|---|---|---|
| A. única, prompt v1 | 3 | 19, 22, 16 | 0.129 | 0.22 | 0.401 |
| B. única, prompt v2 | 9 | 20, 21, 19, 21, 17, 21, 24, 19, 19 | 0.092 | 0.392 | 0.723 |
| C. consenso 3× v2 | 3 | 19, 21, 19 | 0.048 | 0.879 | 0.879 |

Parámetros por modelo:
- A. única, prompt v1: cuenta, disponibilidad_servicio, fecha_desde, fecha_hasta, formato, movimientos_periodo
- A. única, prompt v1: cuenta, fecha_desde, fecha_hasta, formato, generacion_archivo, movimientos_en_rango
- A. única, prompt v1: cuenta, formato, generacion_archivo, rango_fechas
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- B. única, prompt v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- C. consenso 3× v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- C. consenso 3× v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
- C. consenso 3× v2: cuenta, fecha_desde, fecha_hasta, formato, movimientos_en_rango
