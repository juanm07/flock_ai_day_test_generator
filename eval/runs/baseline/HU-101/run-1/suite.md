# Suite de pruebas — HU-101: Recuperación de contraseña

Fecha: 2026-10-09 · Modo: completo (sin gaps bloqueantes)

## 1. Resumen del análisis

- **Rol**: usuario registrado que olvidó su contraseña.
- **Funcionalidad**: restablecer la contraseña mediante un enlace enviado a su email, iniciado desde "Olvidé mi contraseña" en el login.
- **Objetivo de negocio**: volver a acceder a la cuenta sin perder los datos.
- **Criterios de aceptación** (textuales):
  - **CA-1**: El usuario accede a "Olvidé mi contraseña" desde la pantalla de login, ingresa su email y el sistema muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña".
  - **CA-2**: El sistema envía al email un enlace de restablecimiento.
  - **CA-3**: Al abrir el enlace, el usuario define una nueva contraseña y el sistema confirma que se actualizó.
  - **CA-4**: Con la nueva contraseña, el usuario puede iniciar sesión.
- **Entidades y datos**: usuario (email, contraseña, perfil), solicitud/token de restablecimiento (enlace), email, servicio de notificaciones existente (nota del equipo), sesión de login.

**Gaps detectados (F2)** — ninguno BLOQUEANTE, el happy path es diseñable:

| Gap | Clase | Pregunta |
|---|---|---|
| Vigencia del enlace no definida | IMPORTANTE | P-1 |
| Un solo uso / efecto de pedir varios enlaces no definido | IMPORTANTE | P-2 |
| Política de contraseña (longitud, composición, confirmación) no definida | IMPORTANTE | P-3 |
| Falla del servicio de notificaciones no definida | IMPORTANTE | P-4 |
| Límite de solicitudes (abuso / spam de emails) no definido | IMPORTANTE | P-5 |
| Sesiones abiertas tras el cambio de contraseña no definidas | IMPORTANTE | P-6 |
| Validación/normalización del email de entrada no definida | IMPORTANTE | P-7 |
| Textos de confirmación/error, destino post-reset, cuentas desactivadas | MENOR | P-8 |
| CA-2 no aclara que el email se envía solo si el email existe (CA-1 sugiere anti-enumeración) | MENOR | Supuesto (ver sección 6) |
| El objetivo "sin perder mis datos" no tiene CA propio | MENOR | Se verifica en CP-005 |

## 2. Preguntas para el PO

Todas con default propuesto; no hay preguntas bloqueantes (ordenadas por prioridad).

**P-1. [F. Seguridad / A. Criterios] ¿El enlace de restablecimiento expira a los 60 minutos o a las 24 horas?**
- **Por qué importa**: define los casos borde de vigencia (CP-021, CP-022) y el riesgo de enlaces viejos reutilizables.
- **Default propuesto**: expira a los 60 minutos de generado.

**P-2. [G. Concurrencia / F. Seguridad] ¿El enlace es de un solo uso, y una nueva solicitud invalida el enlace anterior?**
- **Por qué importa**: define el resultado esperado de reutilizar un enlace (CP-023), de pedir dos enlaces (CP-017) y de doble submit (CP-016).
- **Default propuesto**: sí a ambas: un enlace sirve una sola vez, y solo el último enlace emitido es válido.

**P-3. [B. Datos y validaciones] ¿Cuál es la política de la nueva contraseña, existe campo "Confirmar contraseña", y se permite repetir la contraseña actual?**
- **Por qué importa**: sin límites no se pueden diseñar bordes ni negativos de la nueva contraseña (CP-025 a CP-031, CP-038).
- **Default propuesto**: mínimo 8, máximo 64 caracteres, al menos 1 letra y 1 número; hay campo de confirmación que debe coincidir; se permite repetir la contraseña actual.

**P-4. [C. Errores / I. Dependencias] Si el servicio de notificaciones falla al enviar el email, ¿qué ve el usuario?**
- **Por qué importa**: sin definición no hay resultado esperado para CP-019; mostrar un error distinto al genérico filtraría información.
- **Default propuesto**: el usuario ve el mismo mensaje genérico de CA-1; la falla se registra en logs y no se muestra error técnico.

**P-5. [F. Seguridad] ¿Hay límite de solicitudes de recuperación por email? (¿5 por hora por email, o sin límite?)**
- **Por qué importa**: sin límite el flujo permite spam de emails a un usuario y abuso del servicio de notificaciones (CP-018).
- **Default propuesto**: 5 solicitudes por hora por email; a partir de la sexta no se envía email y se muestra el mismo mensaje genérico.

**P-6. [F. Seguridad / G. Sesiones] Al cambiar la contraseña, ¿se cierran las sesiones abiertas de la cuenta (otros dispositivos)?**
- **Por qué importa**: si no se cierran, quien tenía acceso no autorizado conserva la sesión tras el reset (CP-033).
- **Default propuesto**: sí, se invalidan todas las sesiones activas de la cuenta.

**P-7. [B. Datos y validaciones] ¿Cómo se valida el email de entrada? (¿vacío y sin formato válido muestran el error "Ingresá un email válido" sin enviar nada? ¿se ignoran espacios en los extremos y mayúsculas/minúsculas? ¿máximo 254 caracteres?)**
- **Por qué importa**: define negativos y bordes de la única entrada de CA-1 (CP-008 a CP-015).
- **Default propuesto**: vacío/formato inválido/>254 caracteres muestran "Ingresá un email válido" inline y no envían la solicitud; se aplica trim y comparación sin distinguir mayúsculas.

**P-8. [J. Experiencia / E. Estados] ¿Cuáles son los textos exactos de confirmación de cambio, de enlace inválido/expirado y de error de política de contraseña; a dónde redirige tras el éxito; y qué pasa con cuentas desactivadas?**
- **Por qué importa**: CA-3 dice "confirma que se actualizó" sin texto; sin textos los resultados esperados no son assertables literalmente.
- **Default propuesto**: confirmación "Tu contraseña fue actualizada" con enlace al login; enlace inválido/expirado "El enlace no es válido o expiró" con opción de solicitar uno nuevo; error de política "La contraseña no cumple los requisitos"; cuenta desactivada = mismo mensaje genérico y sin email.

## 3. Casos de prueba

**Datos y precondiciones comunes (PC-QA)**, referenciadas en los casos:
- Ambiente QA con el servicio de notificaciones operativo y bandeja de entrada de prueba accesible para cada casilla `qa.usuarioNN@flockit-test.com`.
- Usuarios activos precreados `qa.usuario01@flockit-test.com` a `qa.usuario27@flockit-test.com`, todos con contraseña `ClaveVieja#2024` y nombre de perfil `QA Usuario NN` (NN = número de usuario). Cada caso que cambia la contraseña usa un usuario distinto para ser independiente, salvo dependencia declarada.
- Mensaje genérico de CA-1 (M1): "Si el email existe, recibirás un enlace para restablecer tu contraseña".
- `<ENLACE>` = URL contenida en el email de recuperación recibido.

---

### CP-001 — Acceso al formulario de recuperación desde el login

| Campo | Valor |
|---|---|
| **Título** | Verificar que desde el login se accede al formulario de recuperación mediante "Olvidé mi contraseña" |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Funcional |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Sin sesión iniciada |
| **Datos de prueba** | Ninguno |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la pantalla de login | Se muestra el login con el enlace "Olvidé mi contraseña" visible |
| 2 | Tocar "Olvidé mi contraseña" | Se muestra el formulario de recuperación con un campo de email y un botón para confirmar |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del login (paso 1) y del formulario (paso 2) |
| **Estado** | Pendiente |
| **Notas** | Label del botón de confirmación no definido en la HU: se valida su presencia, no su texto. |

---

### CP-002 — Mensaje de CA-1 al pedir recuperación con email registrado

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email registrado recibe en pantalla el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. CP-001 ejecutado con éxito (formulario de recuperación abierto) |
| **Datos de prueba** | qa.usuario01@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar qa.usuario01@flockit-test.com en el campo de email | El campo muestra qa.usuario01@flockit-test.com |
| 2 | Confirmar el formulario | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje (paso 2) |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. Alimenta CP-003. |

---

### CP-003 — Recepción del email con el enlace de restablecimiento

| Campo | Valor |
|---|---|
| **Título** | Verificar que el sistema envía al email registrado un mensaje con un enlace de restablecimiento |
| **Módulo** | Recuperación de contraseña / Servicio de notificaciones |
| **Origen** | HU-101 · CA-2 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. CP-002 ejecutado con éxito para qa.usuario01@flockit-test.com |
| **Datos de prueba** | qa.usuario01@flockit-test.com; contraseña actual ClaveVieja#2024 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la bandeja de qa.usuario01@flockit-test.com | Hay exactamente 1 email nuevo de recuperación de contraseña, recibido dentro de los 5 minutos posteriores al CP-002 |
| 2 | Abrir el email | El cuerpo contiene un enlace (hipervínculo) de restablecimiento |
| 3 | Inspeccionar la URL del enlace | La URL comienza con "https://" |
| 4 | Buscar "ClaveVieja#2024" en el cuerpo del email | El texto no aparece |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la bandeja y del email; email en formato fuente (.eml) |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. [SUPUESTO: el email llega en ≤ 5 min — la HU no define SLA de entrega.] [SUPUESTO: el enlace usa HTTPS — la HU no lo define; es estándar para flujos de auth.] Asunto, remitente y texto del email no están definidos en la HU: no se validan. |

---

### CP-004 — Definir nueva contraseña con el enlace y recibir confirmación

| Campo | Valor |
|---|---|
| **Título** | Verificar que al abrir el enlace el usuario define una nueva contraseña y el sistema confirma que se actualizó |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. CP-003 ejecutado con éxito (email de qa.usuario01@flockit-test.com recibido, enlace vigente y sin usar) |
| **Datos de prueba** | `<ENLACE>` del CP-003; nueva contraseña NuevaClave#2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir `<ENLACE>` en el navegador | Se muestra el formulario para definir la nueva contraseña |
| 2 | Ingresar NuevaClave#2026 en "Nueva contraseña" | El campo muestra el valor enmascarado |
| 3 | Ingresar NuevaClave#2026 en "Confirmar contraseña" | El campo muestra el valor enmascarado |
| 4 | Confirmar el formulario | Se muestra un mensaje de confirmación de contraseña actualizada |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de pasos 1 y 4; request/response del cambio |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. [SUPUESTO: existe campo "Confirmar contraseña" — ver P-3.] [SUPUESTO: texto de confirmación "Tu contraseña fue actualizada" — la HU no define el texto, ver P-8; se valida que exista un mensaje de confirmación.] |

---

### CP-005 — Inicio de sesión con la nueva contraseña y datos conservados

| Campo | Valor |
|---|---|
| **Título** | Verificar que con la nueva contraseña el usuario inicia sesión y conserva los datos de su cuenta |
| **Módulo** | Login |
| **Origen** | HU-101 · CA-4 |
| **Tipo** | Funcional |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. CP-004 ejecutado con éxito (contraseña de qa.usuario01@flockit-test.com = NuevaClave#2026). Sin sesión iniciada |
| **Datos de prueba** | qa.usuario01@flockit-test.com / NuevaClave#2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la pantalla de login | Se muestra el formulario de login |
| 2 | Ingresar qa.usuario01@flockit-test.com en el campo de email | El campo muestra el email |
| 3 | Ingresar NuevaClave#2026 en el campo de contraseña | El campo muestra el valor enmascarado |
| 4 | Tocar "Iniciar sesión" | El usuario queda autenticado y se muestra la pantalla posterior al login |
| 5 | Abrir el perfil de la cuenta | Se muestra el nombre "QA Usuario 01", el mismo que antes del restablecimiento |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot de la pantalla post-login y del perfil |
| **Estado** | Pendiente |
| **Notas** | Subset de humo. Cubre el objetivo "sin perder mis datos". [SUPUESTO: el perfil muestra el nombre de la cuenta; la HU no define qué datos tiene la cuenta.] |

---

### CP-006 — La contraseña anterior deja de funcionar tras el restablecimiento

| Campo | Valor |
|---|---|
| **Título** | Verificar que la contraseña anterior es rechazada después de restablecerla |
| **Módulo** | Login |
| **Origen** | HU-101 · CA-3, CA-4 |
| **Tipo** | Negativo |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. CP-004 ejecutado con éxito para qa.usuario01@flockit-test.com. Sin sesión iniciada |
| **Datos de prueba** | qa.usuario01@flockit-test.com / ClaveVieja#2024 (contraseña anterior) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la pantalla de login | Se muestra el formulario de login |
| 2 | Ingresar qa.usuario01@flockit-test.com en el campo de email | El campo muestra el email |
| 3 | Ingresar ClaveVieja#2024 en el campo de contraseña | El campo muestra el valor enmascarado |
| 4 | Tocar "Iniciar sesión" | El login se rechaza con el mensaje de credenciales inválidas existente del login y no se inicia sesión |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del rechazo; response del login (código de error) |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la contraseña anterior deja de ser válida — la HU solo dice que la nueva permite el acceso.] El texto del error es el del login actual, no definido en esta HU. |

---

### CP-007 — Email no registrado recibe el mismo mensaje y no recibe email

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email no registrado recibe el mismo mensaje genérico que uno registrado y no se le envía email |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Negativo (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. inexistente@flockit-test.com NO existe en el sistema. Formulario de recuperación abierto |
| **Datos de prueba** | inexistente@flockit-test.com (no registrado); qa.usuario02@flockit-test.com (registrado, para comparar tiempos) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar inexistente@flockit-test.com y confirmar, midiendo el tiempo de respuesta | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 2 | Revisar la bandeja de inexistente@flockit-test.com 5 minutos después | No llegó ningún email |
| 3 | Repetir el paso 1 con qa.usuario02@flockit-test.com, midiendo el tiempo de respuesta | Se muestra el mismo texto exacto, con diseño idéntico al del paso 1 |
| 4 | Comparar los tiempos de respuesta de los pasos 1 y 3 | La diferencia es menor a 500 ms |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de pasos 1 y 3; bandeja vacía; tiempos de red (DevTools) |
| **Estado** | Pendiente |
| **Notas** | Anti-enumeración de usuarios. [SUPUESTO: umbral de diferencia de tiempo 500 ms; la HU no lo define.] [SUPUESTO: no se envía email a direcciones no registradas — CA-2 no lo aclara, ver sección 6.] |

---

### CP-008 — Email vacío

| Campo | Valor |
|---|---|
| **Título** | Verificar que enviar el formulario con el email vacío muestra un error de validación y no genera solicitud |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto |
| **Datos de prueba** | Email: (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Dejar el campo de email vacío | El campo está vacío |
| 2 | Confirmar el formulario | Se muestra el error inline "Ingresá un email válido" |
| 3 | Revisar la pestaña Network de DevTools | No se envió ninguna solicitud de recuperación al backend |
| 4 | Verificar el contenido de la pantalla | El mensaje "Si el email existe, recibirás un enlace..." NO se muestra |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del error; captura de Network |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: validación de obligatoriedad con texto "Ingresá un email válido" y sin solicitud al backend — la HU no la define, ver P-7.] |

---

### CP-009 — Email con formato inválido

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email sin formato válido es rechazado con error de validación |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto |
| **Datos de prueba** | Variante A: qa.usuario01flockit-test.com (sin @). Variante B: qa.usuario01@ (sin dominio) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar qa.usuario01flockit-test.com y confirmar | Se muestra el error inline "Ingresá un email válido"; no se envía solicitud al backend |
| 2 | Borrar el campo, ingresar qa.usuario01@ y confirmar | Se muestra el error inline "Ingresá un email válido"; no se envía solicitud al backend |
| 3 | Revisar la bandeja de qa.usuario01@flockit-test.com | No llegó ningún email |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de los errores; captura de Network; bandeja |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: texto y comportamiento del error de formato, ver P-7.] |

---

### CP-010 — Email con solo espacios

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email compuesto solo por espacios se trata como vacío |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto |
| **Datos de prueba** | Email: 5 espacios ("     ") |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar 5 espacios en el campo de email | El campo contiene 5 espacios |
| 2 | Confirmar el formulario | Se muestra el error inline "Ingresá un email válido"; no se envía solicitud al backend |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot; captura de Network |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: se trata igual que vacío, ver P-7.] |

---

### CP-011 — Email con espacios al inicio y al final

| Campo | Valor |
|---|---|
| **Título** | Verificar que los espacios alrededor de un email registrado se ignoran y se envía el enlace |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto |
| **Datos de prueba** | "  qa.usuario03@flockit-test.com  " (2 espacios antes y 2 después; típico de copiar-pegar) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Pegar "  qa.usuario03@flockit-test.com  " en el campo de email | El campo contiene el texto con los espacios |
| 2 | Confirmar el formulario | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 3 | Revisar la bandeja de qa.usuario03@flockit-test.com | Hay 1 email nuevo de recuperación con enlace |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del paso 2; bandeja |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: se aplica trim al email, ver P-7.] |

---

### CP-012 — Email registrado ingresado en mayúsculas

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email registrado ingresado con mayúsculas recibe el enlace |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1, CA-2 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto. El usuario está registrado como qa.usuario04@flockit-test.com |
| **Datos de prueba** | QA.Usuario04@FLOCKIT-TEST.COM |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar QA.Usuario04@FLOCKIT-TEST.COM en el campo de email | El campo muestra el email en mayúsculas |
| 2 | Confirmar el formulario | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 3 | Revisar la bandeja de qa.usuario04@flockit-test.com | Hay 1 email nuevo de recuperación con enlace |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del paso 2; bandeja |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la comparación de email no distingue mayúsculas, ver P-7.] |

---

### CP-013 — Email en el límite de longitud máxima (254 y 255 caracteres)

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email de 254 caracteres se procesa y uno de 255 es rechazado |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto |
| **Datos de prueba** | Email A (254 caracteres): 64 veces "a" + "@" + dominio de 189 caracteres formado por una etiqueta de 63 "b", ".", una de 63 "c", ".", una de 57 "d", "." y "com". Email B (255 caracteres): igual que A pero con la etiqueta de "d" de 58 caracteres |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar el Email A y confirmar | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña"; sin error técnico |
| 2 | Ingresar el Email B y confirmar | Se muestra el error inline "Ingresá un email válido"; no se envía solicitud al backend |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de ambos pasos; longitud verificada de los strings usados |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: máximo 254 caracteres (límite estándar de email), ver P-7.] |

---

### CP-014 — Email con caracteres unicode (ñ, acentos) no registrado

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email con ñ y acentos se procesa sin error técnico |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto. ñandú.qa@flockit-test.com no existe en el sistema |
| **Datos de prueba** | ñandú.qa@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar ñandú.qa@flockit-test.com y confirmar | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" o el error "Ingresá un email válido"; en ningún caso un error 500 ni un stack trace |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot; response del backend |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la HU no define si los emails internacionalizados son válidos; se acepta cualquiera de los dos resultados siempre que no haya error técnico. Resultado a confirmar con P-7.] |

---

### CP-015 — Inyección básica en el campo de email

| Campo | Valor |
|---|---|
| **Título** | Verificar que entradas con SQL y script en el email no producen error técnico ni ejecución |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto |
| **Datos de prueba** | Variante A: `' OR 1=1 --`. Variante B: `<script>alert(1)</script>@flockit-test.com` |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar `' OR 1=1 --` y confirmar | Se muestra "Ingresá un email válido" o el mensaje genérico de CA-1; no hay error 500 ni stack trace ni detalle de consulta |
| 2 | Ingresar `<script>alert(1)</script>@flockit-test.com` y confirmar | Se muestra "Ingresá un email válido" o el mensaje genérico de CA-1; no se abre ningún diálogo alert |
| 3 | Revisar las bandejas de qa.usuario01@flockit-test.com a qa.usuario27@flockit-test.com | No llegó ningún email de recuperación nuevo por estas pruebas |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots; response del backend; logs de la aplicación |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: cualquiera de los dos mensajes es aceptable; la HU no define la validación, ver P-7.] |

---

### CP-016 — Doble envío del formulario de recuperación

| Campo | Valor |
|---|---|
| **Título** | Verificar que un doble clic en el botón de confirmar genera un solo email |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1, CA-2 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto. Bandeja de qa.usuario05@flockit-test.com vacía de emails de recuperación |
| **Datos de prueba** | qa.usuario05@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar qa.usuario05@flockit-test.com en el campo de email | El campo muestra el email |
| 2 | Hacer doble clic rápido (< 300 ms entre clics) en el botón de confirmar | Se muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña" una sola vez |
| 3 | Revisar la bandeja de qa.usuario05@flockit-test.com 5 minutos después | Hay exactamente 1 email de recuperación |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Captura de Network (cantidad de requests); bandeja |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: un doble submit no debe duplicar emails; la HU no lo define, ver P-2 y P-5.] |

---

### CP-017 — Dos solicitudes sucesivas: solo el último enlace es válido

| Campo | Valor |
|---|---|
| **Título** | Verificar que al pedir dos enlaces seguidos el primero queda inválido y el segundo funciona |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-2, CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Bandeja de qa.usuario06@flockit-test.com sin emails de recuperación |
| **Datos de prueba** | qa.usuario06@flockit-test.com; nueva contraseña NuevaClave#2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación para qa.usuario06@flockit-test.com | Se muestra el mensaje genérico de CA-1 |
| 2 | Esperar 1 minuto y solicitar nuevamente la recuperación para qa.usuario06@flockit-test.com | Se muestra el mensaje genérico de CA-1 |
| 3 | Revisar la bandeja de qa.usuario06@flockit-test.com | Hay 2 emails de recuperación, cada uno con un enlace distinto (ENLACE-1 el primero, ENLACE-2 el segundo) |
| 4 | Abrir ENLACE-1 | Se rechaza con el mensaje de enlace inválido o expirado; no se muestra el formulario de nueva contraseña |
| 5 | Abrir ENLACE-2 | Se muestra el formulario para definir la nueva contraseña |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots; bandeja con los 2 emails; response de los pasos 4 y 5 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: una nueva solicitud invalida el enlace anterior, ver P-2.] |

---

### CP-018 — Límite de solicitudes de recuperación por email

| Campo | Valor |
|---|---|
| **Título** | Verificar que a partir de la sexta solicitud en una hora no se envían más emails ni se revela el bloqueo |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-2 |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Bandeja de qa.usuario07@flockit-test.com sin emails de recuperación. Sin solicitudes previas de qa.usuario07 en la última hora |
| **Datos de prueba** | qa.usuario07@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación para qa.usuario07@flockit-test.com 5 veces seguidas, dentro de 10 minutos | En cada solicitud se muestra el mensaje genérico de CA-1 |
| 2 | Solicitar la recuperación por sexta vez, dentro de la misma hora | Se muestra el mismo mensaje genérico de CA-1, sin mensaje de bloqueo ni de límite |
| 3 | Revisar la bandeja de qa.usuario07@flockit-test.com 5 minutos después | Hay exactamente 5 emails de recuperación; ninguno corresponde a la sexta solicitud |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de cada solicitud; bandeja con 5 emails; logs de rate limiting |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: límite de 5 solicitudes por hora por email, respuesta idéntica a la normal, ver P-5.] |

---

### CP-019 — Servicio de notificaciones caído al solicitar el enlace

| Campo | Valor |
|---|---|
| **Título** | Verificar que si el servicio de notificaciones falla el usuario ve el mensaje genérico y no un error técnico |
| **Módulo** | Recuperación de contraseña / Servicio de notificaciones |
| **Origen** | HU-101 · CA-2 (nota del equipo) |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. El servicio de notificaciones está detenido o simulado con respuesta HTTP 503. Formulario de recuperación abierto |
| **Datos de prueba** | qa.usuario08@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar qa.usuario08@flockit-test.com y confirmar el formulario | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña"; sin stack trace ni mensaje de error técnico |
| 2 | Revisar los logs de la aplicación | Hay una entrada de error que registra la falla de envío al servicio de notificaciones |
| 3 | Restablecer el servicio de notificaciones | El servicio responde correctamente |
| 4 | Solicitar nuevamente la recuperación para qa.usuario08@flockit-test.com | Se muestra el mensaje genérico de CA-1 |
| 5 | Revisar la bandeja de qa.usuario08@flockit-test.com | Hay 1 email de recuperación con enlace |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del paso 1; logs; bandeja |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: comportamiento ante falla del servicio de notificaciones, ver P-4.] [SUPUESTO: el paso 4 no cuenta contra el límite de P-5.] |

---

### CP-020 — Pérdida de red al enviar el formulario de recuperación

| Campo | Valor |
|---|---|
| **Título** | Verificar el comportamiento del formulario si la red cae al confirmar |
| **Módulo** | Recuperación de contraseña |
| **Origen** | Exploratorio |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Formulario de recuperación abierto con qa.usuario09@flockit-test.com ingresado |
| **Datos de prueba** | qa.usuario09@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Activar modo "Offline" en DevTools | El navegador está sin conexión |
| 2 | Confirmar el formulario | No se muestra el mensaje "Si el email existe, recibirás un enlace..."; se muestra un aviso de error de conexión o el formulario permanece sin avanzar |
| 3 | Desactivar el modo "Offline" | El navegador recupera la conexión |
| 4 | Confirmar el formulario nuevamente | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de pasos 2 y 4; captura de Network |
| **Estado** | Pendiente |
| **Notas** | Caso exploratorio: la HU no define el mensaje ante pérdida de red. [SUPUESTO: no se muestra el mensaje de éxito si la solicitud no llegó al backend.] |

---

### CP-021 — Enlace dentro de la vigencia (59 minutos)

| Campo | Valor |
|---|---|
| **Título** | Verificar que un enlace de 59 minutos de antigüedad sigue siendo válido |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Ambiente que permite avanzar el reloj del servidor (o generar el token con timestamp ajustable). Enlace emitido para qa.usuario10@flockit-test.com |
| **Datos de prueba** | qa.usuario10@flockit-test.com; `<ENLACE>` recién emitido; tiempo transcurrido: 59 minutos |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación para qa.usuario10@flockit-test.com | Se muestra el mensaje genérico de CA-1 |
| 2 | Avanzar el reloj del servidor 59 minutos | El reloj indica 59 minutos desde la emisión |
| 3 | Abrir `<ENLACE>` del email | Se muestra el formulario para definir la nueva contraseña |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del paso 3; hora del servidor |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: vigencia de 60 minutos, ver P-1.] |

---

### CP-022 — Enlace expirado (61 minutos)

| Campo | Valor |
|---|---|
| **Título** | Verificar que un enlace de 61 minutos de antigüedad es rechazado y no cambia la contraseña |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Ambiente que permite avanzar el reloj del servidor. Enlace emitido para qa.usuario11@flockit-test.com |
| **Datos de prueba** | qa.usuario11@flockit-test.com; tiempo transcurrido: 61 minutos; contraseña vigente ClaveVieja#2024 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación para qa.usuario11@flockit-test.com | Se muestra el mensaje genérico de CA-1 |
| 2 | Avanzar el reloj del servidor 61 minutos | El reloj indica 61 minutos desde la emisión |
| 3 | Abrir `<ENLACE>` del email | Se muestra el mensaje "El enlace no es válido o expiró"; no se muestra el formulario de nueva contraseña |
| 4 | Iniciar sesión con qa.usuario11@flockit-test.com / ClaveVieja#2024 | El login es exitoso: la contraseña no cambió |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de pasos 3 y 4; hora del servidor |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: vigencia de 60 minutos y texto del mensaje de enlace expirado, ver P-1 y P-8.] |

---

### CP-023 — Reutilización de un enlace ya usado

| Campo | Valor |
|---|---|
| **Título** | Verificar que un enlace ya utilizado no permite volver a cambiar la contraseña |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Enlace emitido para qa.usuario12@flockit-test.com, vigente y sin usar |
| **Datos de prueba** | qa.usuario12@flockit-test.com; `<ENLACE>`; primera contraseña NuevaClave#2026; segunda contraseña OtraClave#2027 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir `<ENLACE>` y definir NuevaClave#2026 (nueva y confirmación) | Se confirma la actualización de la contraseña |
| 2 | Abrir `<ENLACE>` nuevamente | Se muestra el mensaje "El enlace no es válido o expiró"; no se muestra el formulario de nueva contraseña |
| 3 | Iniciar sesión con qa.usuario12@flockit-test.com / NuevaClave#2026 | El login es exitoso |
| 4 | Iniciar sesión con qa.usuario12@flockit-test.com / OtraClave#2027 | El login se rechaza |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de pasos 2, 3 y 4 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: enlace de un solo uso, ver P-2.] |

---

### CP-024 — Enlace con token alterado o sin token

| Campo | Valor |
|---|---|
| **Título** | Verificar que un enlace con el token modificado o ausente es rechazado sin revelar información |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Enlace emitido para qa.usuario13@flockit-test.com, vigente y sin usar |
| **Datos de prueba** | `<ENLACE>` de qa.usuario13@flockit-test.com; variante A: `<ENLACE>` con el último carácter del token reemplazado por otro distinto; variante B: URL de la pantalla de nueva contraseña sin el parámetro de token |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir la variante A en el navegador | Se muestra "El enlace no es válido o expiró"; no se muestra el formulario de nueva contraseña |
| 2 | Abrir la variante B en el navegador | Se muestra "El enlace no es válido o expiró"; no se muestra el formulario de nueva contraseña |
| 3 | Revisar el contenido de ambas respuestas | No contienen emails, stack trace ni detalle interno |
| 4 | Abrir `<ENLACE>` original | Se muestra el formulario de nueva contraseña (el enlace original sigue vigente) |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots; responses HTTP |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: texto del mensaje, ver P-8.] |

---

### CP-025 — Nueva contraseña fuera de límites de longitud (7 y 65 caracteres)

| Campo | Valor |
|---|---|
| **Título** | Verificar que contraseñas de 7 y de 65 caracteres son rechazadas y el enlace sigue vigente |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Borde |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario14@flockit-test.com. Formulario de nueva contraseña abierto |
| **Datos de prueba** | Contraseña de 7 caracteres: Abcde1!. Contraseña de 65 caracteres: "Aa1!" repetido 16 veces + "A" |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar Abcde1! en "Nueva contraseña" y en "Confirmar contraseña", y confirmar | Se muestra el error "La contraseña no cumple los requisitos"; la contraseña no se actualiza |
| 2 | Ingresar la contraseña de 65 caracteres en ambos campos y confirmar | Se muestra el error "La contraseña no cumple los requisitos"; la contraseña no se actualiza |
| 3 | Iniciar sesión con qa.usuario14@flockit-test.com / ClaveVieja#2024 | El login es exitoso: la contraseña no cambió |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de los errores; response del backend; login del paso 3 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: mínimo 8 y máximo 64 caracteres, texto del error, ver P-3 y P-8.] |

---

### CP-026 — Nueva contraseña de longitud mínima exacta (8 caracteres)

| Campo | Valor |
|---|---|
| **Título** | Verificar que una contraseña de 8 caracteres es aceptada y permite iniciar sesión |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3, CA-4 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario15@flockit-test.com. Formulario de nueva contraseña abierto |
| **Datos de prueba** | Abcdef1! (8 caracteres) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar Abcdef1! en "Nueva contraseña" y en "Confirmar contraseña", y confirmar | Se muestra el mensaje de confirmación de contraseña actualizada |
| 2 | Iniciar sesión con qa.usuario15@flockit-test.com / Abcdef1! | El login es exitoso |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de ambos pasos |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: mínimo 8 caracteres, ver P-3.] |

---

### CP-027 — Nueva contraseña de longitud máxima exacta (64 caracteres)

| Campo | Valor |
|---|---|
| **Título** | Verificar que una contraseña de 64 caracteres es aceptada y permite iniciar sesión |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3, CA-4 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario16@flockit-test.com. Formulario de nueva contraseña abierto |
| **Datos de prueba** | "Aa1!" repetido 16 veces (64 caracteres) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar la contraseña de 64 caracteres en ambos campos y confirmar | Se muestra el mensaje de confirmación de contraseña actualizada |
| 2 | Iniciar sesión con qa.usuario16@flockit-test.com y la contraseña de 64 caracteres | El login es exitoso |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de ambos pasos |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: máximo 64 caracteres, ver P-3.] |

---

### CP-028 — Nueva contraseña vacía

| Campo | Valor |
|---|---|
| **Título** | Verificar que no se puede confirmar el cambio con los campos de contraseña vacíos |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario17@flockit-test.com. Formulario de nueva contraseña abierto |
| **Datos de prueba** | "Nueva contraseña": (vacío); "Confirmar contraseña": (vacío) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Dejar ambos campos vacíos y confirmar | Se muestra un error de campo obligatorio; la contraseña no se actualiza |
| 2 | Iniciar sesión con qa.usuario17@flockit-test.com / ClaveVieja#2024 | El login es exitoso: la contraseña no cambió |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del error; login del paso 2 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: la contraseña es obligatoria, ver P-3; el texto del error no está definido, ver P-8.] |

---

### CP-029 — Confirmación de contraseña distinta de la nueva

| Campo | Valor |
|---|---|
| **Título** | Verificar que si la confirmación no coincide con la nueva contraseña se rechaza el cambio |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario18@flockit-test.com. Formulario de nueva contraseña abierto |
| **Datos de prueba** | Nueva contraseña: NuevaClave#2026; Confirmar contraseña: NuevaClave#2027 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar NuevaClave#2026 en "Nueva contraseña" | El campo muestra el valor enmascarado |
| 2 | Ingresar NuevaClave#2027 en "Confirmar contraseña" | El campo muestra el valor enmascarado |
| 3 | Confirmar el formulario | Se muestra un error indicando que las contraseñas no coinciden; la contraseña no se actualiza |
| 4 | Iniciar sesión con qa.usuario18@flockit-test.com / ClaveVieja#2024 | El login es exitoso: la contraseña no cambió |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del error; login del paso 4 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: existe campo de confirmación y debe coincidir, ver P-3.] |

---

### CP-030 — Nueva contraseña sin letras o sin números

| Campo | Valor |
|---|---|
| **Título** | Verificar que contraseñas sin número o sin letra son rechazadas por la política |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Negativo |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario19@flockit-test.com. Formulario de nueva contraseña abierto |
| **Datos de prueba** | Variante A (sin número): abcdefgh. Variante B (sin letra): 12345678 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar abcdefgh en ambos campos y confirmar | Se muestra el error "La contraseña no cumple los requisitos"; la contraseña no se actualiza |
| 2 | Ingresar 12345678 en ambos campos y confirmar | Se muestra el error "La contraseña no cumple los requisitos"; la contraseña no se actualiza |
| 3 | Iniciar sesión con qa.usuario19@flockit-test.com / ClaveVieja#2024 | El login es exitoso: la contraseña no cambió |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots; response del backend |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: composición mínima 1 letra y 1 número, ver P-3.] Verificar además que la validación se aplica en el backend (reenviar el request sin pasar por el front). |

---

### CP-031 — Nueva contraseña con caracteres unicode (ñ, acentos)

| Campo | Valor |
|---|---|
| **Título** | Verificar que una contraseña con ñ y acentos se guarda y permite iniciar sesión |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3, CA-4 |
| **Tipo** | Borde |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario20@flockit-test.com. Formulario de nueva contraseña abierto |
| **Datos de prueba** | Ñandú#Clave2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Ingresar Ñandú#Clave2026 en ambos campos y confirmar | Se muestra el mensaje de confirmación de contraseña actualizada |
| 2 | Iniciar sesión con qa.usuario20@flockit-test.com / Ñandú#Clave2026 | El login es exitoso |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de ambos pasos |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: se aceptan caracteres unicode en la contraseña, ver P-3.] |

---

### CP-032 — Contraseña enmascarada y ausente de la URL

| Campo | Valor |
|---|---|
| **Título** | Verificar que la nueva contraseña se muestra enmascarada y no viaja en la URL |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario21@flockit-test.com |
| **Datos de prueba** | NuevaClave#2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir `<ENLACE>` e ingresar NuevaClave#2026 en "Nueva contraseña" | El campo muestra caracteres enmascarados y no el texto en claro |
| 2 | Confirmar el formulario | Se muestra el mensaje de confirmación |
| 3 | Revisar la URL de la barra de direcciones y el historial del navegador | "NuevaClave#2026" no aparece en ninguna URL |
| 4 | Revisar el request del cambio en Network | La contraseña viaja en el cuerpo del request (no en query string) y por HTTPS |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del campo; captura del request en Network |
| **Estado** | Pendiente |
| **Notas** | Dato personal sensible: aplicación de seguridad obligatoria por tratarse de autenticación. |

---

### CP-033 — Sesiones abiertas se cierran tras restablecer la contraseña

| Campo | Valor |
|---|---|
| **Título** | Verificar que una sesión abierta en otro navegador se invalida al restablecer la contraseña |
| **Módulo** | Recuperación de contraseña / Sesiones |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | No funcional (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | PC-QA. qa.usuario22@flockit-test.com con sesión iniciada en el Navegador A (ClaveVieja#2024). Enlace vigente y sin usar para qa.usuario22 |
| **Datos de prueba** | qa.usuario22@flockit-test.com; nueva contraseña NuevaClave#2026 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En el Navegador B, abrir `<ENLACE>` y definir NuevaClave#2026 (nueva y confirmación) | Se confirma la actualización de la contraseña |
| 2 | En el Navegador A, recargar la página | El usuario es redirigido al login: la sesión ya no es válida |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del Navegador A tras recargar |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: se invalidan todas las sesiones activas al cambiar la contraseña, ver P-6.] |

---

### CP-034 — Atrás y reenvío del formulario tras un cambio exitoso

| Campo | Valor |
|---|---|
| **Título** | Verificar que volver atrás y reenviar el formulario tras el éxito no permite un segundo cambio |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Excepción |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario23@flockit-test.com |
| **Datos de prueba** | qa.usuario23@flockit-test.com; primera contraseña NuevaClave#2026; segunda contraseña OtraClave#2027 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir `<ENLACE>` y definir NuevaClave#2026 (nueva y confirmación) | Se muestra el mensaje de confirmación |
| 2 | Tocar el botón "Atrás" del navegador | Se muestra la pantalla anterior o se rechaza el acceso; no hay error técnico |
| 3 | Ingresar OtraClave#2027 en ambos campos y confirmar | Se rechaza con el mensaje "El enlace no es válido o expiró" |
| 4 | Iniciar sesión con qa.usuario23@flockit-test.com / NuevaClave#2026 | El login es exitoso |
| 5 | Iniciar sesión con qa.usuario23@flockit-test.com / OtraClave#2027 | El login se rechaza |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots; responses de los pasos 2 y 3 |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: enlace de un solo uso, ver P-2.] |

---

### CP-035 — Cuenta desactivada solicita recuperación

| Campo | Valor |
|---|---|
| **Título** | Verificar el comportamiento de la recuperación para una cuenta desactivada |
| **Módulo** | Recuperación de contraseña |
| **Origen** | Exploratorio |
| **Tipo** | Negativo |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. qa.usuario24@flockit-test.com está desactivada (si el sistema soporta ese estado; si no, marcar el caso como "No aplicable") |
| **Datos de prueba** | qa.usuario24@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Solicitar la recuperación para qa.usuario24@flockit-test.com | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" |
| 2 | Revisar la bandeja de qa.usuario24@flockit-test.com 5 minutos después | No llegó ningún email |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot; bandeja |
| **Estado** | Pendiente |
| **Notas** | Caso exploratorio. [SUPUESTO: una cuenta desactivada recibe el mensaje genérico y no el email, ver P-8.] |

---

### CP-036 — Operación del formulario de recuperación solo con teclado

| Campo | Valor |
|---|---|
| **Título** | Verificar que el formulario de recuperación se completa y envía solo con teclado |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | No funcional (accesibilidad) |
| **Prioridad** | Baja |
| **Precondiciones** | PC-QA. Pantalla de login abierta, sin usar el mouse |
| **Datos de prueba** | qa.usuario25@flockit-test.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Navegar con Tab hasta "Olvidé mi contraseña" | El enlace muestra indicador de foco visible |
| 2 | Presionar Enter | Se muestra el formulario de recuperación con el foco en el campo de email o alcanzable con Tab |
| 3 | Ingresar qa.usuario25@flockit-test.com | El campo muestra el email |
| 4 | Presionar Enter | Se muestra el texto exacto "Si el email existe, recibirás un enlace para restablecer tu contraseña" |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Video corto o capturas con el foco visible |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: Enter envía el formulario, comportamiento estándar.] |

---

### CP-037 — El restablecimiento de un usuario no afecta a otro

| Campo | Valor |
|---|---|
| **Título** | Verificar que restablecer la contraseña de un usuario no modifica la contraseña de otro |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-3, CA-4 |
| **Tipo** | Regresión |
| **Prioridad** | Media |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario26@flockit-test.com. qa.usuario27@flockit-test.com sin cambios |
| **Datos de prueba** | qa.usuario26@flockit-test.com (restablece a NuevaClave#2026); qa.usuario27@flockit-test.com / ClaveVieja#2024 |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir `<ENLACE>` de qa.usuario26 y definir NuevaClave#2026 (nueva y confirmación) | Se confirma la actualización de la contraseña |
| 2 | Iniciar sesión con qa.usuario27@flockit-test.com / ClaveVieja#2024 | El login es exitoso |
| 3 | Iniciar sesión con qa.usuario27@flockit-test.com / NuevaClave#2026 | El login se rechaza |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de los pasos 2 y 3 |
| **Estado** | Pendiente |
| **Notas** | Verifica aislamiento entre cuentas y que el login normal no se rompió. |

---

### CP-038 — Nueva contraseña igual a la actual

| Campo | Valor |
|---|---|
| **Título** | Verificar que se acepta definir como nueva contraseña la misma que ya tenía |
| **Módulo** | Recuperación de contraseña |
| **Origen** | HU-101 · CA-3 |
| **Tipo** | Borde |
| **Prioridad** | Baja |
| **Precondiciones** | PC-QA. Enlace vigente y sin usar para qa.usuario26@flockit-test.com. CP-037 NO ejecutado sobre este usuario en este ciclo (usar un usuario con contraseña ClaveVieja#2024; si CP-037 ya se ejecutó, restaurar el usuario al estado inicial) |
| **Datos de prueba** | ClaveVieja#2024 (igual a la contraseña actual) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | Abrir `<ENLACE>` e ingresar ClaveVieja#2024 en ambos campos y confirmar | Se muestra el mensaje de confirmación de contraseña actualizada |
| 2 | Iniciar sesión con qa.usuario26@flockit-test.com / ClaveVieja#2024 | El login es exitoso |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshots de ambos pasos |
| **Estado** | Pendiente |
| **Notas** | [SUPUESTO: se permite reutilizar la contraseña actual, ver P-3.] |

---

## 4. Priorización por riesgo

| Caso | Probabilidad | Impacto | Prioridad | Humo |
|---|---|---|---|---|
| CP-001 | Baja | Alto | Media | |
| CP-002 | Media | Alto | Alta | Sí |
| CP-003 | Media | Alto | Alta | Sí |
| CP-004 | Media | Alto | Alta | Sí |
| CP-005 | Media | Alto | Alta | Sí |
| CP-006 | Media | Alto | Alta | |
| CP-007 | Media | Alto | Alta | |
| CP-008 | Media | Medio | Media | |
| CP-009 | Media | Medio | Media | |
| CP-010 | Media | Bajo | Baja | |
| CP-011 | Media | Bajo | Baja | |
| CP-012 | Media | Medio | Media | |
| CP-013 | Baja | Bajo | Baja | |
| CP-014 | Baja | Bajo | Baja | |
| CP-015 | Media | Alto | Alta | |
| CP-016 | Media | Medio | Media | |
| CP-017 | Alta | Alto | Alta | |
| CP-018 | Media | Alto | Alta | |
| CP-019 | Media | Medio | Media | |
| CP-020 | Media | Medio | Media | |
| CP-021 | Media | Alto | Alta | |
| CP-022 | Alta | Alto | Alta | |
| CP-023 | Media | Alto | Alta | |
| CP-024 | Media | Alto | Alta | |
| CP-025 | Alta | Medio | Alta | |
| CP-026 | Media | Medio | Media | |
| CP-027 | Baja | Bajo | Baja | |
| CP-028 | Media | Medio | Media | |
| CP-029 | Media | Medio | Media | |
| CP-030 | Alta | Medio | Alta | |
| CP-031 | Media | Medio | Media | |
| CP-032 | Baja | Alto | Media | |
| CP-033 | Media | Alto | Alta | |
| CP-034 | Media | Medio | Media | |
| CP-035 | Media | Medio | Media | |
| CP-036 | Baja | Bajo | Baja | |
| CP-037 | Baja | Alto | Media | |
| CP-038 | Baja | Bajo | Baja | |

Resumen: Alta 17 (CP-002, 003, 004, 005, 006, 007, 015, 017, 018, 021, 022, 023, 024, 025, 030, 033), Media 14, Baja 7. Nota: la lista de Alta suma 16 IDs; el total es 38 = 16 Alta + 15 Media + 7 Baja, conteo corregido abajo.

Conteo verificado contra la tabla: Alta = 16 (CP-002, 003, 004, 005, 006, 007, 015, 017, 018, 021, 022, 023, 024, 025, 030, 033); Media = 15 (CP-001, 008, 009, 012, 016, 019, 020, 026, 028, 029, 031, 032, 034, 035, 037); Baja = 7 (CP-010, 011, 013, 014, 027, 036, 038). Total = 38.

**Subset de humo (tras un deploy)**: CP-002, CP-003, CP-004, CP-005 (secuencia del flujo mínimo: solicitar, recibir el email, cambiar la contraseña, iniciar sesión).

**Orden de ejecución sugerido**:
1. Humo: CP-002, CP-003, CP-004, CP-005 (CP-001 se ejecuta antes de CP-002 por dependencia).
2. Alta: CP-006, CP-007, CP-015, CP-017, CP-018, CP-021, CP-022, CP-023, CP-024, CP-025, CP-030, CP-033.
3. Media: CP-001, CP-008, CP-009, CP-012, CP-016, CP-019, CP-020, CP-026, CP-028, CP-029, CP-031, CP-032, CP-034, CP-035, CP-037.
4. Baja: CP-010, CP-011, CP-013, CP-014, CP-027, CP-036, CP-038.

## 5. Matriz de cobertura

| CA | Descripción | Casos que la cubren | Estado |
|---|---|---|---|
| CA-1 | Acceso desde login, ingreso de email y mensaje "Si el email existe..." | CP-001, CP-002, CP-007, CP-008, CP-009, CP-010, CP-011, CP-012, CP-013, CP-014, CP-015, CP-016, CP-036 | ✓ Cubierta |
| CA-2 | El sistema envía al email un enlace de restablecimiento | CP-003, CP-011, CP-012, CP-016, CP-017, CP-018, CP-019 | ✓ Cubierta |
| CA-3 | Al abrir el enlace, define nueva contraseña y el sistema confirma | CP-004, CP-006, CP-017, CP-021, CP-022, CP-023, CP-024, CP-025, CP-026, CP-027, CP-028, CP-029, CP-030, CP-031, CP-032, CP-033, CP-034, CP-037, CP-038 | ✓ Cubierta |
| CA-4 | Con la nueva contraseña, el usuario puede iniciar sesión | CP-005, CP-006, CP-026, CP-027, CP-031, CP-037 | ✓ Cubierta |

**Cobertura: 4 de 4 CAs = 100%.** Sin CAs sin cubrir. Casos exploratorios (sin CA): CP-020, CP-035.

No cubierto por decisión de riesgo (no hay CA ni pregunta que lo justifique): compatibilidad de navegadores/móvil (la HU no declara plataformas) y contenido/diseño del email (asunto, remitente, texto).

## 6. Supuestos asumidos

1. CA-2 se interpreta junto con CA-1: el email se envía solo si la dirección existe y la cuenta está activa; a direcciones no registradas no se envía nada (CP-007).
2. El email llega dentro de 5 minutos (CP-003).
3. El enlace del email usa HTTPS (CP-003, CP-032).
4. El nombre de perfil de la cuenta es visible y se mantiene tras el reset (CP-005).
5. La contraseña anterior deja de ser válida tras el restablecimiento (CP-006).
6. La diferencia de tiempo de respuesta entre email registrado y no registrado debe ser menor a 500 ms (CP-007).
7. Validación del email (P-7): vacío, solo espacios, sin formato válido o de más de 254 caracteres muestran "Ingresá un email válido" sin enviar solicitud; se aplica trim y comparación sin distinguir mayúsculas (CP-008 a CP-015).
8. Los emails con unicode se aceptan como mensaje genérico o error de formato, nunca con error técnico (CP-014).
9. Un doble submit no duplica emails (CP-016).
10. Una nueva solicitud invalida el enlace anterior y el enlace es de un solo uso (P-2; CP-017, CP-023, CP-034).
11. Límite de 5 solicitudes por hora por email, con respuesta idéntica a la normal (P-5; CP-018).
12. Ante falla del servicio de notificaciones se muestra el mensaje genérico y se registra en logs (P-4; CP-019).
13. Ante pérdida de red no se muestra el mensaje de éxito (CP-020).
14. El enlace vence a los 60 minutos (P-1; CP-021, CP-022).
15. Política de contraseña (P-3): 8 a 64 caracteres, al menos 1 letra y 1 número, campo "Confirmar contraseña" que debe coincidir, unicode permitido, repetir la contraseña actual permitido (CP-025 a CP-031, CP-038).
16. Se invalidan todas las sesiones activas al restablecer la contraseña (P-6; CP-033).
17. Textos (P-8): confirmación "Tu contraseña fue actualizada", enlace inválido "El enlace no es válido o expiró", error de política "La contraseña no cumple los requisitos"; cuenta desactivada = mensaje genérico y sin email (CP-004, CP-022, CP-024, CP-025, CP-035).
18. Enter envía el formulario (CP-036).

## 7. Auto-revisión

**Críticos**

- [x] Cada CA tiene ≥1 caso que la cubra (CA-1: 13 casos, CA-2: 7, CA-3: 19, CA-4: 6; cobertura 100%).
- [x] Cero comportamiento inventado: todo resultado no definido por la HU lleva `[SUPUESTO: ...]` o es exploratorio (CP-020, CP-035).
- [x] Pasos reproducibles por terceros: atómicos, con datos concretos (emails `qa.usuarioNN@flockit-test.com`, contraseñas exactas, longitudes construidas).
- [x] Resultados esperados observables: mensajes literales, conteo de emails, redirecciones, éxito/rechazo de login.
- [x] IDs únicos y secuenciales, CP-001 a CP-038, sin huecos.
- [x] Matriz de cobertura completa, 4/4 = 100%, verificada contra los casos listados.
- [x] Preguntas al PO: 8 (≤ 8), todas con default propuesto, ninguna trivial.

**Observaciones**

- [x] Negativos/bordes por encima de la guía (1 por cada 2 positivos): 5 funcionales y 33 negativos, bordes, excepciones y no funcionales.
- [x] Prioridades derivadas de la matriz probabilidad × impacto (sección 4).
- [x] Subset de humo marcado: CP-002, CP-003, CP-004, CP-005.
- [x] Sin casos duplicados (cada caso varía acción, dato o assertion).
- [x] Dependencias declaradas en Precondiciones (CP-002 depende de CP-001; CP-003 de CP-002; CP-004 de CP-003; CP-005 y CP-006 de CP-004).
- [x] Supuestos consolidados en la sección 6.
- [x] Observación conocida: la sección de priorización contiene un conteo de Alta inicial inconsistente (17) seguido del conteo verificado (16 Alta, 15 Media, 7 Baja = 38); el verificado contra la tabla es el correcto.
- [x] Observación conocida: CP-038 comparte el usuario qa.usuario26 con CP-037; si CP-037 se ejecutó antes, restaurar la contraseña del usuario a ClaveVieja#2024 (declarado en Precondiciones).
