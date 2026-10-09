# Estructura de bug

> Plantilla canónica del agente. Si el equipo tiene template propio (Jira, Azure DevOps, etc.), reemplazar este archivo: los flujos y skills referencian este path.

---

## Template

```markdown
# BUG-NNN — [Módulo] Síntoma en una línea

| Campo | Valor |
|---|---|
| **Título** | [Módulo] síntoma observable, sin interpretaciones |
| **Severidad** | S1 / S2 / S3 / S4 (según `taxonomia-severidad-prioridad.md`) |
| **Prioridad** | P1 / P2 / P3 / P4 |
| **Ambiente** | Aplicación: [versión/build] · Entorno: QA/Staging/Prod · Plataforma: navegador/SO/dispositivo |
| **Reportado por / Fecha** | Quién y cuándo |
| **Reproducibilidad** | Siempre / Intermitente (N de M intentos) / Una vez / No reproducible aún |
| **Usuario/Rol afectado** | Qué perfil de usuario reproduce el bug |

**Precondiciones**
- Estado y datos necesarios antes del paso 1.

**Pasos para reproducir**

| # | Acción |
|---|--------|
| 1 | ... |
| 2 | ... |

**Resultado actual** (solo hechos observados)
- Qué se ve, qué mensaje aparece exactamente, qué comportamiento se observa.

**Resultado esperado**
- Qué debería pasar según la HU/CA, la lógica o el sentido común del producto.

**Evidencia**
- Screenshots, video, log, request/response, stack trace. Si no hay: `[PENDIENTE: pedir captura del error]`.

**Impacto**
- A quiénes afecta (todos los usuarios / un subconjunto con X condición / un rol), y qué no pueden hacer.

**Hipótesis / Notas** (separado de los hechos)
- Conjeturas sobre causa, posibles workarounds, datos relacionados. Todo lo que NO sea observación directa va acá.

**Información faltante** `[PENDIENTE]`
- Campo: qué falta y por qué importa.
```

---

## Definición de campos

| Campo | Regla |
|---|---|
| **Título** | `[Módulo] + síntoma observable`. Accionable y autónomo: se entiende en una lista de 200 bugs. Nunca "no funciona" solo. |
| **Severidad** | Impacto técnico/funcional del defecto. Se justifica citando la taxonomía. **No se negocia por deadlines** (regla R5). |
| **Prioridad** | Urgencia de arreglo. Sí incorpora contexto de negocio: fecha de release, clientes afectados, riesgo. |
| **Ambiente** | Versión exacta si se conoce; si no: `[PENDIENTE: versión]`. Nunca inventar versión. |
| **Reproducibilidad** | Con tasa cuando sea posible ("3 de 3", "2 de 10"). Intermitente ≠ poco importante. |
| **Resultado actual** | **Solo hechos** (regla R2). Texto exacto del error, no un resumen de opinión. |
| **Resultado esperado** | Fuente: HU/CA si existe; si no existe, se marca como `[SUPUESTO: comportamiento razonable]` y es candidato a pregunta al PO. |
| **Hipótesis** | SIEMPRE separado del resultado actual. Etiquetar el nivel de confianza si aporta. |
| **Información faltante** | Todo campo sin dato va con `[PENDIENTE: ...]` + la pregunta específica para conseguirlo. Rellenar con ficción está prohibido (R6). |

---

## Reglas de redacción

1. **Título con módulo y síntoma**: `[Login] Error al iniciar sesión con contraseñas que contienen "ñ"`, no "Problema con el login".
2. **Pasos reproducibles por terceros**: alguien que nunca vio el bug debe poder reproducirlo. Incluir el paso que parece "obvio" (ej: qué botón, qué URL).
3. **Texto de error literal**: copiar el mensaje exacto entre comillas, no parafrasearlo.
4. **Hechos arriba, conjeturas abajo**: quien lee el bug debe poder distinguir evidencia de interpretación sin dudar.
5. **Un bug = un defecto**: si el reporte suelto contiene 2 problemas distintos, generar 2 bugs y aclararlo.
6. **Nada de culpa ni humor en el cuerpo**: el bug es un artefacto técnico que va a durar años en el tracker.

---

## Ejemplo mínimo relleno

Ver `ejemplos/salida-bug-ejemplo.md` para un caso completo con `[PENDIENTE]`s y preguntas de seguimiento.
