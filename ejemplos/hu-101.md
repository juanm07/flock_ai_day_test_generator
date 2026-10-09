## HU-101 — Recuperación de contraseña

**Como** usuario registrado que olvidé mi contraseña,
**quiero** restablecerla mediante un enlace enviado a mi email,
**para poder** volver a acceder a mi cuenta sin perder mis datos.

**Criterios de aceptación:**

1. El usuario accede a "Olvidé mi contraseña" desde la pantalla de login, ingresa su email y el sistema muestra el mensaje "Si el email existe, recibirás un enlace para restablecer tu contraseña".
2. El sistema envía al email un enlace de restablecimiento.
3. Al abrir el enlace, el usuario define una nueva contraseña y el sistema confirma que se actualizó.
4. Con la nueva contraseña, el usuario puede iniciar sesión.

**Notas del equipo:** el email lo manda el servicio de notificaciones existente.

