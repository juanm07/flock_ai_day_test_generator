# Taxonomía de severidad y prioridad

> Escala canónica del agente. Si el equipo usa otra (Blocker/Critical/Major/Minor, o numérica 1-5), reemplazar este archivo.

---

## Severidad — impacto del defecto en el sistema

| Nivel | Nombre | Definición | Ejemplos |
|---|---|---|---|
| **S1** | Bloqueante | Bloquea un flujo crítico sin workaround, o corrompe/pierde datos, o tumba el sistema | No se puede iniciar sesión; el checkout falla siempre; se borran datos de producción |
| **S2** | Mayor | Funcionalidad clave degradada; hay workaround difícil o solo para un subconjunto de usuarios | Un tipo de usuario no puede exportar; el flujo falla 1 de cada 5 veces; workaround que exige resetear datos |
| **S3** | Menor | Funcionalidad secundaria afectada, o hay workaround simple | Un filtro no ordena; un reporte muestra un total con error; se puede hacer por otro camino |
| **S4** | Trivial | Cosmético, sin impacto funcional | Desalineación de un texto, un ícono feo, un typo en un mensaje |

**Reglas de ajuste:**

- **Seguridad**: un bug de seguridad (fuga de datos, enumeración de usuarios, acceso sin permiso) nunca baja de **S2**, aunque afecte a pocos usuarios.
- **Datos**: corrupción o pérdida de datos es siempre **S1**, aunque el flujo "parezca" terminar bien.
- **Frecuencia**: un fallo intermitente de flujo crítico no baja de severidad por ser intermitente (el impacto cuando ocurre es el mismo); la intermitencia afecta a la *prioridad* de investigación.

---

## Prioridad — urgencia de arreglo

| Nivel | Cuándo se arregla |
|---|---|
| **P1** | Ya: bloquea el release o la operación. Se hotfixea si hace falta. |
| **P2** | Dentro del sprint actual. |
| **P3** | Backlog del próximo sprint / release próximo. |
| **P4** | Cuando se pueda; candidato a "no arreglar" explícito. |

La prioridad se decide con la matriz de abajo + contexto de negocio (fecha de release, % de usuarios afectados, si es regresión de algo que funcionaba).

---

## Matriz de decisión

| | Severidad S1 | S2 | S3 | S4 |
|---|---|---|---|---|
| **Regresión** (antes funcionaba) | P1 | P1 | P2 | P3 |
| **Muchos usuarios / Prod** | P1 | P2 | P3 | P4 |
| **Pocos usuarios / QA** | P1 | P2/P3 | P3 | P4 |
| **Antes del release** | P1 | P1/P2 | P2 | P3 |

Lectura: severidad define el piso de la prioridad; el contexto solo puede subirla, nunca bajarla por debajo del piso. (Regla R5: la severidad es un hecho del defecto; la prioridad es una decisión de negocio.)

---

## Casos particulares

- **No reproducible aún**: severidad preliminar según lo reportado + `[PENDIENTE: reproducir]`. No se promociona a confirmado hasta reproducirlo o juntar evidencia.
- **Información faltante**: clasificación preliminar condicionada: "S2 preliminar, condicionada a confirmar si afecta a todos los usuarios".
- **Bugs de seguridad**: prioridad mínima P2 siempre; P1 si expone datos o permite acceso no autorizado.
- **Múltiples síntomas en un reporte**: clasificar cada defecto por separado; no promediar.
