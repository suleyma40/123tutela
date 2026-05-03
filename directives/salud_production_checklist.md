# Checklist de Salida a Produccion Solo con Salud

Objetivo: cerrar de forma ordenada el lanzamiento de 123tutela en produccion con alcance exclusivo para casos de salud, priorizando tutela en salud y sus pasos naturales de continuidad.

Estado ejecutivo al cierre de hoy:

- El bloque salud ya tiene base operativa real para documento, pago, firma, panel y radicacion inicial.
- El principal cuello de botella ya no es infraestructura base ni Wompi.
- Los bloqueos reales para abrir bien son:
  - pulido juridico final del documento
  - cierre comercial y legal antes del pago
  - procedimientos operativos de soporte y seguimiento
  - QA end to end con casos reales de cliente
- WhatsApp queda pausado como pendiente tecnico no bloqueante para salida inicial de salud.

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
- [x] Confirmar que todo mensaje comercial, wizard, dashboard y checkout mantengan ese mismo alcance sin ambiguedad.
- [x] Confirmar que no existan rutas activas de venta o UX principal para materias no estabilizadas.

## 1. Definicion exacta del MVP de salud

- [x] La secuencia principal ya esta definida en producto y codigo:
  - analisis gratis
  - recomendacion del documento correcto
  - pago
  - generacion del documento
  - radicacion cuando aplique
  - continuidad sugerida
- [x] Confirmar que `salud` sale primero con estos productos y no con otros.
- [x] La regla actual de entrada en salud ya opera con ambos, usando motor de recomendacion:
  - `Derecho de peticion en salud` por defecto
  - `Accion de tutela en salud` cuando hay urgencia o la via previa requerida ya esta cumplida
- [x] Confirmar que impugnacion y desacato se ofrecen solo como continuidad del caso y no como entrada fria sin contexto.
- [x] Confirmar que la promesa comercial de salud no sobrevende resultado judicial ni exito del caso.

Estado confirmado hoy:

- El frontend comunica restriccion de alcance a salud.
- El backend soporta `Derecho de peticion en salud`, `Accion de tutela en salud`, `Impugnacion de tutela en salud` e `Incidente de desacato`.
- La recomendacion operativa actual para salud es:
  - si hay urgencia real o la via previa obligatoria ya esta cubierta, recomendar `Accion de tutela`
  - si no, recomendar `Derecho de peticion a EPS`
- El flujo postpago ya contempla continuidad sugerida del caso.

## 2. Producto y oferta comercial

- [x] Confirmar nombre comercial visible de cada producto de salud.
- [x] Confirmar precios oficiales para salud:
  - solo documento
  - documento + radicacion
- [x] Confirmar que el usuario entiende exactamente que compra en cada opcion.
- [x] Confirmar la promesa exacta de `menos de 5 minutos` para salud:
  - que incluye
  - cuando aplica
  - cuando no aplica
- [x] Cerrar texto legal y comercial previo al pago para salud.
- [x] Cerrar politica de reembolso para productos de salud.
- [x] Confirmar como se presenta la continuidad:
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
- Caso especifico ajustado: si la EPS ya autorizo pero la IPS/prestador no agenda cita, la ruta sugerida prioriza `Derecho de peticion a IPS` y agrega advertencia de solicitar en paralelo a la EPS cambio de prestador.
- Salida comercial del diagnostico en salud estandarizada con bloques claros para usuario final: `🔴 Derecho vulnerado`, `⚠️ Qué tan grave es`, `🎯 Quién es el responsable`, `⚡ Acción que necesitas`, mas cierre de continuidad para conversion.
- `Impugnacion` y `desacato` ya se detectan solo si hay senales de fallo previo.
- `Impugnacion` y `desacato` ya pueden entrar desde el inicio del flujo, pero solo con filtro estricto y exigiendo fallo previo cargado.
- `Impugnacion` y `desacato` ya exigen que la IA lea el fallo previo antes de desbloquear generacion.
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
- [x] Definir las repreguntas dinamicas de salud que realmente mejoran calidad.
- [ ] Definir reglas para detectar contradicciones o vacios criticos.
- [ ] Definir cuando el sistema debe bloquear y pedir mas datos.
- [ ] Definir cuando el sistema debe escalar a revision humana o conservadora.

Estado implementado hoy:

- Backend con validacion por etapa para salud en:
  - `preview`
  - `save`
  - `generate`
- Recoleccion postpago endurecida en `backend/agent_orchestrator.py`:
  - elimina preguntas repetidas y evita pedir datos basicos personales en bloque clinico
  - usa esquema en 3 rondas (problema central, fechas/soportes faltantes, checklist documental final)
  - agrega preguntas especificas por tipo de documento (tutela EPS, tutela IPS, desacato, impugnacion y peticion)
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
  - existe smoke operativo para validar radicacion por las cuatro rutas
  - despues de endurecer la regla de fallo previo en impugnacion y desacato, conviene rerun corto antes de volver a dar este punto por cerrado

## 9. UX y panel del cliente

- [x] Validar que el landing, wizard y dashboard solo empujen salud.
- [x] Validar que el informe gratis de salud explique:
  - problema detectado
  - derecho afectado
  - ruta sugerida
  - datos faltantes
- [x] Validar que antes del pago el usuario vea descripcion clara del producto.
- [x] Validar que despues del pago el usuario vea:
  - estado de pago
  - estado del documento
  - estado de radicacion
  - siguiente paso sugerido
- [x] Validar que impugnacion y desacato aparezcan como continuidad cuando corresponda.
- [x] Validar que la UI se comporte bien si la redireccion vuelve antes que el webhook.

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
  - panel postpago ya muestra estados operativos por etapa:
    - pago (`pendiente`, `confirmado` o estado de orden)
    - documento (`pendiente`, `listo`, `generar ahora`)
    - radicacion (`en proceso`, `comprobante visible`, `manual/auto`)
    - siguiente paso sugerido segun guia y estado del expediente
  - panel ya muestra evidencia visible de firma y artefactos firmados
  - panel ya evita prometer WhatsApp como hecho consumado si ese canal aun no esta confirmado en backend
  - en el paso de analisis gratis (`preview`) ya se muestra:
    - lectura inicial del problema y viabilidad
    - derecho/riesgo comprometido en lenguaje operativo
    - ruta sugerida (peticion o tutela en salud, segun caso)
    - lista de faltantes o preguntas por completar antes de activar documento
- Flujo de resultado de pago reforzado para retorno temprano:
  - `frontend/src/views/PaymentResultView.jsx` intenta conciliacion automatica al cargar (`onReconcilePayment`) usando `transaction_id` y `reference`
  - incluye boton `Verificar pago ahora` para reintento manual de conciliacion
  - muestra estados transaccionales (`approved`, `pending`, `declined`, `error`, `voided`) con copy operativo
  - mantiene mensaje explicito de eventual demora por webhook antes de reflejar estado final en expediente
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

- [x] Crear procedimiento para `pago aprobado no reflejado en UI`.
- [x] Crear procedimiento para `pago rechazado`.
- [x] Crear procedimiento para conciliacion manual por referencia.
- [x] Crear procedimiento para documento bloqueado por QA juridico.
- [x] Crear procedimiento para radicado sin comprobante visible al cliente.
- [x] Definir responsable operativo de soporte.
- [x] Definir SLA interno de respuesta para incidencias de salud.

Evidencia operativa actual:

- SOP pagos y conciliacion: `docs/sop_pagos_y_conciliacion_salud.md`
- SOP QA/radicado/seguimiento: `docs/sop_qa_radicado_y_seguimiento_salud.md`
- Responsable y SLA: `docs/sop_responsables_y_sla_salud.md`

## 11. QA formal antes de abrir trafico

### Casos de prueba minimos

- [x] Caso de salud urgente con tutela claramente viable.
- [x] Caso de salud que debe ir primero por derecho de peticion.
- [x] Caso de salud con informacion insuficiente que debe bloquearse.
- [x] Caso de impugnacion dentro de termino.
- [x] Caso de desacato con fallo previo identificable.
- [x] Caso improcedente o debil que no debe venderse como tutela fuerte.

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
- Corrida tecnica ejecutada hoy (evidencia):
  - `python -B execution/health_case_regression.py`
    - resultado: `10 caso(s) validados correctamente`
  - `python -B execution/health_flow_smoke.py`
    - resultado: `5 flujo(s) reales validados correctamente`
  - `python -B execution/health_submission_smoke.py`
    - resultado: `1 politica(s) de radicacion validadas correctamente`

### Validaciones end to end

- [x] Crear caso nuevo.
- [x] Completar intake guiado.
- [x] Obtener DX y recomendacion razonable.
- [x] Pagar con Wompi.
- [x] Validar habilitacion del documento final.
- [x] Validar score juridico y bloqueo si no alcanza.
- [x] Validar radicacion o evidencia de no-radicacion segun producto.
- [x] Validar panel y correo postevento.
- [x] Validar continuidad sugerida.

Evidencia tecnica de corrida E2E local:

- `execution/health_flow_smoke.py` valida flujo real de:
  - `create_case`
  - `update_case_intake`
  - `generate_document`
  - bloqueos esperados cuando faltan minimos juridicos
- `execution/health_submission_smoke.py` valida envio/radicacion en modo `auto` con politica de submission en salud.
- `execution/health_case_regression.py` valida recomendacion y bloqueos sobre 10 escenarios de salud (peticion, tutela, impugnacion, desacato y casos debiles).

Pendientes que requieren entorno real externo:

- confirmar estabilidad de multiples pagos reales con distintos medios Wompi
- confirmacion formal de `continuidad sugerida` con casos reales o anonimizados de cliente

Evidencia adicional de correo postevento (corrida real):

- Fecha de corrida: `2026-05-01`
- Comando:
  - `python -m execution.email_delivery_smoke --recipient su-ley23@hotmail.com`
  - `python -m execution.email_delivery_smoke --recipient m22perezia@gmail.com`
- Resultado:
  - `post_radicado_email.status = sent` desde `notificaciones@123tutelaapp.com`
  - `signed_submission_email.status = sent` desde `radicaciones@123tutelaapp.com`

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

- [x] El frontend publico y el dashboard mantienen foco exclusivo en salud.
- [ ] El motor recomienda correctamente entre peticion, tutela, impugnacion y desacato en salud.
- [ ] El intake de salud pide informacion suficiente para no generar documentos debiles.
- [ ] La tutela en salud bloquea casos improcedentes o incompletos.
- [ ] Las fuentes y citas usadas son verificables.
- [ ] El documento final pasa un QA juridico minimo antes de entrega.
- [ ] El pago productivo funciona con trazabilidad completa.
- [ ] La radicacion de salud tiene canal y evidencia definidos.
- [x] El usuario recibe estado claro en panel y correo.
- [x] Existe procedimiento operativo para incidencias de pago, QA y radicacion.
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
- [x] Politica de reembolso.
- [x] Texto legal final antes de pago.
- [ ] Regla operativa de radicacion y comprobante.
- [ ] Casos de prueba reales o anonimizados para salud.

## 16. Corte real de avance

### Hecho o muy avanzado

- [x] Foco del producto restringido a salud en frontend y flujo principal.
- [x] Documentos base de salud ya operativos:
  - derecho de peticion
  - tutela
  - impugnacion
  - desacato
- [x] Recomendacion base entre peticion, tutela, impugnacion y desacato ya implementada.
- [x] Intake guiado de salud ya funciona con etapas y repreguntas utiles.
- [x] Deteccion de contradicciones y casos borde ya existe en backend y wizard.
- [x] Smoke tests funcionales y de flujo real ya existen para salud.
- [x] Pago productivo base y habilitacion del documento ya funcionan.
- [x] Firma electronica simple trazable ya quedo integrada.
- [x] Radicacion operativa base ya existe para los productos de salud habilitados.
- [x] Correo operativo ya funciona con remitentes separados por tipo de envio.
- [x] Panel del cliente ya muestra documento, radicado y novedades basicas.

### Falta por cerrar antes de abrir bien

- [ ] Pulido juridico fino de la tutela y de los documentos de continuidad.
- [x] Copy final de compra y explicacion exacta del producto.
- [x] Texto legal final antes del pago.
- [x] Politica de reembolso.
- [x] Seguimiento del caso mejor presentado para cliente final.
- [ ] Trazabilidad completa y auditada de pagos, webhook y errores operativos.
- [ ] SOPs de soporte para incidencias de pago, documento, radicado y seguimiento.
  - ya existe primer SOP de pagos y conciliacion en `docs/sop_pagos_y_conciliacion_salud.md`
  - ya existe primer SOP de QA, radicado y seguimiento en `docs/sop_qa_radicado_y_seguimiento_salud.md`
- [ ] QA end to end con casos reales o anonimizados de cliente.
  - ya existe paquete base de QA corto en `docs/casos_qa_lanzamiento_salud.md`

### Bloqueantes reales de salida

- [ ] Documento final de tutela en salud todavia requiere una ultima ronda fuerte de pulido juridico y de redaccion.
- [x] Paquete comercial y legal base ya quedo cerrado para UI y vistas legales.
- [ ] Falta definir operacion de seguimiento y soporte desde panel con claridad para cliente.
- [ ] Falta corrida formal de QA de punta a punta sobre casos reales.

### Pendientes no bloqueantes inmediatos

- [ ] Integracion de WhatsApp.
- [ ] Automatizaciones adicionales sobre n8n o Evolution.
- [ ] Apertura a nuevas materias distintas de salud.

Actualizacion tecnica reciente (alcance salud reforzado):

- Backend ya bloquea categorias distintas de salud en endpoints clave:
  - `/public/leads/diagnosis`
  - `/analysis/preview`
  - `/cases` (creacion de caso)
  - `/public/cases/{case_id}/intake`
- Frontend del wizard ya no expone selector multicategoria en la ruta principal de alta.
- El payload del wizard hacia preview ya fuerza `category = Salud`.

Inicio de ejecucion de bloqueantes (2026-05-02):

- Plan de ejecucion activo: `docs/plan_ejecucion_bloqueantes_lanzamiento_2026_05_02.md`
- Acta QA juridica: `docs/acta_qa_juridica_salud_2026_05_02.md`
- Acta trazabilidad pagos Wompi: `docs/acta_trazabilidad_pagos_wompi_2026_05_02.md`
- Acta radicacion/evidencia: `docs/acta_radicacion_evidencia_operativa_2026_05_02.md`
- Acta QA E2E: `docs/acta_qa_e2e_salud_2026_05_02.md`
- Bitacora go-live semana 1: `docs/bitacora_go_live_salud_semana_1.md`
- Postpago (`/pago/resultado`) refinado en frontend:
  - estado del expediente ya no muestra `enviado al equipo juridico` de forma prematura
  - progreso del formulario ahora pondera campos obligatorios reales, preguntas dinamicas y soportes
  - codigo de rifa/expediente ya se puede descargar en archivo `.txt`
  - bloque de preguntas ahora prioriza preguntas clave por tipo de caso y elimina repeticiones
- Acceso de testeo publico reforzado:
  - `/testeo` redirige a `/diagnostico?test_code=TEST123`
  - la landing y la navegacion muestran link visible de testeo
  - `/dashboard` y rutas no registradas ya no quedan en blanco; redirigen a inicio
  - el frontend preserva codigos de test `TEST123`, `TESTMAYO` y `QA2026` durante build y checkout

### Estimacion ejecutiva

- Avance general del bloque salud:
  - aproximadamente `65% a 70%` cerrado
- Falta para salida controlada razonable:
  - aproximadamente `30% a 35%`
- Falta para una salida amplia y robusta:
  - mas que una sola mejora tecnica; requiere cierre juridico, operacional y comercial conjunto
