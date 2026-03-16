# Estrategia de Radicacion Operativa v1

Objetivo: cerrar una primera estrategia operativa para radicacion, comprobantes y continuidad del caso sin esperar la integracion final de todos los canales.

## 1. Principio rector

La radicacion no se considera terminada solo porque el documento exista. Debe quedar trazabilidad verificable de:

- canal usado
- destino
- evidencia del envio o radicado
- copia o comprobante entregado al cliente
- siguiente paso sugerido

## 2. Canales iniciales

### 2.1 Canal juridico de radicacion

Orden de preferencia:

1. portal oficial
2. correo institucional verificado
3. canal asistido o manual

Regla: `Evolution API` no sera canal juridico de radicacion por defecto. Su uso inicial sera para notificacion y continuidad con el cliente, no para presentar formalmente escritos ante entidades, salvo que exista aceptacion expresa y verificable del canal.

### 2.2 Canal de notificacion al cliente

Orden inicial:

1. panel del cliente
2. correo electronico
3. Evolution API / WhatsApp como capa posterior de notificacion cuando quede integrada

## 3. Matriz operativa por tipo de documento

| Producto | Canal primario esperado | Evidencia minima | Fallback |
|---|---|---|---|
| Derecho de peticion | correo institucional o portal de entidad | copia de correo, acuse o radicado | envio asistido/manual |
| Habeas data | correo institucional o formulario del responsable | copia del envio o captura del formulario | envio asistido/manual |
| Queja / reclamo | portal o correo de entidad | acuse, captura o copia | envio manual |
| Tutela | reparto judicial o correo judicial verificado | numero de radicado o copia integra del envio | preparacion para radicacion asistida |
| Impugnacion de tutela | mismo despacho o canal judicial del proceso | radicado, acuse o copia integra | radicacion asistida urgente |
| Incidente de desacato | mismo juzgado de primera instancia | radicado, acuse o copia integra | radicacion asistida urgente |

## 4. Evidencia minima por canal

### Portal oficial

- numero de radicado cuando exista
- captura o acuse del portal
- fecha y hora

### Correo institucional

- destinatario
- asunto
- fecha y hora
- copia del mensaje o `message-id` cuando despues se capture

### Manual o asistido

- instrucciones entregadas al cliente
- canal sugerido
- espacio para subir foto, PDF o numero de radicado

## 5. Post-radicado obligatorio

Despues de radicar, el sistema debe dejar listo:

- comprobante o evidencia
- estado del caso
- tiempo estimado de respuesta
- siguiente paso sugerido
- continuidad comercial posible

## 6. Rol inicial de Evolution API

Uso permitido en etapa 1:

- avisar al cliente que el caso fue enviado
- reenviar enlace al panel
- recordar siguientes pasos
- avisar si la entidad no responde en el tiempo esperado

Uso no permitido por defecto en etapa 1:

- presentar escritos juridicos a una entidad solo por existir numero de WhatsApp
- sustituir correo institucional o portal oficial sin validacion previa

## 7. Plantilla base del correo post-radicado

Asunto sugerido:

- `123tutela | Tu tramite fue enviado: {producto}`

Cuerpo minimo:

1. confirmacion de envio o radicacion
2. canal usado
3. numero de radicado o evidencia disponible
4. tiempo estimado de respuesta
5. siguiente paso si no responden o incumplen
6. enlace al panel del cliente

## 8. Siguientes implementaciones

1. usar esta estrategia para poblar `submission_summary` en backend
2. mostrar este resumen en el panel del cliente
3. generar correo post-radicado desde la misma fuente
4. integrar Evolution API solo para notificaciones al cliente
