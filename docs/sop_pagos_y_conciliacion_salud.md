# SOP de Pagos y Conciliacion Salud

Objetivo: operar incidencias de pago del bloque de salud sin perder trazabilidad del expediente.

Aplica a:
- `Derecho de peticion en salud`
- `Tutela en salud`
- `Impugnacion`
- `Desacato`

## 1. Fuentes de verdad

Revisar siempre estas tres capas:
- estado visible del expediente en panel
- `payment_summary` dentro de `submission_summary`
- timeline del caso con eventos de pago

Referencias tecnicas:
- `POST /cases/{case_id}/payments/wompi/session`
- `GET /payments/{reference}`
- `POST /payments/wompi/reconcile`
- `POST /payments/wompi/webhook`
- `POST /payments/wompi/webhook/sandbox`

Eventos utiles del timeline:
- `payment_order_created`
- `payment_webhook_updated`
- `payment_reconciled`
- `payment_confirmed`
- `payment_confirmed_test`

## 2. Datos minimos a pedir o revisar

Antes de actuar, confirmar:
- id del expediente
- correo de la cuenta
- referencia del intento de pago
- estado visible en panel
- producto cobrado
- si hubo debito real o solo intento rechazado

Si el usuario contacta soporte, pedir:
- referencia Wompi
- captura o comprobante si existe
- hora aproximada del intento
- ultimos 4 digitos si el banco debito y luego hubo error

## 3. Estados y que hacer

### Aprobado

Senales:
- `payment_status = pagado`
- `payment_summary.latest_status = approved`

Accion:
- confirmar que el documento ya pueda activarse o generarse
- si el usuario no ve activacion, refrescar expediente y revisar timeline
- si sigue inconsistente, escalar como bug de sincronizacion

Cierre esperado:
- expediente con pago confirmado
- referencia visible
- siguiente paso desbloqueado

### Pendiente

Senales:
- `payment_status = pendiente`
- `payment_summary.latest_status = pending`

Accion:
1. Esperar unos segundos y refrescar el expediente.
2. Revisar `GET /payments/{reference}`.
3. Si existe `transaction_id`, ejecutar conciliacion manual por `POST /payments/wompi/reconcile`.
4. Si despues de eso sigue pendiente, informar al usuario que el pago esta en validacion y que conserve la referencia.

Cierre esperado:
- o cambia a `pagado`
- o queda documentado como `pendiente en validacion`

### Rechazado

Senales:
- `payment_status = rechazado`
- `payment_summary.latest_status = declined`

Accion:
- informar al usuario que el intento fue rechazado
- pedir nuevo intento de pago
- conservar la referencia rechazada en caso de disputa
- no habilitar documento ni radicacion

Cierre esperado:
- usuario informado
- referencia rechazada trazable
- nuevo intento si el usuario quiere continuar

### Error

Senales:
- `payment_status = error`
- `payment_summary.latest_status = error`

Accion:
1. Revisar si el usuario reporta debito real.
2. Si no hubo debito, pedir nuevo intento.
3. Si si hubo debito, conservar referencia y escalar a conciliacion manual.
4. Ejecutar reconciliacion si ya existe `transaction_id`.
5. Si no cambia y hay cobro real, abrir incidencia interna.

Cierre esperado:
- o nuevo intento limpio
- o incidente de conciliacion abierto con referencia y evidencia

### Anulado

Senales:
- `payment_status = anulado`
- `payment_summary.latest_status = voided`

Accion:
- informar al usuario que esa orden ya no sirve
- crear un nuevo intento si desea continuar
- no reutilizar la orden anulada

Cierre esperado:
- nueva orden creada o caso cerrado sin activacion

## 4. Conciliacion manual por referencia

Usar cuando:
- el usuario dice que pago pero el expediente sigue pendiente
- la redireccion volvio antes que el webhook
- el estado quedo en error pero hay indicio de cobro real

Secuencia:
1. Buscar la referencia en el panel del expediente.
2. Consultar `GET /payments/{reference}`.
3. Si ya se conoce `transaction_id`, llamar `POST /payments/wompi/reconcile`.
4. Revisar si aparece evento `payment_reconciled`.
5. Confirmar si `payment_status` del expediente cambio a `pagado`.

Si no cambia:
- dejar la referencia documentada
- no habilitar manualmente el documento salvo instruccion expresa
- escalar como incidencia de conciliacion

## 5. Lo que nunca se debe hacer

- no marcar un expediente como pagado solo por captura de pantalla
- no habilitar documento por intuicion sin referencia trazable
- no borrar referencias viejas aunque el usuario haga un nuevo intento
- no asumir que la redireccion final equivale a pago aprobado

## 6. Evidencia minima que debe quedar

Por cada incidencia, dejar:
- referencia del pago
- estado observado
- accion tomada
- si hubo reconciliacion manual
- resultado final

Idealmente visible en:
- timeline del expediente
- notas internas o SOP operativo humano

## 7. Respuestas cortas sugeridas para soporte

### Pago pendiente

`Vemos tu intento de pago con referencia {referencia}. Aun aparece en validacion. Conserva esa referencia mientras confirmamos el estado final.`

### Pago rechazado

`El intento con referencia {referencia} fue rechazado. Puedes volver a intentarlo con otro medio de pago si quieres seguir con el expediente.`

### Pago con error y posible debito

`La orden con referencia {referencia} aparece con error. Si tu banco si debito el valor, envia el comprobante y conservaremos esta referencia para conciliacion manual.`

### Pago anulado

`La orden con referencia {referencia} quedo anulada. Para continuar debes iniciar un nuevo intento de pago.`

## 8. Estado actual del sistema

Hoy ya existe:
- creacion de orden de pago
- webhook de Wompi
- reconciliacion manual por transaccion
- resumen visible de pago en panel
- estados diferenciados `pendiente`, `pagado`, `rechazado`, `error`, `anulado`

Sigue pendiente:
- prueba controlada formal de reintentos de webhook sin duplicados
- SOP humano de escalacion externa si hay cobro real no conciliado
- validacion operativa con casos reales
