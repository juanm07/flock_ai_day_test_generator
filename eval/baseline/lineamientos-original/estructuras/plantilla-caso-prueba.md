# Estructura de caso de prueba

> Plantilla canónica del agente. Si el equipo tiene template propio, reemplazar este archivo: los flujos y skills referencian este path, no duplican su contenido.

---

## Template

```markdown
### CP-NNN — [Título del caso]

| Campo | Valor |
|---|---|
| **Título** | Verificar que [acción] [resultado esperado] |
| **Módulo** | Área / feature del sistema |
| **Origen** | HU-XXX · CA-N (o "Exploratorio") |
| **Tipo** | Funcional / Negativo / Borde / Excepción / No funcional / Humo / Regresión / E2E |
| **Prioridad** | Alta / Media / Baja (según matriz de riesgo) |
| **Precondiciones** | Estado, datos y permisos necesarios antes del paso 1 |
| **Datos de prueba** | Valores concretos (no "un email válido", sino el email exacto) |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | ... | ... |
| 2 | ... | ... |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Qué capturar: screenshot, log, request/response |
| **Estado** | Pendiente / Aprobado / Fallido / Bloqueado / No aplicable |
| **Notas** | `[SUPUESTO: ...]`, dependencias de otros casos, referencias |
```

---

## Definición de campos

| Campo | Regla |
|---|---|
| **ID** | `CP-NNN`, secuencial y único dentro de la suite. Nunca se reusa un ID, aunque un caso se elimine. |
| **Título** | Formato "Verificar que..." u operación + resultado. Debe entenderse solo, sin leer el resto del caso. |
| **Módulo** | Dónde vive la funcionalidad. Usar la nomenclatura del equipo si existe. |
| **Origen** | Trazabilidad: qué HU y qué criterio de aceptación motiva el caso. "Exploratorio" si no viene de una HU. |
| **Tipo** | Ver glosario abajo. Un caso tiene UN tipo principal. |
| **Prioridad** | Sale de la matriz de riesgo del flujo (`flujo-hu-a-casos.md`, fase F5). No se "intuye". |
| **Precondiciones** | Todo lo que debe ser verdad ANTES del paso 1. Si dependen de otro caso, citarlo por ID (ej: "CP-001 ejecutado con éxito"). |
| **Datos de prueba** | Valores exactos concretos. Si el dato no existe, incluir cómo crearlo. |
| **Pasos** | Numerados, atómicos: un verbo, una acción por paso. Sin pasos con "y". |
| **Resultado esperado** | Observable y assertable: otra persona puede decir "sí, pasó" o "no, falló" sin interpretar. |
| **Evidencia sugerida** | Qué capturar para poder auditar el resultado sin haber estado ahí. |
| **Notas** | Supuestos siempre con el marcador `[SUPUESTO: ...]`. |

---

## Reglas de redacción

1. **Pasos atómicos**: "1. Ingresar el email → 2. Tocar 'Recuperar'", no "1. Ingresar el email y tocar Recuperar".
2. **Resultado esperado observable**: evitar "funciona correctamente", "se ve bien". Escribir qué se ve, qué mensaje aparece, a dónde navega.
3. **Datos concretos**: `qa.usuario01@empresa.com`, no "un email válido". Un caso con datos abstractos no es reproducible.
4. **Un assertion principal por paso**: si un paso valida tres cosas, es un paso triple → dividir.
5. **Sin comportamiento inventado**: si la HU no define qué pasa en ese escenario, el resultado esperado lleva `[SUPUESTO: ...]` o el caso se marca exploratorio.

---

## Glosario de tipos

| Tipo | Qué cubre |
|---|---|
| **Funcional** | Happy path y variantes válidas de un criterio de aceptación |
| **Negativo** | Entradas inválidas, acciones prohibidas, permisos insuficientes, estados inválidos |
| **Borde** | Valores límite y particiones de equivalencia (mín, máx, ±1, vacío, extremos) |
| **Excepción** | Condiciones adversas: timeout, red caída, dependencia en error, concurrencia |
| **No funcional** | Seguridad, performance, compatibilidad, i18n, accesibilidad |
| **Humo** | Subset mínimo que valida que lo básico funciona tras un deploy |
| **Regresión** | Verifica que funcionalidad existente no se rompió |
| **E2E** | Flujo completo de punta a punta, cruzando módulos |

---

## Ejemplo mínimo relleno

```markdown
### CP-004 — Verificar que un email no registrado recibe el mismo mensaje que uno registrado

| Campo | Valor |
|---|---|
| **Título** | Verificar que un email no registrado recibe el mismo mensaje que uno registrado |
| **Módulo** | Login / Recuperación de contraseña |
| **Origen** | HU-101 · CA-1 |
| **Tipo** | Negativo (seguridad) |
| **Prioridad** | Alta |
| **Precondiciones** | El email inexistente@empresa.com NO existe en el sistema |
| **Datos de prueba** | inexistente@empresa.com |

**Pasos y resultado esperado**

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | En el login, tocar "Olvidé mi contraseña" | Se muestra el formulario de recuperación |
| 2 | Ingresar inexistente@empresa.com y confirmar | Se muestra el mensaje genérico "Si el email existe, recibirás un enlace" (idéntico al de un email registrado) |
| 3 | Revisar la bandeja de inexistente@empresa.com | No llega ningún email |

| Campo | Valor |
|---|---|
| **Evidencia sugerida** | Screenshot del mensaje en paso 2; bandeja vacía en paso 3 |
| **Estado** | Pendiente |
| **Notas** | Anti-enumeración de usuarios: el sistema no debe revelar qué emails existen. Comparar también el tiempo de respuesta vs. un email registrado (no debe diferir visiblemente). |
```
