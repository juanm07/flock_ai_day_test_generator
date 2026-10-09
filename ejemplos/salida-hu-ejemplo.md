# Suite de pruebas — HU-101: Recuperación de contraseña

> Salida esperada del flujo HU→casos para `ejemplos/hu-ejemplo.md`. Ejemplo sintético de calibración: define el nivel de detalle, formato y rigor esperados.

---

## 1. Resumen del análisis

- **Rol**: usuario registrado que olvidó su contraseña.
- **Funcionalidad**: restablecer contraseña mediante enlace enviado por email.
- **Objetivo de negocio**: volver a acceder a su cuenta sin perder datos (autonomía del usuario; evita tickets a soporte).
- **Criterios de aceptación detectados:**
  - **CA-1**: Solicitar recuperación desde el login ingresando el email → mensaje genérico "Si el email existe, recibirás un enlace...".
  - **CA-2**: El sistema envía al email un enlace de restablecimiento.
  - **CA-3**: Desde el enlace se define una nueva contraseña y el sistema confirma la actualización.
  - **CA-4**: La nueva contraseña permite iniciar sesión.
- **Entidades y datos**: cuenta de usuario activa con email; servicio de notificaciones (dependencia externa para CA-2).
- **Riesgos identificados de entrada**: funcionalidad de autenticación → seguridad es heurística obligatoria (enumeración de usuarios, rate limiting). Comportamiento indefinido en: expiración del enlace, política de contraseña, límites de solicitudes, invalidación de enlaces previos, sesiones activas → ver preguntas P-1 a P-8.
- **Modo elegido**: completo. No hay gaps bloqueantes: el happy path es diseñable; los indefinidos se cubren con supuestos marcados y casos exploratorios.

## 2. Preguntas para el PO

**P-1. [E. Estados] ¿Cuánto tiempo es válido el enlace de restablecimiento?**
- **Por qué importa**: sin expiración, un enlace filtrado (email reenviado, bandeja compartida) permite tomar la cuenta indefinidamente.
- **Default propuesto**: 24 horas, con pantalla de "enlace expirado" y opción de solicitar uno nuevo.

**P-2. [B. Datos] ¿Cuál es la política de la nueva contraseña?**
- **Por qué importa**: define los negativos de CA-3 y el mensaje de error esperado; además una política inexistente es riesgo de seguridad.
- **Default propuesto**: mínimo 8 caracteres, al menos 1 mayúscula y 1 número (consistente con la política de registro si existe).

**P-3. [F. Seguridad] ¿Hay límite de solicitudes de recuperación por email/IP?**
- **Por qué importa**: sin límite, el flujo es vector de spam y de bombardeo de emails (mail bombing).
- **Default propuesto**: máximo 3 solicitudes por hora por email + captcha a partir de la 3ª.

**P-4. [E. Estados] Al solicitar un nuevo enlace, ¿se invalidan los anteriores?**
- **Por qué importa**: define si puede haber varios enlaces activos simultáneos (superficie de ataque).
- **Default propuesto**: el último enlace invalida todos los anteriores (un solo enlace activo por usuario).

**P-5. [G. Concurrencia] Al completar el restablecimiento, ¿se cierran las sesiones activas en otros dispositivos?**
- **Por qué importa**: escenario de cuenta comprometida: el reset debería expulsar al intruso.
- **Default propuesto**: sí, se invalidan todas las sesiones activas.

**P-6. [E. Estados] ¿Qué pasa si la cuenta está bloqueada o desactivada?**
- **Por qué importa**: define si el reset "revive" cuentas bloqueadas por seguridad.
- **Default propuesto**: mensaje genérico igual que para cualquier email, pero sin enviar enlace; las cuentas bloqueadas no se desbloquean por este flujo.

**P-7. [J. Contexto] ¿En qué idiomas se envía el email? ¿Qué navegadores/dispositivos se soportan?**
- **Por qué importa**: define alcance de i18n y compatibilidad de CA-2/CA-3.
- **Default propuesto**: español por ahora (sin i18n en v1); Chrome/Firefox/Safari desktop + Chrome móvil.

**P-8. [J. Contexto] ¿El flujo de recuperación debe ser navegable por teclado?**
- **Por qué importa**: accesibilidad del formulario; es criterio de "done" en algunos equipos.
- **Default propuesto**: sí, mínimo navegable por teclado con foco visible.

## 3. Casos de prueba

### CP-001 — Verificar que un usuario registrado puede solicitar la recuperación de contraseña

| Campo | Valor |
|---|---|
| **Título** | Verificar que un usuario registrado puede solicitar la recuperación de contraseña |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | Existe la cuenta activa `qa.usuario01@empresa.com`; app en pantalla de login |
| **Datos de prueba** | Email: `qa.usuario01@empresa.com` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En el login, tocar "Olvidé mi contraseña" | Se muestra el formulario de recuperación con campo de email |
| 2 | Ingresar `qa.usuario01@empresa.com` y confirmar | Se muestra exactamente "Si el email existe, recibirás un enlace para restablecer tu contraseña" |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del formulario (paso 1) y del mensaje (paso 2) |
| **Estado** | Pendiente |
| **Notas** | La recepción del email se valida en CP-002, no acá. Humo. |

### CP-002 — Verificar que el email llega y permite definir una nueva contraseña

| Campo | Valor |
|---|---|
| **Título** | Verificar que el email llega y permite definir una nueva contraseña |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-2, CA-3 |
| **Tipo** | E2E |
| **Prioridad** | Alta |
| **Precondiciones** | CP-001 ejecutado con éxito hace menos de 24 h `[SUPUESTO: vigencia del enlace, ver P-1]` |
| **Datos de prueba** | Nueva contraseña: `Reset2024ok` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la bandeja de `qa.usuario01@empresa.com` y localizar el email de recuperación | El email llega en < 5 minutos, con remitente del producto y un enlace visible |
| 2 | Abrir el enlace | Se muestra el formulario "Definí tu nueva contraseña" con el estado de sesión de recuperación iniciado |
| 3 | Ingresar `Reset2024ok` en ambos campos (nueva y repetir) y confirmar | El sistema muestra confirmación de que la contraseña se actualizó |
| 4 | Verificar redirección | Se llega a la pantalla de login |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del email (paso 1), del formulario (paso 2) y de la confirmación (paso 3) |
| **Estado** | Pendiente |
| **Notas** | Humo. La contraseña `Reset2024ok` cumple la política asumida `[SUPUESTO: política, ver P-2]`. Dependencia: servicio de notificaciones. |

### CP-003 — Verificar que el login funciona con la contraseña nueva y rechaza la vieja

| Campo | Valor |
|---|---|
| **Título** | Verificar que el login funciona con la contraseña nueva y rechaza la vieja |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-4 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | CP-002 ejecutado con éxito (contraseña actual = `Reset2024ok`); contraseña anterior documentada en Notas |
| **Datos de prueba** | Email: `qa.usuario01@empresa.com` · Nueva: `Reset2024ok` · Vieja: (la anterior del setup) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En el login, ingresar `qa.usuario01@empresa.com` + `Reset2024ok` y confirmar | Se inicia sesión y se llega al home de la cuenta |
| 2 | Cerrar sesión | Se vuelve al login |
| 3 | Intentar login con `qa.usuario01@empresa.com` + contraseña anterior | El login es rechazado con mensaje de credenciales inválidas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del home (paso 1) y del rechazo (paso 3) |
| **Estado** | Pendiente |
| **Notas** | Humo. El paso 3 también es control de seguridad: la credencial vieja debe morir al resetear. |

### CP-004 — Verificar que un email no registrado recibe el mismo mensaje que uno registrado

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email no registrado recibe el mismo mensaje que uno registrado |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Negativo (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | El email `inexistente@empresa.com` NO existe en el sistema |
| **Datos de prueba** | Email: `inexistente@empresa.com` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En "Olvidé mi contraseña", ingresar `inexistente@empresa.com` y confirmar | Se muestra el mismo mensaje genérico "Si el email existe, recibirás un enlace..." (idéntico al de CP-001, paso 2) |
| 2 | Revisar la bandeja de `inexistente@empresa.com` | No llega ningún email |
| 3 | Comparar el tiempo de respuesta con CP-001 | No hay diferencia visible que permita deducir si el email existe |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje (paso 1); bandeja vacía (paso 2) |
| **Estado** | Pendiente |
| **Notas** | Anti-enumeración de usuarios: el sistema no debe revelar qué emails existen. Relacionado con P-6 (cuentas bloqueadas). |

### CP-005 — Verificar el rechazo de emails con formato inválido o vacíos

| Campo | Valor |
|---|---|
| **Título** | Verificar el rechazo de emails con formato inválido o vacíos |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | App en el formulario de recuperación |
| **Datos de prueba** | `usuario@` · `@empresa.com` · `sin-arroba` · `` (vacío) · `   ` (solo espacios) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar cada dato inválido de la lista y confirmar (una iteración por dato) | Cada valor es rechazado con mensaje de formato inválido, sin enviarse request al backend `[SUPUESTO: validación estándar de formato en el front]` |
| 2 | Ingresar `` (vacío) y confirmar | Se muestra el mensaje de campo obligatorio |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Un screenshot por dato inválido |
| **Estado** | Pendiente |
| **Notas** | Si algún valor inválido pasa al backend y dispara el envío de email, es hallazgo de seguridad (reportar como bug). |

### CP-006 — Verificar el rechazo de un enlace expirado

| Campo | Valor |
|---|---|
| **Título** | Verificar el rechazo de un enlace expirado |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Existe un enlace solicitado hace más de 24 h `[SUPUESTO: expiración 24 h, ver P-1]` |
| **Datos de prueba** | Enlace generado >24 h antes (usar token viejo o manipular la fecha en el entorno de QA) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el enlace vencido | Se muestra pantalla de "enlace expirado" `[SUPUESTO: pantalla definida en P-1]` |
| 2 | Verificar opciones ofrecidas | La pantalla ofrece solicitar un enlace nuevo |
| 3 | Intentar cambiar la contraseña desde el enlace vencido | No es posible: el formulario no se habilita |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la pantalla de expiración |
| **Estado** | Pendiente |
| **Notas** | Si el enlace vencido permite cambiar la contraseña → bug S1 (seguridad). |

### CP-007 — Verificar el rechazo de contraseñas fuera de la política

| Campo | Valor |
|---|---|
| **Título** | Verificar el rechazo de contraseñas fuera de la política |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Enlace de recuperación vigente abierto en el formulario de nueva contraseña |
| **Datos de prueba** | `abc` (corta) · `abcd1234` (sin mayúscula) · 200 caracteres (excede máximo) · `` (vacía) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar cada valor inválido de la lista y confirmar (una iteración por valor) | Cada valor es rechazado con mensaje que explica la regla incumplida `[SUPUESTO: política = mín. 8 + 1 mayúscula + 1 número, ver P-2]` |
| 2 | Verificar el estado de la cuenta | La contraseña NO se cambió: la anterior sigue siendo válida |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot por valor inválido |
| **Estado** | Pendiente |
| **Notas** | El paso 2 es crítico: un rechazo que igualmente cambia la contraseña sería bug S1. |

### CP-008 — Verificar contraseñas con caracteres especiales y unicode

| Campo | Valor |
|---|---|
| **Título** | Verificar contraseñas con caracteres especiales y unicode |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-3, CA-4 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | Enlace de recuperación vigente; cuenta de prueba con email conocido |
| **Datos de prueba** | `Ñandú2024!` · `P4ssw0rd 🦉 ok` · `contra señal123` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Definir la nueva contraseña `Ñandú2024!` desde el enlace | El sistema acepta la contraseña (cumple la política asumida) |
| 2 | Cerrar sesión y hacer login con `Ñandú2024!` | El login funciona: el encoding se preserva de punta a punta |
| 3 | Repetir pasos 1-2 con los otros dos valores de prueba | Ídem: aceptación en el reset y login exitoso |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del login exitoso por cada contraseña probada |
| **Estado** | Pendiente |
| **Notas** | Si el reset acepta la contraseña pero el login la rechaza (o viceversa), es bug S1: el usuario queda fuera de su cuenta. Es el escenario del bug de ejemplo del flujo B (ver `ejemplos/salida-bug-ejemplo.md`). |

### CP-009 — Verificar la invalidación de enlaces previos y la reutilización

| Campo | Valor |
|---|---|
| **Título** | Verificar la invalidación de enlaces previos y la reutilización |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-2, CA-3 |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | Posibilidad de solicitar dos enlaces para la misma cuenta |
| **Datos de prueba** | Enlace A (solicitado primero) · Enlace B (solicitado después) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar dos enlaces seguidos (Enlace A, luego Enlace B) | Llegan dos emails, ambos con enlace |
| 2 | Abrir el Enlace A | Rechazado / expirado `[SUPUESTO: el último enlace invalida los anteriores, ver P-4]` |
| 3 | Abrir el Enlace B y cambiar la contraseña | El cambio se completa con éxito |
| 4 | Reabrir el Enlace B (ya usado) | Rechazado: no se puede volver a usar el mismo enlace |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de cada rechazo (pasos 2 y 4) |
| **Estado** | Pendiente |
| **Notas** | Si el Enlace A sigue activo tras pedir el B, es hallazgo de seguridad (superficie de ataque) → reportar. |

### CP-010 — Explorar el comportamiento ante solicitudes repetidas (rate limiting)

| Campo | Valor |
|---|---|
| **Título** | Explorar el comportamiento ante solicitudes repetidas (rate limiting) |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 (exploratorio) |
| **Tipo** | No funcional (seguridad) — **exploratorio** |
| **Prioridad** | Baja |
| **Precondiciones** | Email válido registrado; reloj/timestamp para registrar tiempos |
| **Datos de prueba** | 10 solicitudes seguidas para el mismo email en < 1 minuto |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación 10 veces seguidas, registrando qué llega en cada intento | **Comportamiento indefinido por la HU** — documentar lo observado: cantidad de emails recibidos, tiempos, aparición de captcha o límite |
| 2 | Documentar el hallazgo | Si no hay límite ni captcha: reportar como hallazgo de seguridad con la evidencia (relacionado con P-3) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Tabla de las 10 solicitudes (hora, resultado) + bandeja con los emails |
| **Estado** | Pendiente |
| **Notas** | Caso exploratorio: la HU no define el comportamiento (P-3). El entregable de este caso es un hallazgo documentado, no un pass/fail binario. |

## 4. Priorización por riesgo

| Caso | Probabilidad de defecto | Impacto si falla | Prioridad |
|---|---|---|---|
| CP-001 | Baja (happy path básico) | Alto (bloquea todo el flujo) | Alta |
| CP-002 | Media (depende del servicio de emails) | Alto | Alta |
| CP-003 | Media | Alto (acceso a la cuenta) | Alta |
| CP-004 | Media (fácil de errar en el backend) | Alto (fuga de información) | Alta |
| CP-005 | Media | Medio | Media |
| CP-006 | Baja | Alto (seguridad: token eterno) | Media |
| CP-007 | Baja | Medio | Media |
| CP-008 | **Alta** (encoding es suelo fértil de bugs) | Alto (usuario fuera de su cuenta) | Alta |
| CP-009 | Media | Medio | Media |
| CP-010 | Alta (probablemente no existe aún) | Medio (spam/bombing) | Baja |

**Orden de ejecución sugerido:** humo primero (CP-001 → CP-002 → CP-003), luego seguridad (CP-004, CP-008), luego el resto por prioridad (CP-005, CP-006, CP-007, CP-009) y exploración al final (CP-010).

**Subset de humo:** CP-001, CP-002, CP-003.

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Solicitud desde login con mensaje genérico | CP-001, CP-004, CP-005 | ✓ Cubierta |
| CA-2 | Envío del email con enlace | CP-002, CP-009 | ✓ Cubierta |
| CA-3 | Definición de nueva contraseña desde el enlace | CP-002, CP-006, CP-007, CP-008, CP-009 | ✓ Cubierta |
| CA-4 | Login con la nueva contraseña | CP-003, CP-008 | ✓ Cubierta |

**Cobertura: 4/4 CA (100%).**

## 6. Supuestos asumidos

1. `[SUPUESTO: vigencia del enlace = 24 h]` — en CP-002, CP-006. Pendiente P-1.
2. `[SUPUESTO: política de contraseña = mín. 8 caracteres + 1 mayúscula + 1 número]` — en CP-002, CP-007, CP-008. Pendiente P-2.
3. `[SUPUESTO: el último enlace invalida los anteriores]` — en CP-009. Pendiente P-4.
4. `[SUPUESTO: validación estándar de formato de email en el front]` — en CP-005. Pendiente P-7.
5. `[SUPUESTO: el servicio de notificaciones funciona en el entorno de QA]` — precondición de CP-002.

## 7. Auto-revisión

| Ítem | Resultado |
|---|---|
| Cada CA tiene ≥1 caso (o motivo explícito) | ✓ 4/4 cubiertas |
| Cero comportamiento inventado sin `[SUPUESTO]` | ✓ CP-010 marcado exploratorio por indefinición |
| Pasos reproducibles por terceros | ✓ Todos con datos concretos |
| Resultados esperados observables | ✓ |
| IDs únicos y secuenciales | ✓ CP-001 a CP-010 |
| Matriz de cobertura completa y verificada | ✓ 100% |
| ≤8 preguntas al PO, con default | ✓ 8 preguntas |
| ≥1 negativo/borde por funcionalidad con riesgo | ✓ 5 negativos/bordes + 2 excepciones + 1 exploratorio |
| Prioridades justificadas por riesgo | ✓ Tabla en sección 4 |
| Subset de humo marcado | ✓ CP-001..CP-003 |
| Sin casos duplicados | ✓ |
| Supuestos consolidados | ✓ Sección 6 |
