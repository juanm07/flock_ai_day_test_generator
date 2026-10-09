# Suite de pruebas — HU-101: Recuperación de contraseña

> Generada por `tbg` (modelo `639da812022b`). Diseño de casos, IDs, prioridades, cobertura y auto-revisión
> calculados por código; redacción de pasos por el agente, validada por `tbg validate`.

## 1. Resumen del análisis

- **Rol**: usuario registrado que olvidé mi contraseña
- **Funcionalidad**: restablecerla mediante un enlace enviado a mi email
- **Objetivo de negocio**: volver a acceder a mi cuenta sin perder mis datos
- **Módulo**: Autenticación
- **Criterios de aceptación:**
  - **CA-1**: El usuario accede a "Olvidé mi contraseña" desde la pantalla de login, ingresa su email y el sistema muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña".
  - **CA-2**: El sistema envía al email un enlace de restablecimiento.
  - **CA-3**: Al abrir el enlace, el usuario define una nueva contraseña y el sistema confirma que se actualizó.
  - **CA-4**: Con la nueva contraseña, el usuario puede iniciar sesión.
- **Parámetros modelados (Category-Partition)**: `email_ingresado` (4 particiones), `password_nueva` (3 particiones), `enlace` (2 particiones), `login_posterior` (2 particiones)
- **Tags de riesgo**: auth, credential, email, external_dep, pii, token_link, ui
- **Lint de la HU**: sin smells ni problemas de formato detectados.
- **Modo**: completo.

## 2. Preguntas para el PO

**P-1. [B. Datos] ¿Cuál es la política de la credencial (longitud mínima/máxima, caracteres obligatorios y permitidos, unicode)?**
- **Por qué importa**: Define los negativos y bordes del formulario y el mensaje de error esperado; sin política hay riesgo de seguridad.
- **Default propuesto**: Mínimo 8 y máximo 64 caracteres, al menos 1 mayúscula y 1 número; se aceptan unicode y espacios.

**P-2. [E. Estados] ¿Cuánto tiempo es válido el enlace/token y qué ve el usuario si lo usa vencido?**
- **Por qué importa**: Sin expiración, un enlace filtrado (email reenviado, bandeja compartida) da acceso indefinido.
- **Default propuesto**: 24 horas; al usarlo vencido se muestra 'enlace expirado' con opción de pedir uno nuevo.

**P-3. [E. Estados] Al pedir un enlace nuevo, ¿se invalidan los anteriores? ¿El enlace es de un solo uso?**
- **Por qué importa**: Define si puede haber varios enlaces activos a la vez (superficie de ataque) y si se puede reusar.
- **Default propuesto**: El último enlace invalida los anteriores y cada enlace es de un solo uso.

**P-4. [F. Seguridad] ¿Hay límite de intentos/solicitudes por usuario o IP? ¿Qué pasa al superarlo?**
- **Por qué importa**: Sin límite, el flujo es vector de fuerza bruta o de bombardeo de emails.
- **Default propuesto**: Máximo 3 solicitudes por hora por usuario; a partir de la 3ª se pide captcha.

**P-5. [G. Concurrencia] Al cambiar la credencial, ¿se cierran las sesiones activas en otros dispositivos?**
- **Por qué importa**: Escenario de cuenta comprometida: el cambio debería expulsar al intruso.
- **Default propuesto**: Sí, se invalidan todas las sesiones activas excepto la actual.

**P-6. [E. Estados] ¿Qué pasa si la cuenta está bloqueada, desactivada o pendiente de activación?**
- **Por qué importa**: Define si el flujo 'revive' cuentas bloqueadas por seguridad.
- **Default propuesto**: Se muestra el mismo mensaje genérico pero no se ejecuta la acción; la cuenta sigue bloqueada.

**P-7. [C. Errores] ¿Qué ve el usuario si el servicio externo falla o no responde? ¿Se reintenta?**
- **Por qué importa**: Sin definición, un fallo del tercero deja al usuario sin feedback o en un estado inconsistente.
- **Default propuesto**: Mensaje de error genérico con opción de reintentar; no se pierde lo ingresado.

**P-8. [J. Contexto] ¿En qué idiomas se muestra/envía el contenido y qué navegadores/dispositivos se soportan?**
- **Por qué importa**: Define el alcance de i18n y de compatibilidad.
- **Default propuesto**: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil.

**Lagunas ya resueltas** (no se preguntan): `auth.enumeration` — La HU lo define («Si el email existe»)

## 3. Casos de prueba

### CP-001 — Verificar que al solicitar la recuperación con un email registrado se muestra el mensaje genérico y se envía el enlace de restablecimiento

| Campo | Valor |
|---|---|
| **Título** | Verificar que al solicitar la recuperación con un email registrado se muestra el mensaje genérico y se envía el enlace de restablecimiento |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1, CA-2 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario registrado con email qa.usuario01@empresa.com y cuenta activa. Servicio de notificaciones operativo. Acceso a la bandeja de qa.usuario01@empresa.com. |
| **Datos de prueba** | `email_ingresado`: qa.usuario01@empresa.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la pantalla de login | Se muestra el formulario de login con el enlace "Olvidé mi contraseña" |
| 2 | Hacer clic en "Olvidé mi contraseña" | Se muestra el formulario de recuperación con un campo de email |
| 3 | Ingresar qa.usuario01@empresa.com en el campo email | El campo muestra qa.usuario01@empresa.com |
| 4 | Confirmar el envío del formulario | Se muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 5 | Abrir la bandeja de entrada de qa.usuario01@empresa.com | Hay un email con un enlace de restablecimiento de contraseña |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado y del email recibido con el enlace. |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: ac-happy-path._ |

### CP-002 — Verificar que al solicitar la recuperación con un email no registrado se muestra el mismo mensaje genérico

| Campo | Valor |
|---|---|
| **Título** | Verificar que al solicitar la recuperación con un email no registrado se muestra el mismo mensaje genérico |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1, CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | No existe usuario registrado con el email no.registrado@empresa.com. |
| **Datos de prueba** | `email_ingresado`: no.registrado@empresa.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la pantalla de login | Se muestra el formulario de login con el enlace "Olvidé mi contraseña" |
| 2 | Hacer clic en "Olvidé mi contraseña" | Se muestra el formulario de recuperación con un campo de email |
| 3 | Ingresar no.registrado@empresa.com en el campo email | El campo muestra no.registrado@empresa.com |
| 4 | Confirmar el envío del formulario | Se muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña" |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje mostrado. |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: each-choice._ |

### CP-003 — Verificar que un texto sin formato de email en el formulario de recuperación es rechazado

| Campo | Valor |
|---|---|
| **Título** | Verificar que un texto sin formato de email en el formulario de recuperación es rechazado |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1, CA-2 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Pantalla de recuperación de contraseña abierta desde "Olvidé mi contraseña". |
| **Datos de prueba** | `email_ingresado`: usuario.sin.arroba |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar usuario.sin.arroba en el campo email | El campo muestra usuario.sin.arroba |
| 2 | Confirmar el envío del formulario | [SUPUESTO: se muestra un mensaje de error de formato de email y no se envía ningún enlace ni se muestra el mensaje genérico de CA-1] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y verificación de que no llega email. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define la validación de formato de email.] `[SUPUESTO: «Texto sin formato de email» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.email_ingresado.formato_invalido)]` _Técnica: error-choice._ |

### CP-004 — Verificar que enviar el formulario de recuperación con el email vacío es rechazado

| Campo | Valor |
|---|---|
| **Título** | Verificar que enviar el formulario de recuperación con el email vacío es rechazado |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1, CA-2 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Pantalla de recuperación de contraseña abierta desde "Olvidé mi contraseña". |
| **Datos de prueba** | `email_ingresado`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Dejar vacío el campo email (valor vacío) | El campo email no tiene contenido |
| 2 | Confirmar el envío del formulario | [SUPUESTO: se muestra un mensaje de error indicando que el email es obligatorio y no se envía ningún enlace] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define el comportamiento ante email vacío.] `[SUPUESTO: «Campo email vacío» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.email_ingresado.vacio)]` _Técnica: error-choice._ |

### CP-005 — Verificar que la respuesta ante un email inexistente es indistinguible de la de un email existente (anti-enumeración)

| Campo | Valor |
|---|---|
| **Título** | Verificar que la respuesta ante un email inexistente es indistinguible de la de un email existente (anti-enumeración) |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario registrado con email qa.usuario01@empresa.com. No existe usuario con el email no.registrado@empresa.com. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación con qa.usuario01@empresa.com y anotar el mensaje y el tiempo de respuesta | Se muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 2 | Solicitar la recuperación con no.registrado@empresa.com y anotar el mensaje y el tiempo de respuesta | Se muestra el mismo mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña", con texto idéntico al del paso 1 |
| 3 | Revisar la bandeja de no.registrado@empresa.com o los logs del servicio de notificaciones | No se envió ningún email a no.registrado@empresa.com |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas de ambos mensajes y log del servicio de notificaciones. |
| **Estado** | Pendiente |
| **Notas** |  _Técnica: rule:auth.enumeration._ |

### CP-006 — Verificar que solicitar la recuperación con una cuenta bloqueada o desactivada no ejecuta la acción

| Campo | Valor |
|---|---|
| **Título** | Verificar que solicitar la recuperación con una cuenta bloqueada o desactivada no ejecuta la acción |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario bloqueado con email qa.bloqueado01@empresa.com (cuenta bloqueada o desactivada). |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el formulario de recuperación desde "Olvidé mi contraseña" | Se muestra el formulario con el campo email |
| 2 | Ingresar qa.bloqueado01@empresa.com en el campo email | El campo muestra qa.bloqueado01@empresa.com |
| 3 | Confirmar el envío del formulario | [SUPUESTO: se muestra el mismo mensaje genérico "Si el email existe, recibirás un enlace para restablecer tu contraseña" y no se envía ningún enlace] |
| 4 | Intentar iniciar sesión con la cuenta qa.bloqueado01@empresa.com | [SUPUESTO: la cuenta sigue bloqueada y el acceso es rechazado] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje, log de notificaciones y del intento de login. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define el comportamiento con cuentas bloqueadas o desactivadas (account.state).] `[SUPUESTO: Se muestra el mismo mensaje genérico pero no se ejecuta la acción; la cuenta sigue bloqueada. (ver account.state)]` _Técnica: rule:account.state._ |

### CP-007 — Explorar el comportamiento ante solicitudes repetidas de recuperación en poco tiempo (rate limiting)

| Campo | Valor |
|---|---|
| **Título** | Explorar el comportamiento ante solicitudes repetidas de recuperación en poco tiempo (rate limiting) |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | No funcional — **exploratorio** |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario registrado con email qa.usuario01@empresa.com. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación con qa.usuario01@empresa.com una primera vez | Se muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 2 | Repetir la solicitud con el mismo email una segunda vez en menos de 1 hora | Se documenta la respuesta observada |
| 3 | Repetir la solicitud con el mismo email una tercera vez en menos de 1 hora | [SUPUESTO: a partir de la 3ª solicitud por hora se pide captcha] |
| 4 | Repetir la solicitud con el mismo email una cuarta vez en menos de 1 hora | Se documenta el comportamiento observado y la cantidad de emails recibidos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas de cada respuesta y conteo de emails recibidos. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: máximo 3 solicitudes por hora por usuario; a partir de la 3ª se pide captcha (auth.rate_limit).] Caso exploratorio. `[SUPUESTO: Máximo 3 solicitudes por hora por usuario; a partir de la 3ª se pide captcha. (ver auth.rate_limit)]` _Técnica: rule:auth.rate_limit._ |

### CP-008 — Verificar que el flujo de recuperación se completa de igual forma en los navegadores soportados

| Campo | Valor |
|---|---|
| **Título** | Verificar que el flujo de recuperación se completa de igual forma en los navegadores soportados |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | No funcional |
| **Prioridad** | Media |
| **Precondiciones** | Usuario registrado con email qa.usuario01@empresa.com. Disponibles Chrome, Firefox y Safari desktop y Chrome móvil. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En Chrome desktop, solicitar la recuperación con qa.usuario01@empresa.com | Se muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 2 | En Firefox desktop, solicitar la recuperación con qa.usuario01@empresa.com | Se muestra el mismo mensaje que en Chrome |
| 3 | En Safari desktop, solicitar la recuperación con qa.usuario01@empresa.com | Se muestra el mismo mensaje que en Chrome |
| 4 | En Chrome móvil, solicitar la recuperación con qa.usuario01@empresa.com | Se muestra el mismo mensaje que en Chrome desktop, sin elementos cortados ni superpuestos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas por navegador. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: solo español; navegadores soportados Chrome, Firefox y Safari desktop + Chrome móvil (context.platform_i18n).] `[SUPUESTO: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil. (ver context.platform_i18n)]` _Técnica: rule:context.platform_i18n._ |

### CP-009 — Verificar que ante una falla o timeout del servicio de notificaciones el usuario recibe feedback y el sistema queda consistente

| Campo | Valor |
|---|---|
| **Título** | Verificar que ante una falla o timeout del servicio de notificaciones el usuario recibe feedback y el sistema queda consistente |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-2 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario registrado con email qa.usuario01@empresa.com. Servicio de notificaciones simulado como caído o con timeout. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el formulario de recuperación desde "Olvidé mi contraseña" | Se muestra el formulario con el campo email |
| 2 | Ingresar qa.usuario01@empresa.com en el campo email | El campo muestra qa.usuario01@empresa.com |
| 3 | Confirmar el envío del formulario | [SUPUESTO: se muestra un mensaje de error genérico con opción de reintentar] |
| 4 | Verificar el contenido del campo email | [SUPUESTO: el campo conserva qa.usuario01@empresa.com] |
| 5 | Verificar la bandeja de qa.usuario01@empresa.com | No se recibió ningún enlace y la contraseña actual sigue vigente |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error y logs del servicio de notificaciones. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: comportamiento ante falla del servicio externo no definido en la HU (external.failure).] `[SUPUESTO: Mensaje de error genérico con opción de reintentar; no se pierde lo ingresado. (ver external.failure)]` _Técnica: rule:external.failure._ |

### CP-010 — Verificar que al abrir el enlace y definir una nueva contraseña válida el sistema confirma la actualización

| Campo | Valor |
|---|---|
| **Título** | Verificar que al abrir el enlace y definir una nueva contraseña válida el sistema confirma la actualización |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Enlace de restablecimiento vigente recibido en el email del usuario qa.usuario01@empresa.com (generado según CP-001). |
| **Datos de prueba** | `password_nueva`: NuevaClave#2026 · `enlace`: (enlace recibido en el email del usuario) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el enlace de restablecimiento recibido en el email | Se muestra el formulario para definir una nueva contraseña |
| 2 | Ingresar NuevaClave#2026 en el campo de nueva contraseña | El campo acepta el valor ingresado |
| 3 | Confirmar el formulario | Se muestra un mensaje que confirma que la contraseña se actualizó |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la confirmación de actualización. |
| **Estado** | Pendiente |
| **Notas** | Depende de CP-001. _Técnica: ac-happy-path._ |

### CP-011 — Verificar que una nueva contraseña vacía es rechazada al abrir el enlace

| Campo | Valor |
|---|---|
| **Título** | Verificar que una nueva contraseña vacía es rechazada al abrir el enlace |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Enlace de restablecimiento vigente recibido en el email del usuario qa.usuario01@empresa.com. |
| **Datos de prueba** | `enlace`: (enlace recibido en el email del usuario) · `password_nueva`: '' (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el enlace de restablecimiento recibido en el email | Se muestra el formulario para definir una nueva contraseña |
| 2 | Dejar vacío el campo de nueva contraseña (valor vacío) | El campo no tiene contenido |
| 3 | Confirmar el formulario | [SUPUESTO: se muestra un mensaje de error indicando que la contraseña es obligatoria y la contraseña actual no se modifica] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define el rechazo de contraseña vacía ni la política de contraseña (credential.policy).] `[SUPUESTO: «Contraseña vacía» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.password_nueva.vacia)]` _Técnica: error-choice._ |

### CP-012 — Verificar que una nueva contraseña igual a la actual es rechazada al abrir el enlace

| Campo | Valor |
|---|---|
| **Título** | Verificar que una nueva contraseña igual a la actual es rechazada al abrir el enlace |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Enlace de restablecimiento vigente recibido en el email del usuario qa.usuario01@empresa.com. Se conoce la contraseña actual del usuario. |
| **Datos de prueba** | `enlace`: (enlace recibido en el email del usuario) · `password_nueva`: (la contraseña actual del usuario) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el enlace de restablecimiento recibido en el email | Se muestra el formulario para definir una nueva contraseña |
| 2 | Ingresar la contraseña actual del usuario en el campo de nueva contraseña | El campo acepta el valor ingresado |
| 3 | Confirmar el formulario | [SUPUESTO: se muestra un mensaje de error indicando que la nueva contraseña no puede ser igual a la actual y la contraseña no se modifica] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define si la nueva contraseña puede coincidir con la actual.] `[SUPUESTO: «Contraseña igual a la actual» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.password_nueva.igual_a_la_actual)]` _Técnica: error-choice._ |

### CP-013 — Verificar que un enlace con el token alterado es rechazado y no permite cambiar la contraseña

| Campo | Valor |
|---|---|
| **Título** | Verificar que un enlace con el token alterado es rechazado y no permite cambiar la contraseña |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Enlace de restablecimiento recibido en el email del usuario qa.usuario01@empresa.com. |
| **Datos de prueba** | `password_nueva`: NuevaClave#2026 · `enlace`: (enlace recibido con el token alterado) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Modificar manualmente un carácter del token en la URL del enlace recibido | La URL contiene el token alterado |
| 2 | Abrir la URL con el token alterado | [SUPUESTO: se muestra un mensaje de enlace inválido y no se muestra el formulario de nueva contraseña] |
| 3 | Intentar iniciar sesión con la contraseña actual del usuario | [SUPUESTO: el inicio de sesión es exitoso, la contraseña no fue modificada] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de enlace inválido. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define el comportamiento ante un enlace alterado. El dato de nueva contraseña NuevaClave#2026 no debe llegar a aplicarse.] `[SUPUESTO: «Enlace con el token modificado manualmente» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.enlace.alterado)]` _Técnica: error-choice._ |

### CP-014 — Verificar que un enlace vencido es rechazado y ofrece pedir uno nuevo

| Campo | Valor |
|---|---|
| **Título** | Verificar que un enlace vencido es rechazado y ofrece pedir uno nuevo |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | Enlace de restablecimiento del usuario qa.usuario01@empresa.com generado hace más de 24 horas (o con reloj del entorno adelantado). |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el enlace de restablecimiento vencido | [SUPUESTO: se muestra el mensaje "enlace expirado" con opción de pedir uno nuevo] |
| 2 | Verificar que no se muestra el formulario de nueva contraseña | No hay campo para definir una nueva contraseña |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de enlace expirado. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: validez de 24 horas (token.expiration); la HU no define la expiración.] `[SUPUESTO: 24 horas; al usarlo vencido se muestra 'enlace expirado' con opción de pedir uno nuevo. (ver token.expiration)]` _Técnica: rule:token.expiration._ |

### CP-015 — Verificar que un enlace ya usado y un enlace anterior al último solicitado son rechazados

| Campo | Valor |
|---|---|
| **Título** | Verificar que un enlace ya usado y un enlace anterior al último solicitado son rechazados |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario registrado con email qa.usuario01@empresa.com. Dos enlaces (A y B) generados con solicitudes sucesivas; B es el más reciente. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir el enlace A (anterior) | [SUPUESTO: se rechaza el enlace A por haber sido invalidado por el enlace B] |
| 2 | Abrir el enlace B (último) | Se muestra el formulario para definir una nueva contraseña |
| 3 | Ingresar NuevaClave#2026 en el campo de nueva contraseña | El campo acepta el valor ingresado |
| 4 | Confirmar el formulario | Se muestra un mensaje que confirma que la contraseña se actualizó |
| 5 | Abrir nuevamente el enlace B ya usado | [SUPUESTO: se rechaza el enlace B por ser de un solo uso] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas de cada resultado. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: el último enlace invalida los anteriores y cada enlace es de un solo uso (token.invalidation).] `[SUPUESTO: El último enlace invalida los anteriores y cada enlace es de un solo uso. (ver token.invalidation)]` _Técnica: rule:token.invalidation._ |

### CP-016 — Verificar que tras cambiar la contraseña se invalidan las sesiones abiertas en otros dispositivos

| Campo | Valor |
|---|---|
| **Título** | Verificar que tras cambiar la contraseña se invalidan las sesiones abiertas en otros dispositivos |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Excepción |
| **Prioridad** | Alta |
| **Precondiciones** | Usuario qa.usuario01@empresa.com con sesión activa en un segundo dispositivo o navegador. Enlace de restablecimiento vigente. |
| **Datos de prueba** | — |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En el dispositivo 2, iniciar sesión con qa.usuario01@empresa.com y mantener la sesión abierta | El usuario accede a su cuenta |
| 2 | En el dispositivo 1, abrir el enlace de restablecimiento | Se muestra el formulario para definir una nueva contraseña |
| 3 | Ingresar NuevaClave#2026 en el campo de nueva contraseña | El campo acepta el valor ingresado |
| 4 | Confirmar el formulario | Se muestra un mensaje que confirma que la contraseña se actualizó |
| 5 | En el dispositivo 2, recargar la página o realizar una acción autenticada | [SUPUESTO: la sesión está invalidada y se redirige a la pantalla de login] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Capturas del dispositivo 2 antes y después del cambio. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: se invalidan todas las sesiones activas excepto la actual (credential.sessions).] `[SUPUESTO: Sí, se invalidan todas las sesiones activas excepto la actual. (ver credential.sessions)]` _Técnica: rule:credential.sessions._ |

### CP-017 — Verificar que el usuario puede iniciar sesión con la nueva contraseña definida en el restablecimiento

| Campo | Valor |
|---|---|
| **Título** | Verificar que el usuario puede iniciar sesión con la nueva contraseña definida en el restablecimiento |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-4 |
| **Tipo** | Funcional · Humo |
| **Prioridad** | Alta |
| **Precondiciones** | Contraseña de qa.usuario01@empresa.com restablecida a NuevaClave#2026 (ver CP-010 ejecutado con éxito). Sin sesión activa. |
| **Datos de prueba** | `login_posterior`: (la misma definida en password_nueva) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la pantalla de login | Se muestra el formulario de login |
| 2 | Ingresar qa.usuario01@empresa.com en el campo email | El campo muestra qa.usuario01@empresa.com |
| 3 | Ingresar NuevaClave#2026 en el campo contraseña | El campo muestra el valor enmascarado |
| 4 | Confirmar el inicio de sesión | El usuario inicia sesión y accede a su cuenta con sus datos intactos |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de la pantalla posterior al login. |
| **Estado** | Pendiente |
| **Notas** | Depende de CP-010. _Técnica: ac-happy-path._ |

### CP-018 — Verificar que tras el restablecimiento no se puede iniciar sesión con la contraseña anterior

| Campo | Valor |
|---|---|
| **Título** | Verificar que tras el restablecimiento no se puede iniciar sesión con la contraseña anterior |
| **Módulo** | Autenticación |
| **Origen** | HU-101 · CA-4 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | Contraseña de qa.usuario01@empresa.com restablecida a NuevaClave#2026 (ver CP-010 ejecutado con éxito). Se conoce la contraseña anterior. Sin sesión activa. |
| **Datos de prueba** | `login_posterior`: (la contraseña actual anterior al restablecimiento) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la pantalla de login | Se muestra el formulario de login |
| 2 | Ingresar qa.usuario01@empresa.com en el campo email | El campo muestra qa.usuario01@empresa.com |
| 3 | Ingresar la contraseña anterior al restablecimiento en el campo contraseña | El campo muestra el valor enmascarado |
| 4 | Confirmar el inicio de sesión | [SUPUESTO: se rechaza el acceso con un mensaje de credenciales inválidas y el usuario permanece en la pantalla de login] |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura del mensaje de error. |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define el rechazo de la contraseña anterior.] Depende de CP-010. `[SUPUESTO: «Login con la contraseña anterior» se considera inválido aunque la HU no lo dice]` `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.login_posterior.con_anterior)]` _Técnica: error-choice._ |

## 4. Priorización por riesgo

| Caso | Probabilidad | Impacto | Prioridad | Justificación |
|---|---|---|---|---|
| CP-001 | Baja | Alto | Alta | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media; humo → Alta |
| CP-002 | Baja | Alto | Media | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media |
| CP-003 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-004 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-005 | Media | Alto | Alta | Prob. Media (tipo Negativo) × Impacto Alto (regla de F. Seguridad) → Alta |
| CP-006 | Media | Alto | Alta | Prob. Media (tipo Negativo) × Impacto Alto (regla de E. Estados) → Alta |
| CP-007 | Media | Alto | Alta | Prob. Media (tipo No funcional) × Impacto Alto (regla de F. Seguridad) → Alta |
| CP-008 | Media | Medio | Media | Prob. Media (tipo No funcional) × Impacto Medio (tipo No funcional en funcionalidad crítica) → Media |
| CP-009 | Alta | Medio | Alta | Prob. Alta (tipo Excepción; depende de un servicio externo («servicio externo»)) × Impacto Medio (tipo Excepción en funcionalidad crítica) → Alta |
| CP-010 | Baja | Alto | Alta | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media; humo → Alta |
| CP-011 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-012 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-013 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |
| CP-014 | Media | Alto | Alta | Prob. Media (tipo Excepción) × Impacto Alto (regla de E. Estados) → Alta |
| CP-015 | Media | Alto | Alta | Prob. Media (tipo Excepción) × Impacto Alto (regla de E. Estados) → Alta |
| CP-016 | Media | Alto | Alta | Prob. Media (tipo Excepción) × Impacto Alto (regla de G. Concurrencia) → Alta |
| CP-017 | Baja | Alto | Alta | Prob. Baja (tipo Funcional) × Impacto Alto (tipo Funcional en funcionalidad crítica) → Media; humo → Alta |
| CP-018 | Media | Medio | Media | Prob. Media (tipo Negativo) × Impacto Medio (tipo Negativo en funcionalidad crítica) → Media |

**Orden de ejecución sugerido:** CP-001 → CP-010 → CP-017 → CP-005 → CP-006 → CP-007 → CP-009 → CP-014 → CP-015 → CP-016 → CP-002 → CP-003 → CP-004 → CP-008 → CP-011 → CP-012 → CP-013 → CP-018

**Subset de humo:** CP-001, CP-010, CP-017

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | El usuario accede a "Olvidé mi contraseña" desde la pantalla de login, ingresa su email y el sistema muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña". | CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008 | ✓ Cubierta |
| CA-2 | El sistema envía al email un enlace de restablecimiento. | CP-001, CP-002, CP-003, CP-004, CP-009 | ✓ Cubierta |
| CA-3 | Al abrir el enlace, el usuario define una nueva contraseña y el sistema confirma que se actualizó. | CP-010, CP-011, CP-012, CP-013, CP-014, CP-015, CP-016 | ✓ Cubierta |
| CA-4 | Con la nueva contraseña, el usuario puede iniciar sesión. | CP-017, CP-018 | ✓ Cubierta |

**Cobertura de CAs: 4/4 (100.0%).**
Cobertura 2-wise de particiones válidas: 1/1 pares (100.0%).
Cobertura de valores límite: 0/0 (100.0%) — ningún parámetro tiene límites definidos aún (ver preguntas sobre límites).

## 6. Supuestos asumidos

1. `[SUPUESTO: «Texto sin formato de email» se considera inválido aunque la HU no lo dice]` — en CP-003.
2. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.email_ingresado.formato_invalido)]` — en CP-003.
3. `[SUPUESTO: «Campo email vacío» se considera inválido aunque la HU no lo dice]` — en CP-004.
4. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.email_ingresado.vacio)]` — en CP-004.
5. `[SUPUESTO: Se muestra el mismo mensaje genérico pero no se ejecuta la acción; la cuenta sigue bloqueada. (ver P-6)]` — en CP-006.
6. `[SUPUESTO: Máximo 3 solicitudes por hora por usuario; a partir de la 3ª se pide captcha. (ver P-4)]` — en CP-007.
7. `[SUPUESTO: Solo español; Chrome, Firefox y Safari desktop + Chrome móvil. (ver P-8)]` — en CP-008.
8. `[SUPUESTO: Mensaje de error genérico con opción de reintentar; no se pierde lo ingresado. (ver P-7)]` — en CP-009.
9. `[SUPUESTO: «Contraseña vacía» se considera inválido aunque la HU no lo dice]` — en CP-011.
10. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.password_nueva.vacia)]` — en CP-011.
11. `[SUPUESTO: «Contraseña igual a la actual» se considera inválido aunque la HU no lo dice]` — en CP-012.
12. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.password_nueva.igual_a_la_actual)]` — en CP-012.
13. `[SUPUESTO: «Enlace con el token modificado manualmente» se considera inválido aunque la HU no lo dice]` — en CP-013.
14. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.enlace.alterado)]` — en CP-013.
15. `[SUPUESTO: 24 horas; al usarlo vencido se muestra 'enlace expirado' con opción de pedir uno nuevo. (ver P-2)]` — en CP-014.
16. `[SUPUESTO: El último enlace invalida los anteriores y cada enlace es de un solo uso. (ver P-3)]` — en CP-015.
17. `[SUPUESTO: Sí, se invalidan todas las sesiones activas excepto la actual. (ver P-5)]` — en CP-016.
18. `[SUPUESTO: «Login con la contraseña anterior» se considera inválido aunque la HU no lo dice]` — en CP-018.
19. `[SUPUESTO: Se rechaza con un mensaje que explica el error y no cambia el estado (ver choice.expected.login_posterior.con_anterior)]` — en CP-018.
20. `[SUPUESTO: Navegable por teclado con foco visible.]` — laguna menor `context.a11y` no preguntada (tope de preguntas).

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
| O2 — ≥1 negativo/borde cada 2 positivos | No | ✓ 8 negativos/bordes vs 4 funcionales (ratio 2.00) |
| O3 — Subset de humo marcado | No | ✓ CP-001, CP-010, CP-017 |
| O4 — Sin casos duplicados (mismo título) | No | ✓ |
| O5 — Dependencias entre casos apuntan a casos existentes (referenciar por frame_id F-…) | No | ✓ |

**Gate: APROBADO.**

## 8. Trazabilidad técnica

**Técnicas de diseño por caso:** ac-happy-path: 3 · each-choice: 1 · error-choice: 6 · rule: 8.

- `ac-happy-path` / `each-choice` / `pairwise`: Category-Partition (Ostrand & Balcer 1988) + cobertura 2-wise (Kuhn et al. 2004).
- `error-choice`: elecciones `[error]` de TSL, un caso cada una sin combinar.
- `bva`: análisis de valores límite (mín-1, mín, mín+1, máx-1, máx, máx+1).
- `rule:<id>`: heurística de `rules/gaps.yaml`.
