# Acta Trazabilidad de Pagos Wompi (2026-05-02)

Estado: en ejecucion.

## Objetivo
Verificar trazabilidad completa por pago y confirmar idempotencia de reintentos webhook.

## Campos obligatorios por caso auditado
- `reference`
- `transaction_id`
- timestamp de creacion de sesion checkout
- timestamp de conciliacion o webhook
- estado final en orden (`approved/pending/declined`)
- estado final en caso (`pagado/pendiente/rechazado`)
- evidencia de no duplicidad en reintento

## Matriz de auditoria (llenar)
| Caso | reference | transaction_id | session_ts | webhook_ts | reconcile_ts | estado_orden | estado_caso | reintento_webhook | duplicidad |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |  |

## Criterio de cierre
- 5/5 referencias auditadas con trazabilidad completa.
- Reintentos webhook sin cambios duplicados de estado ni registros duplicados.

## Estado actual
- Pendiente corrida formal de auditoria con 5 referencias reales/sandbox.
