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

## Matriz de auditoria (actualizada con transacciones disponibles en Wompi)
| Caso | reference | transaction_id | session_ts | webhook_ts | reconcile_ts | estado_orden | estado_caso | reintento_webhook | duplicidad |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 123T-PAGO_PRUEBA-79053A68-FC5AB3E461 | 1368581-1777670347-31543 | Pendiente de extraer (backend) | Pendiente de extraer (backend) | Pendiente de extraer (backend) | APPROVED | Pagado (esperado) | Pendiente | Pendiente |
| 2 | 123T-HAZLOPORMI_V1-5DD71C91-1E0C886B62 | 1368581-1777327571-17605 | Pendiente de extraer (backend) | Pendiente de extraer (backend) | Pendiente de extraer (backend) | DECLINED | Rechazado/Pendiente (esperado) | Pendiente | Pendiente |
| 3 | 123T-ACCION_TUTELA-D2630A7C-A0B24A520A | 1368581-1773873653-77545 | Pendiente de extraer (backend) | Pendiente de extraer (backend) | Pendiente de extraer (backend) | APPROVED | Pagado (esperado) | Pendiente | Pendiente |
| 4 | 123T-PAGO_PRUEBA-BD0697A2-BA18454889 | 1368581-1773607590-36203 | Pendiente de extraer (backend) | Pendiente de extraer (backend) | Pendiente de extraer (backend) | APPROVED | Pagado (esperado) | Pendiente | Pendiente |

## Criterio de cierre
- 5/5 referencias auditadas con trazabilidad completa.
- Reintentos webhook sin cambios duplicados de estado ni registros duplicados.

## Estado actual
- Pre-cierre provisional de pre-lanzamiento con 4 transacciones disponibles.
- Pendiente completar:
  - extraccion de timestamps y estado final del caso en backend por cada referencia
  - prueba de reintento webhook (misma transaccion) para confirmar idempotencia sin duplicados
- Cierre definitivo cuando se complete la evidencia de no duplicidad y/o al llegar a 5 transacciones en semana 1 de go-live.
