# Checklist de Salida a Produccion Solo con Salud

Objetivo: cerrar de forma ordenada el lanzamiento de 123tutela en produccion con alcance exclusivo para casos de salud, priorizando tutela en salud y sus pasos naturales de continuidad.

Regla de alcance:

- Esta checklist cubre solo el bloque `salud`.
- No se abre trafico amplio para otras materias hasta cerrar esta lista.
- El alcance inicial de documentos es:
  - `Derecho de peticion en salud`
  - `Accion de tutela en salud`
  - `Impugnacion de tutela en salud`
  - `Incidente de desacato en salud`

## 0. Criterio de enfoque

- [x] El frontend ya comunica que por ahora solo se atienden casos de salud.
- [x] El backend ya tiene documentos operativos del bloque salud.
- [x] El flujo postpago ya bloquea la generacion final hasta pago aprobado.
- [ ] Confirmar que todo mensaje comercial, wizard, dashboard y checkout mantengan ese mismo alcance sin ambiguedad.
- [ ] Confirmar que no existan rutas activas de venta o UX principal para materias no estabilizadas.

## 1. Definicion exacta del MVP de salud

- [x] La secuencia principal ya esta definida en producto y codigo:
  - analisis gratis
  - recomendacion del documento correcto
  - pago
  - generacion del documento
  - radicacion cuando aplique
  - continuidad sugerida
- [ ] Confirmar que `salud` sale primero con estos productos y no con otros.
- [x] La regla actual de entrada en salud ya opera con ambos, usando motor de recomendacion:
  - `Derecho de peticion en salud` por defecto
  - `Accion de tutela en salud` cuando hay urgencia o la via previa requerida ya esta cumplida
- [ ] Confirmar que impugnacion y desacato se ofrecen solo como continuidad del caso y no como entrada fria sin contexto.
- [ ] Confirmar que la promesa comercial de salud no sobrevende resultado judicial ni exito del caso.

Estado confirmado hoy:

- El frontend comunica restriccion de alcance a salud.
- El backend soporta `Derecho de peticion en salud`, `Accion de tutela en salud`, `Impugnacion de tutela en salud` e `Incidente de desacato`.
- La recomendacion operativa actual para salud es:
  - si hay urgencia real o la via previa obligatoria ya esta cubierta, recomendar `Accion de tutela`
  - si no, recomendar `Derecho de peticion a EPS`
- El flujo postpago ya contempla continuidad sugerida del caso.

## 2. Producto y oferta comercial

- [ ] Confirmar nombre comercial visible de cada producto de salud.
- [ ] Confirmar precios oficiales para salud:
  - solo documento
  - documento + radicacion
- [ ] Confirmar que el usuario entiende exactamente que compra en cada opcion.
- [ ] Confirmar la promesa exacta de `menos de 5 minutos` para salud:
  - que incluye
  - cuando aplica
  - cuando no aplica
- [ ] Cerrar texto legal y comercial previo al pago para salud.
- [ ] Cerrar politica de reembolso para productos de salud.
- [ ] Confirmar como se presenta la continuidad:
  - impugnacion
  - desacato
  - seguimiento

## 3. Flujo juridico del bloque salud

### Reglas de recomendacion

- [ ] Definir cuando recomendar `Derecho de peticion en salud`.
- [ ] Definir cuando recomendar `Accion de tutela en salud`.
- [ ] Definir cuando no recomendar tutela para evitar casos debiles o improcedentes.
- [ ] Definir cuando la via previa debe exigirse y cuando la urgencia permite no frenarla.
- [ ] Definir cuando ofrecer `Impugnacion de tutela`.
- [ ] Definir cuando ofrecer `Incidente de desacato`.

Estado implementado hoy en backend:

- Primera capa endurecida de recomendacion en `backend/workflows.py`.
- `Impugnacion` y `desacato` ya se detectan solo si hay senales de fallo previo.
- `Tutela` en salud ya no depende solo de palabras urgentes; ahora exige mejor combinacion de:
  - nucleo medico minimo
  - barrera de EPS o IPS
  - urgencia actual o especial proteccion
  - gestion previa cuando aplica
- Lo pendiente ya no es crear la regla desde cero, sino cerrarla con QA y criterios juridicos finales.

### Procedencia minima de tutela en salud

- [ ] Legitimacion por activa clara.
- [ ] Entidad accionada clara: EPS, IPS, clinica, hospital o autoridad.
- [ ] Diagnostico o condicion medica clara.
- [ ] Servicio, medicamento, procedimiento, insumo o cita claramente identificado.
- [ ] Barrera concreta: negativa, demora, suspension, silencio o falta de autorizacion.
- [ ] Riesgo actual: salud, dolor, agravacion, continuidad, vida digna o perjuicio irremediable.
- [ ] Inmediatez suficientemente explicada.
- [ ] Subsidiariedad evaluada sin bloquear urgencias reales.
- [ ] No temeridad o aclaracion de tutela previa.
- [ ] Soporte medico minimo disponible o razonablemente descrito.

### Estructura minima exigible del documento

- [ ] Hechos cronologicos claros.
- [ ] Derechos vulnerados correctamente conectados.
- [ ] Fundamento juridico verificable y no ornamental.
- [ ] Pretensiones medicas concretas y ejecutables.
- [ ] Pruebas y anexos claramente referidos.
- [ ] Competencia o destinatario correcto.
- [ ] Firma, identificacion y calidad del accionante.

## 4. Intake guiado de salud

- [ ] Confirmar el intake minimo obligatorio para salud:
  - EPS
  - IPS o prestador si aplica
  - diagnostico
  - tratamiento o servicio requerido
  - fecha de negativa, demora o barrera
  - urgencia o riesgo actual
  - gestion previa
  - soportes disponibles
- [ ] Confirmar cuales campos son obligatorios para preview.
- [ ] Confirmar cuales campos son obligatorios para guardar expediente.
- [ ] Confirmar cuales campos son obligatorios para generar documento final.
- [ ] Definir las repreguntas dinamicas de salud que realmente mejoran calidad.
- [ ] Definir reglas para detectar contradicciones o vacios criticos.
- [ ] Definir cuando el sistema debe bloquear y pedir mas datos.
- [ ] Definir cuando el sistema debe escalar a revision humana o conservadora.

Estado implementado hoy:

- Backend con validacion por etapa para salud en:
  - `preview`
  - `save`
  - `generate`
- El wizard inicial de salud ya usa una entrevista guiada por el agente desde el arranque, no solo despues del pago.
- Las preguntas iniciales del agente ya siguen mejor el orden juridicamente util:
  - entidad de salud
  - diagnostico
  - servicio requerido
  - urgencia actual
  - soporte medico
  - barrera de la EPS
- Frontend del wizard ya no bloquea el preview de salud por campos que pertenecen a etapas posteriores como:
  - fecha exacta
  - canal de respuesta
  - soporte obligatorio desde el primer paso
- Backend ya detecta contradicciones importantes del bloque salud, por ejemplo:
  - EPS distinta entre `target_entity` y `eps_name`
  - marcar `sin gestion previa` pero describir radicado o respuesta de EPS
  - actuar en nombre propio con datos de representado o al reves
  - marcar `No aplica` en proteccion especial pero describir una condicion reforzada
  - mezclar `caso ya resuelto` con urgencia actual sin aclaracion
- El wizard inicial de salud ya prioriza preguntas correctivas cuando detecta esas inconsistencias, en vez de seguir solo un orden lineal.
- Backend ya endurece varios casos borde de salud:
  - continuidad de tratamiento interrumpida
  - menor de edad
  - embarazo o gestacion
  - discapacidad o condicion reforzada
  - urgencia real aunque la PQRS no este completamente cerrada
- El agente ya repregunta especificamente por continuidad del tratamiento y por proteccion especial cuando eso cambia la procedencia.
- El wizard inicial de salud ya refleja esos casos borde en microcopy y preguntas:
  - continuidad del tratamiento
  - menor de edad
  - embarazo de riesgo
  - discapacidad
  - dolor o empeoramiento actual
- El pendiente principal ya no es separar etapas, sino afinar repreguntas y cubrir contradicciones o casos borde.

Matriz operativa inicial por etapa:

- Preview o DX preliminar:
  - entidad de salud identificable
  - diagnostico o condicion medica
  - servicio, medicamento o procedimiento requerido
  - relato minimo del problema
  - urgencia o afectacion actual inicial
- Guardado de expediente:
  - cronologia minima
  - entidad accionada clara
  - diagnostico
  - tratamiento o servicio requerido
  - urgencia o riesgo actual
  - pretension concreta
  - soporte o descripcion minima de soportes
- Generacion de `Derecho de peticion en salud`:
  - entidad o destinatario claro
  - solicitudes concretas
  - hechos suficientes
  - canal de respuesta
- Generacion de `Accion de tutela en salud`:
  - entidad accionada clara
  - diagnostico
  - servicio o tratamiento requerido
  - dano o riesgo actual
  - gestion previa o justificacion de urgencia
  - inmediatez
  - no temeridad o aclaracion de tutela previa
  - soporte medico minimo
- Generacion de `Impugnacion de tutela`:
  - juzgado o despacho
  - fecha o decision impugnada
  - resultado del fallo
  - motivo concreto de impugnacion
- Generacion de `Incidente de desacato`:
  - juzgado que emitio el fallo
  - fecha o identificacion del fallo
  - orden incumplida
  - hechos concretos del incumplimiento

## 5. Fuentes juridicas y politica de citas

- [ ] Confirmar set minimo de fuentes oficiales para salud:
  - Constitucion art. 86
  - Ley 1751 de 2015
  - Decreto 2591 de 1991
  - lineamientos oficiales de salud segun el caso
- [ ] Confirmar que toda cita usada en salud sea verificable.
- [ ] Prohibir citas jurisprudenciales no verificadas o decorativas.
- [ ] Definir cuando una sentencia si aporta y cuando no hace falta citarla.
- [ ] Confirmar persistencia de fuentes usadas en expediente o metadata del documento.

## 6. Generacion y QA juridico

- [ ] Cerrar plantilla base de `Derecho de peticion en salud`.
- [ ] Cerrar plantilla base de `Accion de tutela en salud`.
- [ ] Cerrar plantilla base de `Impugnacion de tutela en salud`.
- [ ] Cerrar plantilla base de `Incidente de desacato en salud`.
- [ ] Revisar que cada plantilla tenga grosor argumentativo suficiente.
- [ ] Revisar que las pretensiones sean medibles y ejecutables.
- [ ] Revisar que no haya lenguaje inflado ni promesas impropias.
- [ ] Definir score minimo de QA para documentos de salud.
- [ ] Definir que hallazgos bloquean entrega automatica.
- [ ] Definir que hallazgos solo generan warning.
- [ ] Validar que el documento final sea util para presentar, no solo que suene juridico.

Estado implementado hoy:

- Ya existe regresion funcional de flujo real en `execution/health_flow_smoke.py`.
- El smoke test ya valida sobre `backend/app_v2.py` el ciclo:
  - `create_case`
  - `update_case_intake`
  - `generate_document`
- El smoke test usa repositorio en memoria para aislar reglas y generacion sin depender de la base remota.
- Casos cubiertos hoy en flujo real:
  - `Accion de tutela en salud` por continuidad de tratamiento de menor
  - `Derecho de peticion en salud` por demora ordinaria de EPS
  - `Impugnacion de tutela en salud` por error de valoracion del fallo
  - `Incidente de desacato en salud` por incumplimiento de orden judicial
  - `Bloqueo esperado en generate_document` cuando una tutela llega sin cierre juridico minimo
- Comando operativo:
  - `python -B execution/health_flow_smoke.py`
- Resultado actual:
  - `5 flujo(s) reales validados correctamente`
- QA juridico del writer ya mejorado para salud en `backend/document_writer.py`:
  - se eliminaron frases internas impropias del sistema en los documentos finales
  - `Derecho de peticion en salud` ya respeta mejor las solicitudes numeradas del caso
  - `Impugnacion de tutela` ya identifica mejor fallo, decision controvertida, motivo y soportes
  - `Incidente de desacato` ya identifica mejor la orden incumplida, el incumplimiento actual y los anexos relevantes
  - se redujo el tono excesivo de tutela en documentos no judiciales o de continuidad
  - se limito el apoyo jurisprudencial del derecho de peticion a una referencia complementaria mas sobria

## 7. Pago y habilitacion del documento

- [x] Wompi productivo ya esta integrado.
- [x] El webhook ya confirma el pago.
- [x] El documento final ya depende de pago aprobado.
- [ ] Verificar trazabilidad completa en base de datos:
  - pago creado
  - referencia
  - transaccion
  - estado final
  - timestamps
  - payload auditado
- [ ] Crear indice por `transaction_id` si sigue pendiente.
- [ ] Registrar y revisar logs de errores de firma o webhook.
- [ ] Confirmar que los productos de salud mapean correctamente a pago y postpago.
- [ ] Probar reintentos de webhook sin duplicar efectos en casos de salud.

## 8. Radicacion de salud

- [ ] Definir que documentos de salud admiten radicacion operativa real en esta fase.
- [ ] Definir si la radicacion inicial sera:
  - automatica
  - asistida
  - manual con soporte interno
- [ ] Confirmar canal principal de radicacion por tipo de documento.
- [ ] Confirmar evidencia minima que se guarda de cada envio.
- [ ] Confirmar evidencia minima que recibe el cliente:
  - correo
  - panel
  - ambos
- [ ] Definir fallback cuando no exista canal digital confiable.
- [ ] Cerrar trazabilidad completa de radicado, comprobante y continuidad.

Estado implementado hoy:

- La politica operativa ya quedo bajada a codigo en `backend/workflows.py` y `backend/app_v2.py`.
- En salud, los cuatro documentos del bloque ya admiten `auto` cuando existe canal confiable:
  - `Derecho de peticion en salud`
  - `Accion de tutela en salud`
  - `Impugnacion de tutela en salud`
  - `Incidente de desacato`
- Para documentos judiciales, el `routing` ya prioriza canales de juzgado o reparto judicial:
  - correo judicial principal
  - correo nacional o institucional de reparto
  - correos judiciales de respaldo cuando existan en base
- Si no existe canal judicial o institucional confiable, el sistema conserva fallback a:
  - `manual_contact`
  - `presencial`
- La politica de radicacion ya queda persistida en `submission_summary` del caso.
- Smoke test operativo agregado en `execution/health_submission_smoke.py`.
- Comando de validacion:
  - `python -B execution/health_submission_smoke.py`
- Resultado actual:
  - `4 politica(s) de radicacion validadas correctamente`

## 9. UX y panel del cliente

- [ ] Validar que el landing, wizard y dashboard solo empujen salud.
- [ ] Validar que el informe gratis de salud explique:
  - problema detectado
  - derecho afectado
  - ruta sugerida
  - datos faltantes
- [ ] Validar que antes del pago el usuario vea descripcion clara del producto.
- [ ] Validar que despues del pago el usuario vea:
  - estado de pago
  - estado del documento
  - estado de radicacion
  - siguiente paso sugerido
- [ ] Validar que impugnacion y desacato aparezcan como continuidad cuando corresponda.
- [ ] Validar que la UI se comporte bien si la redireccion vuelve antes que el webhook.

Estado implementado hoy:

- La firma para radicacion ya quedo encaminada como `firma electronica simple`, no como firma digital certificada.
- Backend reforzado en `backend/app_v2.py`:
  - exige aceptacion expresa y revision previa del documento
  - guarda `accepted_at`
  - guarda `consent_version`
  - guarda `consent_text`
  - guarda metodo declarado `firma_electronica_simple`
  - guarda trazabilidad tecnica basica disponible desde request:
    - `ip_address`
    - `user_agent`
- Artefactos firmados reforzados en `backend/submission_artifacts.py`:
  - DOCX y PDF ya incluyen bloque de firma electronica simple
  - incluyen consentimiento y version
  - incluyen fecha/hora de aceptacion
- Frontend reforzado en `frontend/src/views/DashboardV2.jsx`:
  - copy explicito de consentimiento
  - ciudad y fecha mejor hidratadas
  - payload alineado con `consent_version = ses_v1`
  - panel post-radicacion ya diferencia:
    - firma registrada
    - envio ejecutado
    - radicado confirmado o pendiente
  - panel ya muestra evidencia visible de firma y artefactos firmados
  - panel ya evita prometer WhatsApp como hecho consumado si ese canal aun no esta confirmado en backend
- La decision operativa actual es:
  - usar firma electronica simple trazable para salud
  - no exigir firma digital certificada en esta fase
- Texto de consentimiento operativo ya cerrado en version `ses_v1`:
  - autoriza a 123tutela a usar firma electronica simple para radicacion o envio
  - confirma revision previa del documento
  - confirma exactitud basica de datos de identificacion y ciudad
  - reconoce conservacion de evidencia basica de aceptacion y metadatos tecnicos
- Regla operativa de copia y radicado ya aclarada:
  - 123tutela envia o deja disponible copia del documento al cliente por panel y correo cuando el canal este habilitado
  - WhatsApp queda como canal deseado pero no debe mostrarse como confirmado mientras siga pendiente la integracion operativa
  - en tramites judiciales automaticos, el radicado o acuse puede llegar primero al correo de radicaciones usado para el envio
  - segun el despacho, ese mismo radicado tambien puede llegar al correo del cliente si fue incluido en el escrito o en el envio
- Buzones operativos ya definidos:
  - `radicaciones@123tutelaapp.com` para envios judiciales y recepcion inicial de acuses o radicados
  - `notificaciones@123tutelaapp.com` para copias al cliente y avisos operativos del expediente
  - `soporte@123tutelaapp.com` para incidencias, conciliacion y seguimiento manual
- Gestor de correo ya definido para esta fase:
  - los buzones y el dominio siguen gestionados en `Hostinger`
  - `Resend` se usa como SMTP saliente real del producto y para mejorar entregabilidad
  - toda radicacion por correo debe salir desde `radicaciones@123tutelaapp.com`
  - las copias y avisos al cliente pueden salir desde `notificaciones@123tutelaapp.com`
- Smoke test operativo de correo disponible:
  - `python -B execution/email_delivery_smoke.py --recipient TU_CORREO`
  - envia una copia al cliente y una radicacion simulada para validar remitente, cuerpo visible y `reply-to`
  - hallazgo confirmado: Hostinger SMTP rechazaba el remitente `radicaciones@123tutelaapp.com` cuando la autenticacion salia desde otro buzon
  - hallazgo confirmado: con `Resend SMTP` ya se pudo enviar una copia desde `notificaciones@123tutelaapp.com` y una radicacion simulada desde `radicaciones@123tutelaapp.com`

## 10. Operacion y soporte

- [ ] Crear procedimiento para `pago aprobado no reflejado en UI`.
- [ ] Crear procedimiento para `pago rechazado`.
- [ ] Crear procedimiento para conciliacion manual por referencia.
- [ ] Crear procedimiento para documento bloqueado por QA juridico.
- [ ] Crear procedimiento para radicado sin comprobante visible al cliente.
- [ ] Definir responsable operativo de soporte.
- [ ] Definir SLA interno de respuesta para incidencias de salud.

## 11. QA formal antes de abrir trafico

### Casos de prueba minimos

- [ ] Caso de salud urgente con tutela claramente viable.
- [ ] Caso de salud que debe ir primero por derecho de peticion.
- [ ] Caso de salud con informacion insuficiente que debe bloquearse.
- [ ] Caso de impugnacion dentro de termino.
- [ ] Caso de desacato con fallo previo identificable.
- [ ] Caso improcedente o debil que no debe venderse como tutela fuerte.

Estado implementado hoy:

- Runner de regresion inicial en `execution/health_case_regression.py`.
- Comando de ejecucion local:
  - `python -B execution/health_case_regression.py`
- Casos simulados ya cubiertos y pasando:
  - continuidad de tratamiento
  - embarazo de alto riesgo sin PQRS completamente cerrada
  - derecho de peticion en salud ordinario
  - desacato en salud con fallo previo
  - impugnacion de tutela en salud
  - discapacidad con barrera de EPS
  - contradiccion fuerte de EPS y gestion previa
  - hecho superado o barrera ya superada
  - tutela previa con riesgo de temeridad
  - caso debil o incompleto que debe bloquearse

### Validaciones end to end

- [ ] Crear caso nuevo.
- [ ] Completar intake guiado.
- [ ] Obtener DX y recomendacion razonable.
- [ ] Pagar con Wompi.
- [ ] Validar habilitacion del documento final.
- [ ] Validar score juridico y bloqueo si no alcanza.
- [ ] Validar radicacion o evidencia de no-radicacion segun producto.
- [ ] Validar panel y correo postevento.
- [ ] Validar continuidad sugerida.

## 12. Apertura controlada

- [ ] Abrir primero trafico controlado solo para salud.
- [ ] Medir porcentaje de casos:
  - que llegan con datos suficientes
  - que bloquea el sistema
  - que convierten a pago
  - que requieren soporte manual
- [ ] Revisar semanalmente errores recurrentes de intake, QA, pago y radicacion.
- [ ] Convertir cada bug repetido en validacion, regla o mejora del flujo.
- [ ] No abrir nuevas materias hasta estabilizar salud con evidencia.

## 13. Criterio de salida a produccion solo con salud

Solo se considera lista la salida de salud cuando se cumpla todo esto:

- [ ] El frontend publico y el dashboard mantienen foco exclusivo en salud.
- [ ] El motor recomienda correctamente entre peticion, tutela, impugnacion y desacato en salud.
- [ ] El intake de salud pide informacion suficiente para no generar documentos debiles.
- [ ] La tutela en salud bloquea casos improcedentes o incompletos.
- [ ] Las fuentes y citas usadas son verificables.
- [ ] El documento final pasa un QA juridico minimo antes de entrega.
- [ ] El pago productivo funciona con trazabilidad completa.
- [ ] La radicacion de salud tiene canal y evidencia definidos.
- [ ] El usuario recibe estado claro en panel y correo.
- [ ] Existe procedimiento operativo para incidencias de pago, QA y radicacion.
- [ ] Existen casos de prueba satisfactorios de punta a punta.

## 14. Orden recomendado de ejecucion

1. Cerrar definicion exacta del MVP de salud.
2. Cerrar reglas juridicas de recomendacion y procedencia.
3. Cerrar intake guiado y bloqueos por faltantes.
4. Cerrar plantillas, citas y QA juridico.
5. Cerrar radicacion y evidencia operativa.
6. Completar trazabilidad de pago y soporte.
7. Ejecutar QA formal end to end.
8. Abrir trafico controlado solo para salud.

## 15. Lo que necesitamos ya

- [ ] Endurecer y cerrar la regla final de recomendacion entre peticion y tutela en salud.
- [ ] Intake definitivo de salud con campos obligatorios por etapa.
- [ ] Politica de reembolso.
- [ ] Texto legal final antes de pago.
- [ ] Regla operativa de radicacion y comprobante.
- [ ] Casos de prueba reales o anonimizados para salud.
