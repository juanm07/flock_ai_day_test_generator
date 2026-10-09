# Checklist de ambigüedad y preguntas al PO

> **Versión ejecutable:** `rules/gaps.yaml` (reglas por tipo de funcionalidad + tope de 8 preguntas) y `rules/smells_es.yaml` (verificabilidad de los CAs), aplicadas por `tbg lint-hu`. Agregar una categoría acá sin agregar su regla no tiene efecto en la herramienta.

> El "ojo senior" aplicado a la HU antes de diseñar. Se usa en la fase F2 del flujo HU→casos, y puede ejecutarse solo (modo análisis rápido).

---

## Categorías a revisar (checklist)

### A. Criterios de aceptación
- [ ] ¿Hay CAs? Si no hay, es bloqueante.
- [ ] ¿Son verificables? "Carga rápido" no es verificable; "muestra resultados en < 2s" sí.
- [ ] ¿Hay contradicciones entre CAs o con HUs existentes?
- [ ] ¿El "para poder..." (objetivo) queda satisfecho por los CAs? A veces el objetivo pide más que lo que los CAs cubren.

### B. Datos y validaciones
- [ ] Límites: longitudes, rangos numéricos, tamaños de archivo.
- [ ] Formatos: email, teléfono, fecha, moneda, decimales.
- [ ] Obligatoriedad: qué campos pueden quedar vacíos.
- [ ] Caracteres permitidos: unicode, emojis, espacios.
- [ ] Datos existentes: ¿qué pasa con los datos ya creados cuando cambia una regla?

### C. Comportamiento ante errores
- [ ] ¿Qué pasa cuando falla cada dependencia (API, email, pasarela)?
- [ ] ¿Qué ve el usuario en cada fallo? ¿Se puede reintentar? ¿Se pierde trabajo?

### D. Permisos y roles
- [ ] ¿Qué roles pueden ejecutar la funcionalidad? ¿Y cuáles NO deben poder?
- [ ] ¿Los datos son visibles solo para quien corresponde?

### E. Estados y ciclo de vida
- [ ] Estados por los que pasa la entidad: ¿todas las transiciones están definidas?
- [ ] ¿Qué pasa con la funcionalidad si la entidad está desactivada/borrada/bloqueada?

### F. Seguridad
- [ ] Anti-enumeración: ¿algún mensaje revela qué usuarios/datos existen?
- [ ] Límite de intentos / rate limiting.
- [ ] Acciones sensibles: ¿pueden dispararse sin permiso (deep-link, API directa)?

### G. Concurrencia y sesiones
- [ ] ¿Qué pasa con dos sesiones del mismo usuario?
- [ ] ¿Qué pasa si se pide dos veces lo mismo?
- [ ] ¿Qué pasa con el estado al expirar la sesión a mitad del flujo?

### H. Alcance negativo
- [ ] ¿Qué NO hace esta funcionalidad? (el PO casi nunca lo escribe y evita scope creep)
- [ ] ¿Hay flujos alternos o excepciones explícitamente fuera de scope?

### I. Dependencias externas
- [ ] ¿Qué sistemas de terceros intervienen? ¿Quién define su comportamiento ante fallo?

### J. Experiencia y contexto
- [ ] Idioma/i18n del texto visible.
- [ ] Dispositivos/navegadores soportados.
- [ ] Accesibilidad esperada del flujo.

---

## Formato de cada pregunta

```markdown
**P-N. [Categoría] Pregunta concreta y cerrada cuando sea posible**
- **Por qué importa**: qué riesgo de diseño genera no tener la respuesta.
- **Default propuesto**: qué vamos a asumir si no hay respuesta (y que queda como [SUPUESTO] en los casos).
```

---

## Reglas

1. **Máximo ~8 preguntas** por HU. Si hay más, agrupar por categoría y priorizar: el PO que recibe 25 preguntas no responde ninguna.
2. **Nada de preguntas triviales**: si la respuesta no cambia el diseño de casos ni el riesgo, no va.
3. **Cerrada cuando se pueda**: "¿El enlace expira a las 24h o a las 1h?" mejor que "¿cuánto dura el enlace?".
4. **Siempre default propuesto**: el agente no se queda esperando; sigue con el supuesto marcado.
5. **Cada pregunta cita la categoría** del checklist: le muestra al PO que hubo método, no intuición.
6. Las preguntas BLOQUEANTES van primero, marcadas como tales.
