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

- [ ] Confirmar el precio oficial en COP.
- [ ] Confirmar el nombre del producto que compra el usuario.
- [ ] Confirmar si el pago cubre solo generacion del documento o tambien envio/radicacion.
- [ ] Confirmar politica de reembolso.
- [ ] Confirmar texto legal visible antes de pagar.
- [ ] Definir la descripcion comercial corta de cada producto.
- [ ] Definir la descripcion detallada de cada producto.
- [ ] Definir exactamente que significa la promesa `menos de 5 minutos` en cada flujo.

## 2. Accesos y credenciales

- [ ] Crear o validar cuenta Wompi.
- [ ] Completar vinculacion para cobros en produccion.
- [ ] Obtener credenciales sandbox.
- [ ] Obtener credenciales produccion.
- [ ] Guardar secretos solo en `.env` o en variables seguras de Dokploy.

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

- [ ] Confirmar URL publica frontend: `https://123tutelaapp.com`
- [ ] Confirmar URL publica backend: `https://api.123tutelaapp.com`
- [ ] Definir URL de resultado de pago: `https://123tutelaapp.com/pago/resultado`
- [ ] Definir webhook sandbox: `https://api.123tutelaapp.com/payments/wompi/webhook/sandbox`
- [ ] Definir webhook produccion: `https://api.123tutelaapp.com/payments/wompi/webhook`
- [ ] Configurar URL de eventos sandbox en Wompi.
- [ ] Configurar URL de eventos produccion en Wompi.

## 4. Decisiones de implementacion

- [ ] Confirmar que arrancamos con Wompi Widget o Web Checkout.
- [ ] Usar validacion final por webhook, no por redireccion.
- [ ] Mantener el frontend sin secretos de Wompi.
- [ ] Generar referencias de pago unicas por intento.
- [ ] Definir estados internos de pago: `pending`, `approved`, `declined`, `error`, `voided`.
- [x] Implementar desde el inicio todo el catalogo de productos individuales.
- [ ] Dejar los combos para una fase posterior, cuando las reglas de encadenamiento esten cerradas.

Decision recomendada para este MVP:

- [ ] Fase 1: Widget o Checkout + webhook para todos los productos individuales.
- [ ] Fase 2: evaluar API avanzada solo si luego hace falta tokenizacion, devoluciones o cargos mas complejos.
- [ ] Fase 2: agregar combos cuando el motor de continuidad comercial este completamente definido.

## 5. Base de datos

- [ ] Crear tabla `payments` o `payment_orders`.
- [ ] Relacionar cada pago con `case_id` y `user_id`.
- [ ] Guardar `reference`, `amount_in_cents`, `currency`, `status`, `transaction_id`, `provider`, `environment`.
- [ ] Guardar payload crudo del webhook para auditoria.
- [ ] Guardar timestamps de creacion, aprobacion y ultimo cambio de estado.
- [ ] Crear indice por `reference`.
- [ ] Crear indice por `transaction_id`.

## 6. Backend

- [ ] Crear modulo Wompi en backend.
- [ ] Crear endpoint para iniciar pago y entregar configuracion segura al frontend.
- [ ] Crear generacion de firma de integridad.
- [ ] Crear endpoint webhook de Wompi.
- [ ] Validar firma del evento entrante.
- [ ] Hacer idempotente el webhook para no procesar dos veces el mismo evento.
- [ ] Marcar el expediente como pagado solo con evento `approved`.
- [ ] Registrar errores y rechazos de pago.
- [ ] Deshabilitar el flujo `pago demo`.

Rutas sugeridas:

- [ ] `POST /payments/wompi/checkout-session`
- [ ] `POST /payments/wompi/webhook`
- [ ] `POST /payments/wompi/webhook/sandbox`
- [ ] `GET /payments/{reference}`

## 7. Frontend

- [ ] Reemplazar boton `Confirmar pago demo`.
- [ ] Mostrar boton real de pago Wompi en el paso correcto.
- [ ] Mostrar estado visual: pendiente, pagado, rechazado, en revision.
- [ ] Crear pantalla `pago/resultado`.
- [ ] Mostrar mensaje claro si la redireccion vuelve antes de que llegue el webhook.
- [ ] Bloquear generacion de documento final hasta que el backend confirme pago aprobado.
- [ ] Mostrar referencia de pago al usuario.
- [ ] Mostrar informe gratis con derecho vulnerado, analisis y recomendacion antes del pago.
- [ ] Permitir elegir entre `Solo documento` y `Documento + radicacion` cuando el producto lo soporte.
- [ ] Mostrar siguientes pasos sugeridos segun el tipo de caso.
- [ ] Mostrar ofertas de continuidad: seguimiento, impugnacion, desacato y otros pasos posteriores.
- [ ] Mostrar esos pasos tanto en panel como en correo.
- [ ] Mostrar tiempos estimados, siguiente accion esperada y posibles escenarios del tramite.
- [ ] Mostrar descripcion clara del producto antes del pago.
- [ ] Mostrar que la plataforma cuenta con base de correos de juzgados y entidades para radicacion donde aplique.
- [ ] No mostrar `Guia de radicacion` ni `Documento urgente` en la oferta inicial.

## 8. UX y legal

- [ ] Crear pagina publica de Terminos.
- [ ] Crear pagina publica de Privacidad.
- [ ] Crear pagina publica de Contacto o Soporte.
- [ ] Mostrar que el cobro se procesa con Wompi.
- [ ] Mostrar claramente que recibe el usuario al pagar.
- [ ] Revisar textos de consentimiento antes del pago.

## 9. Dokploy y variables de entorno

- [ ] Agregar variables Wompi en Dokploy para backend.
- [ ] Agregar variables Wompi en `.env.production.template`.
- [ ] Agregar placeholders Wompi en `.env.example`.
- [ ] Verificar que ninguna llave sensible quede en frontend.
- [ ] Hacer redeploy de backend y frontend despues de integrar pagos.

Variables previstas:

- [ ] `WOMPI_ENVIRONMENT`
- [ ] `WOMPI_PUBLIC_KEY`
- [ ] `WOMPI_INTEGRITY_SECRET`
- [ ] `WOMPI_EVENT_SECRET`
- [ ] `WOMPI_PRIVATE_KEY` si despues la usamos
- [ ] `WOMPI_PAYMENT_REDIRECT_URL`

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

- [ ] Cargar credenciales productivas en Dokploy.
- [ ] Configurar evento productivo en Wompi.
- [ ] Hacer despliegue a produccion.
- [ ] Ejecutar una compra real controlada.
- [ ] Verificar recepcion del webhook productivo.
- [ ] Verificar cambio de estado del expediente.
- [ ] Verificar habilitacion del documento final.
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

## 13. Criterio de cierre

Solo damos este bloque por terminado cuando se cumpla todo lo siguiente:

- [ ] El pago demo ya no existe.
- [ ] El usuario puede pagar con Wompi en produccion.
- [ ] El backend valida el pago por webhook.
- [ ] El expediente cambia a pagado correctamente.
- [ ] El documento final solo se habilita tras pago aprobado.
- [ ] Hay paginas legales publicas visibles.
- [ ] La prueba real en produccion quedo completada.

## 14. Lo que necesitamos ya para arrancar

- [ ] Precio oficial en COP.
- [ ] Decision final: Widget o Web Checkout.
- [ ] Credenciales sandbox.
- [ ] Credenciales produccion.
- [ ] Confirmacion de la URL final de resultado.
- [ ] Confirmacion de la politica de reembolso.
- [ ] Confirmacion del catalogo inicial completo de productos individuales.
- [ ] Confirmacion del texto comercial de cada producto.
