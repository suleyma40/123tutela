# SOP de QA, Radicado y Seguimiento Salud

Objetivo: operar incidencias posteriores al pago en el bloque de salud sin entregar documentos debiles ni perder trazabilidad del caso.

Aplica a:
- `Derecho de peticion en salud`
- `Tutela en salud`
- `Impugnacion`
- `Desacato`

## 1. Escenarios cubiertos

Este SOP cubre:
- documento bloqueado por QA o validacion final
- radicado sin comprobante visible para el cliente
- seguimiento manual reportado por el cliente

## 2. Documento bloqueado por QA

### Senales

Puede aparecer cuando:
- `generate_document` devuelve error `422`
- existe `document_quality` con `blocking_issues`
- existe `final_validation` con `apto_para_entrega = false`
- aparece evento `document_delivery_validation_blocked`

### Que revisar

Revisar en el expediente:
- `submission_summary.document_quality`
- `submission_summary.final_validation`
- preguntas pendientes del caso
- campos faltantes del intake

### Que hacer

1. Identificar si el bloqueo es por falta de datos del usuario o por refuerzo interno de la IA.
2. Si faltan datos del usuario:
   - pedir solo los faltantes accionables
   - no improvisar el documento
3. Si el bloqueo es interno de calidad:
   - regenerar cuando ya exista mejor contexto
   - no entregar el borrador como si fuera final
4. Si el caso es `impugnacion` o `desacato`, confirmar que el fallo previo siga legible y correctamente analizado.

### Cierre esperado

- o documento final generado sin bloqueos
- o caso devuelto al usuario con lista corta de datos pendientes

### Respuesta corta sugerida

`Tu documento aun no sale porque la validacion juridica detecto ajustes pendientes. Ya identificamos que falta y te pediremos solo los datos necesarios para cerrarlo bien.`

## 3. Radicado sin comprobante visible

### Senales

Puede pasar cuando:
- el caso ya aparece como `enviado` o `radicado`
- existe `submission_attempted`
- el cliente no ve `submission_summary.radicado`
- el canal de envio no devolvio acuse inmediato

### Que revisar

Revisar:
- `submission_summary.delivery_result`
- `submission_summary.last_channel`
- `submission_summary.last_destination`
- `submission_attempts`
- `guidance`
- si hubo copia enviada al cliente o a `radicaciones@123tutelaapp.com`

### Que hacer

1. Confirmar si el envio realmente salio.
2. Si el canal no genera radicado inmediato:
   - informar al cliente que el envio existe pero el comprobante aun no es visible
   - dejar seguimiento abierto
3. Si el cliente ya radico por su cuenta:
   - registrar por `manual-radicado`
   - guardar numero de radicado y nota
4. Si el despacho o entidad respondio por otro canal:
   - registrar novedad manual en seguimiento

### Nunca hacer

- no inventar numero de radicado para tranquilizar al cliente
- no marcar como `radicado` definitivo solo porque el correo salio, salvo que el sistema ya lo haya hecho por politica operativa

### Cierre esperado

- o comprobante visible en el expediente
- o estado claro de `envio realizado, comprobante pendiente`

### Respuesta corta sugerida

`El envio del documento ya quedo registrado, pero el comprobante aun no esta visible. En algunos canales el acuse llega despues. Si recibes respuesta directa, repórtala en el mismo expediente.`

## 4. Seguimiento manual del caso

### Senales

Aplica cuando el cliente reporta:
- llamada de la EPS
- correo del juzgado
- requerimiento adicional
- respuesta parcial
- incumplimiento posterior al radicado

### Herramienta actual

Existe endpoint:
- `POST /cases/{case_id}/follow-up`

Campos operativos:
- `note`
- `source`
- `received_at_label`

El expediente guarda:
- `submission_summary.last_follow_up_report`
- evento `judicial_update_reported`

### Que hacer

1. Pedir al cliente una nota corta y concreta.
2. Identificar la fuente:
   - `correo`
   - `llamada`
   - `panel`
   - `whatsapp`
   - `juzgado`
   - `eps`
3. Registrar el reporte en el expediente.
4. Revisar si el siguiente paso cambia:
   - seguir esperando
   - aportar nuevo soporte
   - preparar impugnacion
   - preparar desacato

### Cierre esperado

- novedad registrada
- siguiente paso sugerido actualizado para el caso

### Respuesta corta sugerida

`La novedad ya quedo registrada en tu expediente. Si la entidad o el juzgado te pidio algo adicional, sube ese soporte para decidir el siguiente paso correcto.`

## 5. Lista minima para soporte humano

Antes de cerrar cualquier incidencia, verificar:
- expediente correcto
- referencia de pago si aplica
- estado del documento
- estado del envio
- si existe o no radicado visible
- ultimo reporte de seguimiento

## 6. Estado actual del sistema

Hoy ya existe:
- bloqueo de entrega por QA y validacion final
- registro de intento de envio
- registro manual de radicado
- reporte manual de seguimiento
- panel con documento, radicado y siguientes pasos basicos

Sigue pendiente:
- SOP humano mas fino para decidir cuando escalar a impugnacion o desacato despues del seguimiento
- corrida formal con casos reales de cliente
