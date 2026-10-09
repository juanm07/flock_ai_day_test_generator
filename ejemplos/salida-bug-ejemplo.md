# BUG-001 — [Login] Error al iniciar sesión con contraseñas que contienen "ñ"

> Salida esperada del flujo reporte→bug para `ejemplos/reporte-suelto-ejemplo.md`. Ejemplo sintético de calibración.

---

| Campo | Valor |
|---|---|
| **Título** | [Login] Error al iniciar sesión con contraseñas que contienen "ñ" |
| **Severidad** | S2 (Mayor) — **preliminar**, ver justificación |
| **Prioridad** | P2 |
| **Ambiente** | Aplicación: `[PENDIENTE: versión/build de staging]` · Entorno: Staging · Plataforma: Chrome `[PENDIENTE: confirmar versión]` |
| **Reportado por / Fecha** | Soporte (por chat interno) · "desde ayer" `[PENDIENTE: fecha exacta y deploy previo]` |
| **Reproducibilidad** | Siempre (3 de 3 intentos reportados por el usuario) |
| **Usuario/Rol afectado** | Usuario final con contraseña que contiene "ñ" (`jperez@empresa.com`) |

**Precondiciones**

- Cuenta con contraseña registrada que contiene al menos una "ñ".
- App desplegada en staging en su versión actual `[PENDIENTE: versión]`.

**Pasos para reproducir**

| # | Acción |
|---|--------|
| 1 | Ir a la pantalla de login de staging |
| 2 | Ingresar `jperez@empresa.com` |
| 3 | Ingresar la contraseña que contiene "ñ" |
| 4 | Confirmar el login |

**Resultado actual** (solo hechos observados)

- El login es rechazado con un mensaje de error rojo que mencionaba "algo de caracteres no válidos" (paráfrasis del reportero).
- Con una contraseña reseteada sin "ñ", el mismo usuario puede iniciar sesión sin problema.
- Sucedió 3 de 3 veces que probó.

**Resultado esperado**

- El login debe aceptar contraseñas con "ñ" y cualquier otro carácter unicode si fueron aceptadas al crearse `[SUPUESTO: comportamiento razonable; no hay CA que lo defina → candidato a pregunta al PO]`.

**Evidencia**

- `[PENDIENTE: screenshot del mensaje de error]`
- `[PENDIENTE: texto exacto del error — pedir copiarlo literal o captura]`
- `[PENDIENTE: log/network del request rechazado en staging]`

**Impacto**

- Subconjunto de usuarios con "ñ" (u otros caracteres no-ASCII) en su contraseña quedan **fuera de su cuenta**, con workaround no evidente (resetear la contraseña a una sin "ñ" — solo lo halló el reportero por su cuenta).

**Hipótesis / Notas** (separado de los hechos)

- **Hipótesis 1 (del reportero, razonable):** la "ñ" dispara el rechazo. Consistente con que la misma cuenta entra con contraseña ASCII.
- **Hipótesis 2 (del agente):** regresión de un cambio reciente: la contraseña con "ñ" se creó hace meses y funcionaba → algo cambió del lado de validación/encoding "desde ayer". Verificar últimos deploys.
- **Hipótesis 3 (del agente):** si el reset acepta contraseñas con "ñ" pero el login las rechaza, hay una inconsistencia de charset entre dos endpoints.

**Información faltante**

- Versión/build de staging y si hubo deploy en las últimas 48 h.
- Texto exacto del error y screenshot.
- Reproducción en otros navegadores (Firefox no probado).
- Si también falla el **restablecimiento** hacia una contraseña con "ñ" (distingue validación de login vs. de creación).

---

## Justificación de clasificación

- **Severidad S2 (Mayor), preliminar**: funcionalidad clave (login) bloqueada para un subconjunto de usuarios (los que tienen "ñ" en su contraseña); existe workaround (resetear contraseña), pero no es evidente y el usuario promedio no lo va a hallar solo. **Condicionada a**: confirmar si afecta a todos los usuarios con caracteres especiales o solo a casos puntuales (si solo fuera 1 usuario y con datos corruptos, bajaría a S3).
- **Prioridad P2**: posible regresión reciente en flujo crítico de acceso, en staging. Sube a P1 si se confirma que llega a producción o que afecta a todos los usuarios con caracteres no-ASCII.

---

## Preguntas de seguimiento

1. **[Ambiente]** ¿Qué versión/build está desplegada en staging y hubo deploy en las últimas 48 h?
2. **[Evidencia]** ¿Podés copiar el texto exacto del error o mandar una captura?
3. **[Repro]** ¿Falla también en Firefox u otros navegadores, o solo en Chrome?
4. **[Alcance]** ¿Podemos probar con otra cuenta que tenga "ñ" en la contraseña (o acentos/emoji) para medir el alcance real?
5. **[Creación vs. login]** ¿El restablecimiento a una contraseña CON "ñ" funciona? (si falla también, el bug es de la validación compartida; si no, es solo del login)

---

## Auto-revisión

| Ítem | Resultado |
|---|---|
| Título autónomo con módulo y síntoma | ✓ |
| Pasos reproducibles por terceros | ✓ (reconstruidos del reporte, sin pasos inventados) |
| Resultado actual = solo hechos | ✓ Paráfrasis del error marcada como tal |
| Hipótesis separadas de hechos | ✓ 3 hipótesis etiquetadas (1 del reportero, 2 del agente) |
| Severidad justificada y preliminar si condicionada | ✓ S2 preliminar + condición |
| Faltantes con `[PENDIENTE]` + pregunta específica | ✓ 3 faltantes críticos mapeados a preguntas 1-3 |
| Cero datos inventados de ambiente/versión | ✓ |
| Reporte original citado | ✓ Abajo |

---

> **Reporte original (Soporte, chat interno):**
> "che tengo un problema con el login de staging... desde ayer más o menos. pongo mi contraseña (que tiene una ñ porque me gusta complicarme jaja) y me tira un error rojo que decía algo de caracteres no válidos. pero esa contraseña la uso hace meses! después probé reseteando la contraseña a una sin ñ y ahí pude entrar sin problema. no me acuerdo bien qué decía el error exacto. estoy en chrome, la última versión creo. me pasó las 3 veces que probé. ah, en firefox no lo probé porque ahí nunca me logueo. mi usuario es jperez arroba empresa punto com. no tengo captura, disculpá"
