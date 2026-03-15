# Checklist de Integracion Wompi y Salida a Produccion

Objetivo: reemplazar el pago demo actual por un flujo real con Wompi, validado por webhook, y dejar la app lista para operar en produccion.

## 0. Decisiones de producto ya confirmadas

- [x] Fase inicial con cobros individuales, no suscripciones.
- [x] El analisis inicial del caso y la identificacion del derecho vulnerado son gratis.
- [x] El usuario recibe un informe gratis antes de pagar.
- [x] El usuario elige despues si paga solo el documento o documento + radicacion.
- [x] El documento completo se genera solo despues del pago confirmado.
- [x] Si el usuario paga radicacion, se ejecuta la radicacion y se le envia comprobante al correo.
- [x] En el correo de radicado y en el panel se debe informar la continuidad posible del caso: seguimiento, impugnacion, desacato u otros pasos.
- [x] El usuario tiene panel propio para ver historial, documentos, pagos, radicaciones y siguientes pasos.
- [x] La continuidad del caso puede generar nuevos cobros por evento cuando aplique.
- [x] En esta etapa los combos quedan fuera.
- [x] No se ofrece `Guia de radicacion` como producto separado.
- [x] No se ofrece `Documento urgente` como producto separado.
- [x] La promesa comercial es: analizar el caso, generar el documento y radicarlo en menos de 5 minutos cuando el usuario compre esa opcion.
- [x] Cada producto debe mostrar una descripcion clara de que incluye y que esta pagando el cliente.
- [x] La base operativa incluye correos de juzgados en Colombia para soportar la radicacion donde aplique.
- [ ] Falta cerrar las reglas exactas para cuando un paso posterior se recomienda automaticamente y cuanto cuesta en cada escenario.

## 1. Definiciones de negocio

- [x] Confirmar el precio oficial en COP.
- [ ] Confirmar el nombre del producto que compra el usuario.
- [x] Confirmar si el pago cubre solo generacion del documento o tambien envio/radicacion.
- [ ] Confirmar politica de reembolso.
- [ ] Confirmar texto legal visible antes de pagar.
- [x] Definir la descripcion comercial corta de cada producto.
- [x] Definir la descripcion detallada de cada producto.
- [ ] Definir exactamente que significa la promesa `menos de 5 minutos` en cada flujo.

## 2. Accesos y credenciales

- [x] Crear o validar cuenta Wompi.
- [x] Completar vinculacion para cobros en produccion.
- [ ] Obtener credenciales sandbox.
- [x] Obtener credenciales produccion.
- [x] Guardar secretos solo en `.env` o en variables seguras de Dokploy.

Credenciales requeridas:

- [ ] `WOMPI_PUBLIC_KEY_SANDBOX`
- [ ] `WOMPI_PUBLIC_KEY_PRODUCTION`
- [ ] `WOMPI_INTEGRITY_SECRET_SANDBOX`
- [ ] `WOMPI_INTEGRITY_SECRET_PRODUCTION`
- [ ] `WOMPI_EVENT_SECRET_SANDBOX`
- [ ] `WOMPI_EVENT_SECRET_PRODUCTION`
- [ ] `WOMPI_PRIVATE_KEY_SANDBOX` opcional para futuras operaciones administrativas
- [ ] `WOMPI_PRIVATE_KEY_PRODUCTION` opcional para futuras operaciones administrativas

## 3. URLs y configuracion externa

- [x] Confirmar URL publica frontend: `https://123tutelaapp.com`
- [x] Confirmar URL publica backend: `https://api.123tutelaapp.com`
- [x] Definir URL de resultado de pago: `https://123tutelaapp.com/pago/resultado`
- [x] Definir webhook sandbox: `https://api.123tutelaapp.com/payments/wompi/webhook/sandbox`
- [x] Definir webhook produccion: `https://api.123tutelaapp.com/payments/wompi/webhook`
- [x] Configurar URL de eventos sandbox en Wompi.
- [x] Configurar URL de eventos produccion en Wompi.

## 4. Decisiones de implementacion

- [x] Confirmar que arrancamos con Wompi Widget o Web Checkout.
- [x] Usar validacion final por webhook, no por redireccion.
- [x] Mantener el frontend sin secretos de Wompi.
- [x] Generar referencias de pago unicas por intento.
- [x] Definir estados internos de pago: `pending`, `approved`, `declined`, `error`, `voided`.
- [x] Implementar desde el inicio todo el catalogo de productos individuales.
- [x] Dejar los combos para una fase posterior, cuando las reglas de encadenamiento esten cerradas.

Decision recomendada para este MVP:

- [x] Fase 1: Widget o Checkout + webhook para todos los productos individuales.
- [ ] Fase 2: evaluar API avanzada solo si luego hace falta tokenizacion, devoluciones o cargos mas complejos.
- [ ] Fase 2: agregar combos cuando el motor de continuidad comercial este completamente definido.

## 5. Base de datos

- [x] Crear tabla `payments` o `payment_orders`.
- [x] Relacionar cada pago con `case_id` y `user_id`.
- [x] Guardar `reference`, `amount_in_cents`, `currency`, `status`, `transaction_id`, `provider`, `environment`.
- [x] Guardar payload crudo del webhook para auditoria.
- [x] Guardar timestamps de creacion, aprobacion y ultimo cambio de estado.
- [x] Crear indice por `reference`.
- [ ] Crear indice por `transaction_id`.

## 6. Backend

- [x] Crear modulo Wompi en backend.
- [x] Crear endpoint para iniciar pago y entregar configuracion segura al frontend.
- [x] Crear generacion de firma de integridad.
- [x] Crear endpoint webhook de Wompi.
- [x] Validar firma del evento entrante.
- [x] Hacer idempotente el webhook para no procesar dos veces el mismo evento.
- [x] Marcar el expediente como pagado solo con evento `approved`.
- [x] Registrar errores y rechazos de pago.
- [x] Deshabilitar el flujo `pago demo`.

Rutas sugeridas:

- [x] `POST /payments/wompi/checkout-session`
- [x] `POST /payments/wompi/webhook`
- [x] `POST /payments/wompi/webhook/sandbox`
- [x] `GET /payments/{reference}`

## 7. Frontend

- [x] Reemplazar boton `Confirmar pago demo`.
- [x] Mostrar boton real de pago Wompi en el paso correcto.
- [x] Mostrar estado visual: pendiente, pagado, rechazado, en revision.
- [x] Crear pantalla `pago/resultado`.
- [x] Mostrar mensaje claro si la redireccion vuelve antes de que llegue el webhook.
- [x] Bloquear generacion de documento final hasta que el backend confirme pago aprobado.
- [x] Mostrar referencia de pago al usuario.
- [x] Mostrar informe gratis con derecho vulnerado, analisis y recomendacion antes del pago.
- [x] Permitir elegir entre `Solo documento` y `Documento + radicacion` cuando el producto lo soporte.
- [x] Mostrar siguientes pasos sugeridos segun el tipo de caso.
- [x] Mostrar ofertas de continuidad: seguimiento, impugnacion, desacato y otros pasos posteriores.
- [ ] Mostrar esos pasos tanto en panel como en correo.
- [x] Mostrar tiempos estimados, siguiente accion esperada y posibles escenarios del tramite.
- [x] Mostrar descripcion clara del producto antes del pago.
- [x] Mostrar que la plataforma cuenta con base de correos de juzgados y entidades para radicacion donde aplique.
- [x] No mostrar `Guia de radicacion` ni `Documento urgente` en la oferta inicial.

## 8. UX y legal

- [x] Crear pagina publica de Terminos.
- [x] Crear pagina publica de Privacidad.
- [x] Crear pagina publica de Contacto o Soporte.
- [x] Mostrar que el cobro se procesa con Wompi.
- [x] Mostrar claramente que recibe el usuario al pagar.
- [x] Revisar textos de consentimiento antes del pago.

## 9. Dokploy y variables de entorno

- [x] Agregar variables Wompi en Dokploy para backend.
- [x] Agregar variables Wompi en `.env.production.template`.
- [x] Agregar placeholders Wompi en `.env.example`.
- [x] Verificar que ninguna llave sensible quede en frontend.
- [x] Hacer redeploy de backend y frontend despues de integrar pagos.

Variables previstas:

- [x] `WOMPI_ENVIRONMENT`
- [x] `WOMPI_PUBLIC_KEY`
- [x] `WOMPI_INTEGRITY_SECRET`
- [x] `WOMPI_EVENT_SECRET`
- [ ] `WOMPI_PRIVATE_KEY` si despues la usamos
- [x] `WOMPI_PAYMENT_REDIRECT_URL`

## 10. Pruebas sandbox

- [ ] Crear caso real de prueba en la app.
- [ ] Iniciar pago sandbox.
- [ ] Validar pago aprobado.
- [ ] Validar pago rechazado.
- [ ] Validar que el webhook cambie el estado del expediente.
- [ ] Validar que no se pueda generar documento sin pago aprobado.
- [ ] Validar que la referencia quede guardada.
- [ ] Validar reintentos del webhook sin duplicar efectos.
- [ ] Validar que la UI refleje el estado correcto despues de refrescar.

## 11. Salida a produccion

- [x] Cargar credenciales productivas en Dokploy.
- [x] Configurar evento productivo en Wompi.
- [x] Hacer despliegue a produccion.
- [x] Ejecutar una compra real controlada.
- [x] Verificar recepcion del webhook productivo.
- [x] Verificar cambio de estado del expediente.
- [x] Verificar habilitacion del documento final.
- [ ] Verificar trazabilidad en base de datos y logs.

## 12. Operacion y soporte

- [ ] Crear procedimiento para pagos aprobados sin reflejo en UI.
- [ ] Crear procedimiento para pagos rechazados.
- [ ] Crear procedimiento para conciliacion manual por referencia.
- [ ] Registrar logs de webhook y errores de firma.
- [ ] Definir responsable de soporte para incidencias de pago.
- [ ] Definir catalogo de continuidad por tipo de caso.
- [ ] Definir regla de negocio para cobrar pasos posteriores solo cuando el usuario los active o cuando el sistema los recomiende.
- [ ] Definir si seguimiento es un producto cobrable, informativo o mixto.

## 13. Calidad juridica e IA

Este bloque es critico. No basta con generar documentos; deben estar construidos para maximizar probabilidad de exito y reducir negaciones evitables.

- [x] Documentar una matriz inicial de calidad juridica para tutela y derecho de peticion basada en fuentes oficiales.
- [x] Dejar explicito que la calidad juridica debe cubrir todo el catalogo permitido sin abogado, no solo tutela y derecho de peticion.
- [x] Integrar a la matriz base los requisitos del documento local `123tutela_Requisitos_Juridicos_Documentos_Calidad.docx`.
- [x] Implementar una primera capa de validacion runtime para tutela, derecho de peticion y habeas data.
- [ ] Definir los criterios juridicos minimos por tipo de documento: tutela, derecho de peticion, carta formal, reclamo, impugnacion, desacato, etc.
- [ ] Definir la estructura obligatoria por documento:
  - hechos
  - derechos vulnerados o interes juridico
  - fundamentos normativos
  - pretensiones claras
  - pruebas o anexos
  - competencia o destino
  - firma y datos del accionante
- [ ] Definir el tono y tecnica narrativa por producto:
  - claridad
  - precision fáctica
  - lenguaje juridico suficiente pero no inflado
  - pretensiones concretas
  - no inventar hechos, normas ni anexos
- [ ] Definir que informacion minima debe pedir la IA al usuario antes de generar cada tipo de documento.
- [ ] Definir que informacion adicional es opcional pero mejora la calidad del resultado.
- [ ] Crear reglas para detectar cuando el caso esta incompleto y no debe generarse automaticamente sin pedir mas datos.
- [ ] Crear reglas para detectar contradicciones, fechas faltantes, falta de prueba o ausencia de legitimacion.
- [ ] Definir cuando recomendar tutela y cuando no recomendarla para evitar tutelas débiles o improcedentes.
- [ ] Definir cuando exigir agotamiento de via previa o reclamacion previa.
- [ ] Definir cuando sugerir derecho de peticion antes de tutela.
- [ ] Definir cuando ofrecer impugnacion, desacato, seguimiento o nueva actuacion.
- [ ] Crear plantillas base por tipo de producto con alta calidad juridica.
- [ ] Revisar el grosor argumentativo de cada plantilla:
  - suficiencia constitucional o legal
  - conexidad entre hechos y pretensiones
  - peticiones medibles y ejecutables
  - anexos esperados
- [ ] Definir una politica estricta para citas:
  - normas permitidas
  - jurisprudencia permitida
  - cuando citar y cuando no citar
  - no citar sin soporte verificable
- [ ] Definir criterios de calidad minima antes de entregar un documento al cliente.
- [ ] Crear evaluacion manual o semiautomatica de documentos generados.
- [ ] Crear un set de casos de prueba reales o anonimizados para medir calidad de salida.
- [ ] Validar que el documento final no se limite a sonar juridico; debe ser util, procedente y accionable.

## 14. Intake del usuario

- [x] Documentar un intake minimo inicial para tutela, derecho de peticion y habeas data.
- [x] Implementar una primera version del intake guiado en frontend con mezcla de campos estructurados y texto libre.
- [x] Implementar preguntas dinamicas iniciales para Salud y Habeas Data dentro del wizard.
- [x] Implementar preguntas dinamicas iniciales para Derecho de Peticion en categorias de respuesta formal.
- [x] Implementar preguntas dinamicas iniciales para Laboral, Bancos, Servicios y Consumidor.
- [ ] Diseñar los formularios de entrada por categoria para pedir mejores hechos.
- [ ] Definir preguntas dinamicas por tipo de caso.
- [x] Implementar una primera separacion entre campos estructurados y texto libre dentro del wizard.
- [x] Implementar una primera captura guiada de fechas, respuestas previas, entidad, pruebas y actos o decisiones relevantes.
- [x] Implementar una primera capa de validaciones minimas de longitud, claridad y completitud antes del preview.
- [x] Implementar una primera capa de ayudas de redaccion por categoria dentro del wizard.
- [x] Bloquear el preview cuando la informacion base siga siendo insuficiente para un analisis juridico serio.
- [x] Bloquear el guardado del expediente cuando la revision juridica inicial detecte datos criticos faltantes en tutela, derecho de peticion o habeas data.
- [x] Aplicar una primera capa equivalente de enforcement en backend para no depender solo del frontend.

## 15. Radicacion y canales

- [ ] Definir estrategia de radicacion por tipo de documento.
- [ ] Confirmar que Evolution API sera el canal inicial donde aplique y documentar limites reales.
- [ ] Definir que parte de la radicacion sera automatica y cual sera asistida o manual.
- [ ] Definir como se enviara el radicado o comprobante al cliente:
  - correo
  - panel
  - ambos
- [ ] Definir que evidencia se guarda de cada envio.
- [ ] Definir como registrar errores de entrega, rebotes o rechazo del canal.
- [ ] Definir fallback cuando no exista canal digital confiable.
- [ ] Definir SLA real por canal de radicacion.

## 16. Criterio de cierre

Solo damos este bloque por terminado cuando se cumpla todo lo siguiente:

- [x] El pago demo ya no existe.
- [x] El usuario puede pagar con Wompi en produccion.
- [x] El backend valida el pago por webhook.
- [x] El expediente cambia a pagado correctamente.
- [x] El documento final solo se habilita tras pago aprobado.
- [x] Hay paginas legales publicas visibles.
- [x] La prueba real en produccion quedo completada.
- [ ] La calidad juridica del documento fue validada con criterios claros por tipo de producto.
- [ ] La IA pide informacion suficiente antes de generar documentos sensibles.
- [ ] La estrategia de radicacion y entrega de comprobantes esta cerrada.

## 17. Lo que necesitamos ya para arrancar

- [x] Precio oficial en COP.
- [x] Decision final: Widget o Web Checkout.
- [ ] Credenciales sandbox.
- [x] Credenciales produccion.
- [x] Confirmacion de la URL final de resultado.
- [ ] Confirmacion de la politica de reembolso.
- [x] Confirmacion del catalogo inicial completo de productos individuales.
- [x] Confirmacion del texto comercial de cada producto.
- [ ] Confirmacion de reglas juridicas minimas por tipo de documento.
- [ ] Confirmacion de formularios y preguntas minimas por tipo de caso.
- [ ] Confirmacion del canal inicial de radicacion y su evidencia de entrega.
