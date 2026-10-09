# BUG-001 — [Login] Error al iniciar sesión con contraseñas que contienen "ñ"

> Generado por `tbg bug-check`: cada hecho cita el reporte original (verificado por código); severidad y prioridad
> calculadas con `rules/severity.yaml`.

| Campo | Valor |
|---|---|
| **Título** | [Login] Error al iniciar sesión con contraseñas que contienen "ñ" |
| **Severidad** | S2 — **preliminar** |
| **Prioridad** | P2 — **preliminar** |
| **Ambiente** | Aplicación: `[PENDIENTE: Versión/build de la app]` · Entorno: Staging · Plataforma: Chrome (última versión) `[PENDIENTE: confirmar — el reportero dijo «creo»]` |
| **Reportado por / Fecha** | Soporte (chat interno) · Desde ayer `[PENDIENTE: confirmar — el reportero dijo «más o menos»]` |
| **Reproducibilidad** | Siempre: 3 de 3 intentos |
| **Usuario/Rol afectado** | jperez@empresa.com, usuario con "ñ" en la contraseña |

**Pasos para reproducir**

| # | Acción |
|---|--------|
| 1 | Ir a la pantalla de login de staging |
| 2 | Ingresar el usuario jperez@empresa.com |
| 3 | Ingresar la contraseña que contiene "ñ" |
| 4 | Confirmar el login _(reconstruido)_ |

**Resultado actual** (solo hechos observados)

- Al ingresar una contraseña que contiene "ñ", el login muestra un error rojo
- Tras resetear a una contraseña sin "ñ", el mismo usuario inicia sesión
- Texto del error: `[PENDIENTE: texto literal del error]` (paráfrasis del reportero: «decía algo de caracteres no válidos»)

**Resultado esperado**

- `[SUPUESTO: comportamiento razonable — candidato a pregunta al PO]`

**Evidencia**

- `[PENDIENTE: captura, video o log del error]`

**Impacto**

- Subconjunto de usuarios; bloquea un flujo crítico (existe workaround).

**Hipótesis / Notas** (separado de los hechos)

- **Hipótesis 1 (del reportero):** La "ñ" de la contraseña dispara el rechazo
- **Hipótesis 2 (del agente):** Regresión reciente: la contraseña con "ñ" funcionaba hace meses y falla desde ayer; revisar deploys recientes
- **Hipótesis 3 (del agente):** Inconsistencia de charset entre el endpoint de reset (acepta "ñ") y el de login (la rechaza)

---

## Justificación de clasificación

- **Severidad S2 (preliminar)**: Funcionalidad clave degradada: hay workaround o afecta a un subconjunto de usuarios. **Condicionada a**: confirmar `data_loss` (si fuera cierto → S1).
- **Prioridad P2 (preliminar)**: Contexto «default» × S2 → P2. **Podría cambiar si**: `data_loss` → P1; `regression` → P1; `before_release` → P1.
- **Features con evidencia**: `blocks_critical_flow=true` («tengo un problema con el login»); `workaround_exists=true` («reseteando la contraseña a una sin ñ y ahí pude entrar»); `affects_subset_only=true` («que tiene una ñ»); `cosmetic_only=false` («me tira un error rojo»); `in_production=false` («el login de staging»).
- **Desconocidas** (el reporte no lo dice): data_loss, security, regression, before_release.

## Información faltante y preguntas de seguimiento

1. **[Resultado esperado (EB)]** _(crítico)_ ¿Qué esperabas que pasara?
2. **[Texto literal del error]** _(crítico)_ ¿Podés copiar el texto exacto del error o mandar una captura?
3. **[Versión/build de la app]** _(crítico)_ ¿Qué versión/build estaba desplegada y hubo un deploy reciente?
4. **[Evidencia]** ¿Tenés captura, video o log del momento del error?
5. **[Confirmar since (el reportero dijo «más o menos»)]** Sobre «desde ayer más o menos»: ¿podés confirmarlo?
6. **[Confirmar environment.platform (el reportero dijo «creo»)]** Sobre «estoy en chrome, la última versión creo»: ¿podés confirmarlo?

## Auto-revisión (`tbg bug-check`)

| Ítem | Crítico | Resultado |
|---|---|---|
| B1 — Cero hechos sin cita verificable en el reporte | Sí | ✓ |
| B2 — Título autónomo [Módulo] + síntoma | Sí | ✓ [Login] Error al iniciar sesión con contraseñas que contienen "ñ" |
| B3 — Cada faltante crítico tiene [PENDIENTE] + pregunta | Sí | ✓ 3 faltantes críticos con pregunta |
| B4 — Severidad justificada (y preliminar si depende de faltantes) | Sí | ✓ S2 preliminar: Funcionalidad clave degradada: hay workaround o afecta a un subconjunto de usuarios. |
| B5 — Cero datos de ambiente/versión inventados | Sí | ✓ |
| B6 — Hipótesis separadas de hechos (hechos dudosos marcados) | No | ✓ 3 hipótesis; 3 hechos 'a confirmar' |
| B7 — Pasos con respaldo en el reporte | No | ✗ paso 4 reconstruido sin cita |

**Gate: APROBADO.**

---

> **Reporte original:**
> che tengo un problema con el login de staging... desde ayer más o menos. pongo mi contraseña (que tiene una ñ porque me gusta complicarme jaja) y me tira un error rojo que decía algo de caracteres no válidos. pero esa contraseña la uso hace meses! después probé reseteando la contraseña a una sin ñ y ahí pude entrar sin problema. no me acuerdo bien qué decía el error exacto. estoy en chrome, la última versión creo. me pasó las 3 veces que probé. ah, en firefox no lo probé porque ahí nunca me logueo. mi usuario es jperez arroba empresa punto com. no tengo captura, disculpá

