# Matriz de Ejecucion QA Lanzamiento Salud

Objetivo: registrar de forma operativa el resultado real de la validacion del bloque de salud antes del soft launch.

Fecha objetivo de salida:
- `15 de abril de 2026`

Modo de uso:
- correr cada caso de arriba hacia abajo
- llenar `resultado real`
- marcar `pasa` o `no pasa`
- dejar nota corta si aparece un hallazgo

## Matriz

| ID | Caso | Producto esperado | Validacion clave | Resultado esperado | Resultado real | Pasa / No pasa | Notas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `peticion_eps_respuesta_ordinaria` | Derecho de peticion en salud | La recomendacion no debe empujar a tutela | Preview viable, ruta correcta, documento de peticion | Pendiente | Pendiente | |
| 2 | `tutela_continuidad_tratamiento` | Tutela en salud | Debe priorizar urgencia y continuidad | Viabilidad alta, ruta correcta, tutela desbloqueada | Pendiente | Pendiente | |
| 3 | `tutela_debil_sin_datos` | No tutela fuerte | Debe pedir mas datos y bloquear generacion debil | Ruta conservadora o faltantes visibles | Pendiente | Pendiente | |
| 4 | `impugnacion_fallo_negado` | Impugnacion | No debe avanzar sin fallo previo legible | Con fallo avanza, sin fallo bloquea | Pendiente | Pendiente | |
| 5 | `desacato_incumplimiento_fallo` | Desacato | No debe avanzar sin fallo favorable legible | Con fallo avanza, sin fallo bloquea | Pendiente | Pendiente | |
| 6 | `pago_aprobado_documento_activo` | Pago confirmado | Debe desbloquear documento y mostrar referencia | Estado confirmado, timeline y panel correctos | Pendiente | Pendiente | |
| 7 | `pago_rechazado_o_error` | Pago no confirmado | Debe mostrar estado y accion correcta | Rechazado o error visible, referencia trazable | Pendiente | Pendiente | |
| 8 | `seguimiento_post_radicado` | Seguimiento del caso | Debe guiar el siguiente paso con claridad | Novedad visible, watch items y escalation claros | Pendiente | Pendiente | |

## Reglas de aprobado

- `Pasa` solo si la ruta, el bloqueo y el siguiente paso coinciden con lo esperado.
- `No pasa` si:
  - recomienda el producto equivocado
  - deja avanzar cuando debia bloquear
  - bloquea cuando debia avanzar
  - el panel no deja claro el siguiente paso
  - el estado de pago o radicacion es confuso

## Corte de salida

Para abrir soft launch:
- los casos `1` a `5` deben pasar
- los casos `6` a `8` no pueden tener fallos criticos

Si falla alguno de estos, no abrir:
- `2` tutela fuerte
- `4` impugnacion con fallo
- `5` desacato con fallo
- `6` pago aprobado

## Hallazgos criticos

Registrar aqui cualquier hallazgo que bloquee salida:

| Fecha | Caso | Hallazgo | Severidad | Estado |
| --- | --- | --- | --- | --- |
| Pendiente |  |  |  |  |
