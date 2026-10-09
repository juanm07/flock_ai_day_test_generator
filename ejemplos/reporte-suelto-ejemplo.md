# Reporte suelto de ejemplo (sintético)

> Ejemplo fabricado para calibrar al agente: simula un mensaje informal recibido por chat interno. Reemplazar por un reporte real anonimizado cuando exista.

---

> **Mensaje original de Soporte (recibido por chat):**
>
> "che tengo un problema con el login de staging... desde ayer más o menos. pongo mi contraseña (que tiene una ñ porque me gusta complicarme jaja) y me tira un error rojo que decía algo de caracteres no válidos. pero esa contraseña la uso hace meses! después probé reseteando la contraseña a una sin ñ y ahí pude entrar sin problema. no me acuerdo bien qué decía el error exacto. estoy en chrome, la última versión creo. me pasó las 3 veces que probé. ah, en firefox no lo probé porque ahí nunca me logueo. mi usuario es jperez arroba empresa punto com. no tengo captura, disculpá"

---

## Qué debe detectar el agente en este reporte

- **Hechos sólidos**: entorno staging, desde ayer, síntoma (login falla con contraseña con "ñ"), workaround hallado por el usuario (resetear a contraseña sin ñ), reproducibilidad 3/3 en Chrome.
- **Faltantes críticos**: versión/build de la app, texto exacto del error, evidencia (captura/log), pasos formales ordenados, si pasa en otros navegadores.
- **Faltantes secundarios**: impacto en otros usuarios, si también falla al CREAR una contraseña con ñ (el usuario la tiene "desde hace meses", lo que sugiere que la creación con ñ funcionó → posible regresión reciente).
- **Hipótesis separable** (no confundir con hecho): el usuario "cree" que es la ñ; el agente lo trata como hipótesis razonable y arma el caso para confirmarlo.
