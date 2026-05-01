# SOP de Responsables y SLA Salud

Objetivo: definir responsable operativo y tiempos maximos de respuesta para incidencias del bloque salud.

Alcance:
- Pago no reflejado
- Pago rechazado o error con posible debito
- Conciliacion manual por referencia
- Documento bloqueado por QA juridico
- Radicado sin comprobante visible

## 1. Responsable operativo

Rol responsable:
- `Coordinacion Operativa Salud` (owner de soporte diario del bloque salud)

Canal principal:
- `soporte@123tutelaapp.com`

Canales de apoyo:
- `radicaciones@123tutelaapp.com` (acuse/radicado/envio)
- `notificaciones@123tutelaapp.com` (copias y avisos al cliente)

Regla de cobertura:
- Lunes a viernes, 08:00 a 18:00 (hora Colombia)
- Sabados, 08:00 a 12:00 para incidencias criticas

## 2. SLA interno por tipo de incidencia

- Pago aprobado no reflejado en UI:
  - Primer acuse interno: <= 15 minutos
  - Verificacion y conciliacion inicial: <= 30 minutos
  - Cierre esperado: <= 2 horas

- Pago rechazado:
  - Primer acuse interno: <= 15 minutos
  - Confirmacion de estado y guia al cliente: <= 30 minutos
  - Cierre esperado: <= 1 hora

- Conciliacion manual por referencia:
  - Primer acuse interno: <= 15 minutos
  - Ejecucion de conciliacion: <= 45 minutos
  - Cierre esperado: <= 4 horas

- Documento bloqueado por QA juridico:
  - Primer acuse interno: <= 30 minutos
  - Diagnostico de faltantes accionables: <= 2 horas
  - Cierre esperado (con datos completos): <= 8 horas habiles

- Radicado sin comprobante visible:
  - Primer acuse interno: <= 30 minutos
  - Confirmacion de envio y estado de comprobante: <= 2 horas
  - Cierre esperado: <= 8 horas habiles

## 3. Priorizacion minima

- P1:
  - Pago cobrado con expediente bloqueado
  - Error operativo que impide generar o enviar documento pagado
- P2:
  - Radicado sin comprobante visible
  - Bloqueo QA con faltantes claros
- P3:
  - Dudas de estado, seguimiento informativo, consultas de trazabilidad

## 4. Criterio de cierre

Toda incidencia debe cerrar con:
- referencia de expediente
- estado inicial y estado final
- accion aplicada
- evidencia en timeline o nota de expediente
- mensaje final al cliente con siguiente paso
