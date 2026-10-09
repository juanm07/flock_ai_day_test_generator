# HU de ejemplo (sintética)

> Ejemplo fabricado para calibrar al agente. Reemplazar por una HU real anonimizada del equipo cuando exista. Tiene lagunas deliberadas: el valor del ejemplo está en que el agente las detecte.

---

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

---

## Lagunas deliberadas (para el que calibra)

- No define la **expiración del enlace**.
- No define la **política de contraseña** (longitud, caracteres).
- No define **rate limiting** ni límite de intentos.
- No define si un **enlace nuevo invalida los anteriores**.
- No define si el reset **cierra sesiones activas** en otros dispositivos.
- No define el comportamiento con **cuentas bloqueadas/desactivadas**.
- No define i18n, navegadores soportados ni accesibilidad.
