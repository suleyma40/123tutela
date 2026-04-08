# Paquete de Salida Salud 2026-04-15

Objetivo: consolidar en un solo documento lo ya definido para lanzar `123tutela` solo con `salud`, dejando listo lo que debe aprobar el humano y lo que debe ejecutar el sistema.

Fecha objetivo de salida:

- `15 de abril de 2026`

Alcance confirmado:

- `Derecho de peticion en salud`
- `Accion de tutela en salud`
- `Impugnacion de tutela en salud`
- `Incidente de desacato en salud`

Regla de negocio confirmada:

- No se vende ninguna otra materia en la UX principal del lanzamiento.
- `Impugnacion` y `desacato` pueden operar como continuidad del caso o como puerta de entrada, pero solo cuando el usuario ya llega con contexto procesal minimo verificable.
- Para `impugnacion` y `desacato`, el usuario debe aportar si o si el fallo previo o una copia legible del documento judicial base para analisis.
- La IA debe leer ese fallo, extraer decision, fechas, ordenes y fundamentos relevantes antes de recomendar o generar el escrito.

## 1. Precios encontrados en el proyecto

Fuente local:

- `directives/catalogo_productos_individuales_2026.md`

Precios originalmente encontrados en el repo:

| Producto salud | Solo documento | Documento + radicacion |
| --- | ---: | ---: |
| Derecho de peticion en salud | 41.900 COP | 77.900 COP |
| Accion de tutela en salud | 76.900 COP | 112.900 COP |
| Impugnacion de tutela en salud | 76.900 COP | 112.900 COP |
| Incidente de desacato en salud | 84.900 COP | 120.900 COP |

Regla de precio existente:

- `Documento + radicacion = precio base + 36.000 COP`

Decision operativa ajustada:

- Bajar los precios aproximadamente un `12%`, dentro del rango pedido de `10% a 15%`.
- No crear descuentos, combos ni addons adicionales antes del lanzamiento.
- Mantener `analisis gratis` y cobro solo por activacion del documento o del paquete con radicacion.

Precios propuestos para lanzamiento:

| Producto salud | Solo documento | Documento + radicacion |
| --- | ---: | ---: |
| Derecho de peticion en salud | 36.900 COP | 72.900 COP |
| Accion de tutela en salud | 67.900 COP | 103.900 COP |
| Impugnacion de tutela en salud | 67.900 COP | 103.900 COP |
| Incidente de desacato en salud | 74.900 COP | 110.900 COP |

## 2. Oferta comercial propuesta para aprobacion

### 2.1 Nombre y descripcion visible

| Producto | Nombre visible propuesto | Uso comercial corto |
| --- | --- | --- |
| Derecho de peticion en salud | Derecho de peticion en salud | Para pedir autorizacion, respuesta, entrega de servicio, medicamento, cita o explicacion formal a la EPS, IPS o entidad de salud. |
| Accion de tutela en salud | Tutela en salud | Para proteger el derecho fundamental a la salud cuando existe urgencia, barrera seria o riesgo actual para el paciente. |
| Impugnacion | Impugnacion de tutela en salud | Para controvertir un fallo de tutela cuando fue negado, limitado o valoro mal el caso. Solo debe ofrecerse si el usuario aporta el fallo para lectura y analisis. |
| Desacato | Incidente de desacato en salud | Para exigir cumplimiento de un fallo de tutela ya favorable que la entidad no esta obedeciendo. Solo debe ofrecerse si el usuario aporta el fallo y la orden incumplida puede leerse o reconstruirse con claridad. |

### 2.2 Que incluye cada opcion

#### Solo documento

- Analisis inicial del caso sin costo.
- Recomendacion de la ruta juridica aplicable.
- Documento final listo para revisar y usar.
- Acceso al expediente y al panel del caso.
- No incluye radicacion por parte de 123tutela.

#### Documento + radicacion

- Todo lo de `Solo documento`.
- Activacion del flujo de firma electronica simple.
- Intento de radicacion por 123tutela cuando exista canal operativo compatible.
- Evidencia visible en panel del envio, radicado o estado operativo disponible.
- Seguimiento inicial del expediente en el panel.

## 3. Promesa comercial propuesta

Texto principal propuesto:

> Analisis gratis. Si decides activar el servicio, 123tutela genera tu documento y puede gestionar la radicacion en menos de 5 minutos cuando exista un canal digital compatible y la informacion del caso este completa.

Version corta para landing o checkout:

> Analisis gratis y radicacion en menos de 5 minutos cuando el canal lo permite.

Version legalmente mas segura para aprobar:

> El tiempo estimado de menos de 5 minutos aplica a la generacion del documento y al inicio del envio o radicacion digital cuando el usuario ya completo la informacion necesaria, el pago fue confirmado y el canal de destino permite tramite operativo inmediato. No garantiza respuesta ni radicado definitivo dentro de ese mismo tiempo.

## 4. Texto legal previo al pago propuesto

Texto propuesto para checkout:

> Estas activando un servicio digital de preparacion documental juridica y, si eliges esa opcion, gestion de radicacion operativa. 123tutela analiza la informacion que suministras, recomienda una ruta legal y genera el documento correspondiente para tu caso. La plataforma no garantiza un resultado judicial o administrativo especifico, porque la decision final depende de la entidad o del juzgado competente y de la veracidad, suficiencia y oportunidad de la informacion aportada. La activacion del documento y de la radicacion solo ocurre cuando el pago ha sido confirmado de forma segura. Si el canal de radicacion elegido no permite tramite automatico o requiere gestion adicional, el expediente mostrara el estado aplicable y el siguiente paso recomendado.

Checkbox propuesto:

> Confirmo que entiendo que estoy comprando un servicio de preparacion documental y, cuando aplique, de radicacion operativa; que no se me esta garantizando un resultado; y que la activacion depende de la confirmacion segura del pago.

## 5. Politica de reembolso propuesta para aprobacion

Politica propuesta:

1. Si el pago fue cobrado pero el documento no se activo por una falla tecnica atribuible a 123tutela, procede reembolso total o activacion manual prioritaria, a eleccion del usuario.
2. Si el documento final ya fue generado y puesto a disposicion del usuario en el panel, el valor de `Solo documento` no es reembolsable, salvo falla tecnica grave, cobro duplicado o error operativo atribuible a la plataforma.
3. Si el usuario pago `Documento + radicacion` y la radicacion automatica no pudo ejecutarse por una limitacion del canal, falta de datos esenciales o necesidad de gestion manual, no procede reembolso automatico del documento ya generado. Debe evaluarse si corresponde:
   - reembolso parcial del componente de radicacion, o
   - cambio a gestion asistida, o
   - saldo a favor operativo
4. Si hubo cobro duplicado, procede devolucion del cobro repetido una vez conciliado el pago.
5. No procede reembolso por decisiones del juzgado, respuesta negativa de la EPS, improcedencia declarada por la autoridad o cambios de opinion del usuario despues de recibir el documento final, salvo que exista una falla atribuible a la plataforma.

Decision sugerida:

- Aprobar esta politica como base de lanzamiento.
- Ajustarla mas adelante solo si aparecen patrones reales de soporte.

## 6. Lo que yo debo ejecutar ya

- Alinear frontend y checkout al alcance exclusivo de salud.
- Ajustar copy visible a los 4 productos de salud.
- Dejar integrados los textos aprobados en UI y flujo de pago.
- Preparar lote de casos de prueba sinteticos.
- Endurecer QA y recorrido de continuidad para impugnacion y desacato.
- Habilitar rutas de entrada directas para impugnacion y desacato con filtros estrictos.

## 7. Lo que debes aprobar o definir tu

- Aprobar precios finales o pedir ajuste.
- Aprobar promesa comercial.
- Aprobar texto legal previo al pago.
- Aprobar politica de reembolso.
- Confirmar si el termino visible sera `radicacion` o `radicacion y seguimiento`.

## 8. Casos de prueba sinteticos propuestos para salud

Base usada para construirlos:

- Informe de tutelas en salud del Ministerio de Salud sobre 2024, publicado en 2025:
  - https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/DE/CA/informe-tutelas-vulneracion-derecho-salud-2024.pdf
- Consolidado oficial de PQRD y solicitudes de informacion de la Superintendencia Nacional de Salud:
  - https://docs.supersalud.gov.co/PortalWeb/ProteccionUsuario/EstadisticasPQRD/Forms/Consolidado%20PQRD.aspx

Inferencia operativa a partir de esas fuentes:

- Las barreras repetidas en salud suelen concentrarse en autorizaciones, entrega de medicamentos, continuidad de tratamientos, citas con especialista, procedimientos, demoras y falta de respuesta oportuna.
- Por eso, los casos sinteticos del lanzamiento deben concentrarse ahi y no en escenarios exoticos.

### Lote inicial de QA

| Caso | EPS sugerida | Producto esperado | Resumen |
| --- | --- | --- | --- |
| 1 | Nueva EPS | Derecho de peticion en salud | Paciente con orden de resonancia y cita con especialista; la EPS no responde una solicitud formal de autorizacion y no hay urgencia vital inmediata. |
| 2 | Sanitas | Tutela en salud | Menor con continuidad de terapias ordenadas; la EPS suspendio sesiones y el cuadro empeora. |
| 3 | Sura | Tutela en salud | Mujer embarazada de alto riesgo con demora en autorizacion de medicamento o control prioritario. |
| 4 | Compensar | Derecho de peticion en salud | Usuario requiere entrega de medicamento PBS y la farmacia reporta espera indefinida sin respuesta de fondo. |
| 5 | Coosalud | Tutela en salud | Paciente con discapacidad necesita silla de ruedas o insumo funcional ordenado medicamente y la EPS mantiene barreras de autorizacion. |
| 6 | Nueva EPS | Impugnacion de tutela en salud | Juzgado nego tutela pese a historia clinica y riesgo actual; el usuario sigue dentro de termino para impugnar. |
| 7 | Sanitas | Incidente de desacato en salud | Ya existe fallo favorable para procedimiento o medicamento, pero la EPS no cumple dentro del plazo fijado. |
| 8 | Sura | Bloqueo esperado | Usuario quiere tutela pero no identifica EPS, no tiene orden medica ni explica riesgo actual. Debe bloquearse o pedir mas datos. |
| 9 | Compensar | Derecho de peticion en salud | Usuario pide copia de historia, autorizaciones y explicacion de glosas o negaciones previas para preparar paso posterior. |
| 10 | Coosalud | Tutela en salud | Adulto mayor con dolor severo y cirugia demorada pese a orden del medico tratante y gestion previa documentada. |

## 9. Orden de trabajo hasta la salida

### Antes de tocar UI o checkout

- [ ] Aprobar seccion 2
- [ ] Aprobar seccion 3
- [ ] Aprobar seccion 4
- [ ] Aprobar seccion 5

### Luego

- [ ] Ajustar frontend al alcance solo salud
- [ ] Integrar copy final de productos
- [ ] Integrar texto legal en flujo de pago
- [ ] Integrar politica de reembolso en vista legal o checkout
- [ ] Crear y ejecutar lote de QA con los 10 casos sinteticos

## 10. Como hacer que impugnacion y desacato tambien sean puerta de entrada

Decision de producto propuesta:

- Si, pueden ser puerta de entrada.
- Pero no como venta abierta y generica.
- Deben tener `entrada condicionada por evidencia minima`.

Regla para `Impugnacion de tutela en salud` como entrada:

- Mostrarla como opcion inicial cuando el usuario diga que ya tuvo fallo de tutela.
- Exigir carga del fallo o providencia base antes de permitir activacion del producto.
- Pedir desde el primer paso:
  - juzgado o despacho
  - fecha del fallo o fecha de notificacion
  - resultado del fallo
  - por que considera equivocada la decision
  - copia del fallo si la tiene
- La IA debe leer el fallo y extraer:
  - sentido de la decision
  - razones centrales del despacho
  - puntos discutibles para contraargumentar
  - fecha y riesgo de vencimiento del termino
- Bloquear si no hay fallo adjunto legible, si no hay contexto procesal suficiente o si parece estar fuera de termino sin explicacion.

Regla para `Incidente de desacato en salud` como entrada:

- Mostrarlo como opcion inicial cuando el usuario diga que ya gano una tutela pero la orden no se ha cumplido.
- Exigir carga del fallo favorable antes de permitir activacion del producto.
- Pedir desde el primer paso:
  - juzgado que emitio el fallo
  - fecha del fallo
  - orden concreta incumplida
  - quien esta incumpliendo
  - desde cuando no cumplen
  - prueba minima del incumplimiento
- La IA debe leer el fallo y extraer:
  - ordenes concretas impartidas
  - plazo o condicion de cumplimiento
  - entidad obligada
  - hechos utiles para demostrar incumplimiento actual
- Bloquear si no hay fallo adjunto legible, si no se identifica la orden incumplida o si no hay base minima para demostrar incumplimiento.

Implementacion UX recomendada:

- En el wizard inicial, agregar una pregunta muy temprana:
  - `Tu caso esta empezando o ya tienes un fallo de tutela previo?`
- Opciones operativas:
  - `Aun no tengo fallo`
  - `Ya tengo fallo y quiero impugnar`
  - `Ya tengo fallo favorable y no lo cumplen`
- Si elige una de las dos ultimas, saltar a intake especializado.

Ventaja comercial:

- Capturas usuarios que ya llegan en un momento de dolor fuerte y urgencia alta.
- Son casos con intencion de pago mas clara porque el problema ya esta definido.

Riesgo si se hace mal:

- vender impugnaciones fuera de termino
- vender desacatos sin fallo identificable
- generar documentos inviables

Por eso la regla correcta no es `abrirlos a todo el mundo`, sino `abrirlos con intake corto pero juridicamente duro`.

Implicacion tecnica obligatoria:

- La capa de adjuntos debe tratar el fallo previo como insumo principal del caso.
- El analisis del fallo no puede ser opcional ni decorativo.
- Sin lectura estructurada del fallo, no se debe desbloquear `impugnacion` ni `desacato`.

## 11. Decision pendiente mas importante

Falta tu aprobacion sobre este punto:

- si el paquete premium visible al cliente se llama `Documento + radicacion`
- o si se llama `Documento + radicacion y seguimiento`

Mi recomendacion:

- usar `Documento + radicacion`

Razon:

- es mas corto
- es mas claro comercialmente
- evita discutir que tanto seguimiento incluye
- el seguimiento puede quedar descrito como consecuencia operativa visible en panel, no como promesa principal
