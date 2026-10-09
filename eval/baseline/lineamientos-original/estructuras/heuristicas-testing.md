# Heurísticas de testing — el "ojo" del agente

> Guía de decisión para que la suite no sea solo happy path. El agente las aplica en la fase de diseño del flujo HU→casos.

---

## Regla de aplicación: riesgo primero

NO se aplican todas las heurísticas a todo. Se diseñan primero los casos de mayor riesgo:

1. **Piso mínimo obligatorio**: por cada criterio de aceptación, ≥1 caso funcional; por cada entrada de datos del usuario, ≥1 negativo y ≥1 borde.
2. **Luego, según tipo de funcionalidad**: usar la tabla de selección de abajo, que dice qué heurísticas tipicamente aplican.
3. **No funcionales**: solo los que el riesgo justifica; en funcionalidades de auth, dinero o datos personales, seguridad es obligatorio.

---

## 1. Positivos (happy path y variantes)

- Happy path de cada criterio de aceptación.
- Variantes válidas: distinto rol/permiso, distinto estado inicial, distinto dato válido.
- ¿El flujo funciona con los datos reales del día a día (no solo datos "de demo")?

## 2. Negativos

- Entradas inválidas por **tipo** (texto donde va número), **formato** (email sin @), **longitud** (excede máximo), **obligatoriedad** (campos vacíos).
- **Acciones prohibidas**: llamar a la acción sin permiso, en estado inválido, desde otra cuenta, por URL directa (deep-link a pantalla restringida).
- **Cancelación y abandono**: cancelar a mitad de flujo, irse sin guardar, cerrar el modal.
- **Doble submit**: doble click en el botón, Enter + click, reenvío del formulario.

## 3. Bordes y particiones de equivalencia

Para cada entrada, probar el límite y sus vecinos (mín-1, mín, mín+1, máx-1, máx, máx+1):

| Tipo de entrada | Casos de borde |
|---|---|
| Numérico | 0, -1, mín, mín±1, máx, máx±1, decimales, separador de miles/punto-comma |
| Texto | Vacío, solo espacios, 1 carácter, longitud exacta, longitud máx+1, unicode (ñ, acentos, emoji), copiar-pegar |
| Fecha/hora | Formato alternativo (31/12 vs 12/31), fecha futura/pasada inválida, 29/2, cambio de día a mitad de operación, zona horaria |
| Archivo | 0 bytes, muy grande, tipo incorrecto, doble extensión (`foto.jpg.exe`), nombre con caracteres especiales |
| Lista/colección | Vacía, 1 elemento, muchos, duplicados, elemento borrado mientras se usa |

## 4. Excepciones y robustez

- Red caída / lenta en cada punto de espera del flujo.
- Timeout y error 5xx de cada dependencia (API externa, cola de emails, pasarela de pago).
- **Back / refresh / cerrar pestaña** en medio del flujo: ¿qué pasa con el estado?
- **Concurrencia**: dos sesiones del mismo usuario, dos usuarios sobre el mismo dato, operación simultánea.
- Datos corruptos o estados "imposibles" que la base igual podría contener.

## 5. No funcionales (mínimo pragmático)

**Seguridad** (obligatorio en auth, dinero, datos personales):
- Autorización: cada acción restringida probada con un rol SIN permiso (no solo con permiso).
- Anti-enumeración: mensajes que no revelan qué emails/usuarios existen.
- Inyección básica: `<script>`, `' OR 1=1 --`, caracteres de escape.
- Fuga de información en mensajes de error (stack traces, queries, emails ajenos).
- Campos readonly/hidden del front no confiables: replicar el request "mal" desde el backend si aplica.

**Performance** (humo): masa de datos razonable, respuesta < umbral del equipo en la operación típica.

**Compatibilidad**: navegadores del equipo (mínimo: el declarado como soportado), móvil si el producto lo es, resoluciones extremas.

**i18n/encoding**: contenido con ñ, acentos, emoji, texto largo en espacios chicos (overflow).

**Accesibilidad** (humo): navegación por teclado del flujo, contraste del mensaje de error.

## 6. Estados y ciclo de vida

- Todas las transiciones de estado válidas, y al menos una inválida (saltearse un paso).
- Persistencia: ¿el estado sobrevive refresh/reinicio/relogin?
- "Resurrección": entidad borrada/desactivada que reaparece por un link viejo, un favorito, un email.

## 7. Datos y relaciones

- Duplicados (¿se pueden crear dos entidades idénticas? ¿debería?).
- Dependencias: borrar el padre, ¿qué pasa con los hijos?
- Referencias huérfanas; crear datos desde B mientras se los lista en A.

---

## Tabla de selección por tipo de funcionalidad

| Tipo de funcionalidad | Heurísticas típicas (además del piso mínimo) |
|---|---|
| **ABM / CRUD** | Duplicados (2), bordes de cada campo (3), borrado en uso (7), orden y paginación de la lista |
| **Login / autenticación** | Seguridad completa (5): roles, enumeración, sesiones; límite de intentos; unicode en credenciales (3); logout en múltiples pestañas (4) |
| **Formulario con validaciones** | Cada regla de validación: negativo + borde (2, 3); validación solo-cliente ¿se valida en el server? (5) |
| **Integración con terceros** | Errores del tercero (4), respuesta lenta, datos con formato inesperado, reintentos, idempotencia |
| **Reportes / export** | Sin datos, con 1 fila, con masa (3, 5); decimales y formato en export; columnas que se agregan/quitan |
| **Upload de archivos** | Bordes de archivo (3), archivos concurrentes, subida interrumpida (4) |
| **Búsqueda / filtros** | Sin resultados, caracteres especiales en el query (inyección, 5), combinaciones de filtros, performance con masa (5) |
| **Acciones críticas** (pagos, envíos, acciones irreversibles) | Doble submit (2), confirmación y cancelación, concurrencia (4), estado consistente post-error (4), auditabilidad |

---

## Anexo: heurísticas clásicas (para profundizar)

- **SFDIPOT** — Structure, Function, Data, Interfaces, Platform, Operations, Time: recorrer el sistema preguntando qué probar en cada dimensión.
- **FEW HICCUPPS** — Familiarity, Existing, Wanted, Imagined + History, Image, Comparable product, Claims, User expectations, Product, Purpose, Standards: oráculo de "¿esto es un bug?" cuando no hay especificación.
- Uso: como checklist mental al CERRAR el diseño de la suite ("¿me quedó algo sin SFDIPOT?"), no como burocracia delante de cada caso.
