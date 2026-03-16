# Integracion del Manual de Produccion v1

Fuente incorporada:

- documento local del usuario: `123tutela_Manual_Produccion_v1.docx`

Objetivo: convertir el manual descargado en reglas operativas para continuar el roadmap de produccion real.

## 1. Hallazgos clave del manual

El documento agrega cinco exigencias fuertes que cambian el nivel del producto:

- reglas juridicas profundas por tipo de documento, no solo por categoria
- prompts de produccion separados por producto
- plantillas de salida con secciones obligatorias y fallas bloqueantes
- scoring QA automatico del documento antes de entregarlo
- radicacion, correo post-radicado, sandbox y politica legal como piezas obligatorias de produccion

## 2. Reglas nuevas que deben gobernar el producto

### 2.1 Tutela

- verificar improcedencia antes de generar
- exigir juramento de no temeridad
- exigir argumentacion de subsidiariedad e inmediatez
- bloquear si el caso encaja mejor en peticion, reclamo o cumplimiento
- exigir contra particulares solo bajo supuestos del Art. 42 del Decreto 2591 de 1991
- impugnacion: 3 dias habiles desde notificacion
- medida provisional solo si la urgencia esta soportada

### 2.2 Derecho de peticion

- usar Art. 23 CP + Ley 1755 de 2015
- distinguir modalidad: general, particular, informacion, documentos, consulta
- exponer termino legal segun el tipo
- advertir falta disciplinaria por no responder
- advertir que el silencio puede habilitar tutela
- exigir respuesta de fondo, no simple acuse de recibo

### 2.3 Desacato

- siempre va ante el mismo juez de primera instancia
- requiere prueba de tres cosas:
  - existencia del fallo
  - notificacion del fallo
  - incumplimiento actual
- no debe generarse si el usuario no tiene identificable el fallo o la orden incumplida

### 2.4 Impugnacion

- verificar plazo fatal de 3 dias habiles
- contraargumentar cada razon relevante del fallo
- si el plazo vencio, no fingir impugnacion valida

### 2.5 Quejas y habeas data

- varias entidades de control exigen reclamacion previa
- en habeas data debe exigirse reclamo previo al responsable del dato antes de SIC
- en consumidor, financiero y servicios debe validarse primero la reclamacion directa

### 2.6 Cumplimiento, popular y recursos

- accion de cumplimiento exige renuencia previa y deber claro
- accion popular exige interes colectivo real, no solo dano individual
- reposicion/apelacion exige acto recurrible y control estricto del termino

## 3. Reglas de generacion

El manual deja claro que no basta con “redactar bonito”. La generacion debe obedecer:

- system prompt separado por tipo de documento
- estructura fija por producto
- minimos obligatorios de secciones
- bloqueo si falta una seccion critica

Primera traduccion al sistema:

- `document_rules.py`: define lo minimo exigible por producto
- `document_templates.py`: arma una salida base por producto

Pendiente siguiente:

- prompts especializados por producto con instrucciones duras de calidad
- regeneracion guiada cuando falte grosor juridico

## 4. Reglas de QA automatico

El manual propone una arquitectura correcta:

1. generar documento
2. evaluarlo con una segunda llamada de QA
3. obtener score, falencias y recomendacion
4. si el score es bajo, regenerar o pedir mas datos

Decision operativa para este repo:

- umbral inicial sugerido de aprobacion: `70/100`
- maximo inicial sugerido: `2` regeneraciones
- si sigue por debajo del umbral:
  - no entregar como documento final silenciosamente
  - advertir
  - o pedir mas datos

## 5. Reglas para continuar el roadmap

Orden correcto a partir de este manual:

1. endurecer prompts por producto
2. implementar QA automatico con scoring
3. conectar scoring al endpoint de generacion
4. cerrar flujo de radicacion por canal
5. cerrar correo post-radicado y continuidad del caso
6. cerrar sandbox formal con casos de prueba
7. cerrar politica de reembolso y textos legales finos

## 6. Cambios concretos que este manual obliga

- no permitir tutela sin control de procedencia
- no permitir impugnacion fuera de termino sin advertencia
- no permitir desacato sin fallo identificable
- no permitir habeas data sin validar reclamo previo
- no entregar documento final sin control minimo de calidad
- no dejar la radicacion, el correo y la trazabilidad para “despues”

## 7. Estado de integracion

Ya absorbido del manual:

- refuerzo del enfoque por tipo de documento
- necesidad de prompts por producto
- necesidad de QA automatico
- necesidad de reglas de plazo y procedencia mas duras

Pendiente de implementar desde el manual:

- prompts de produccion por producto
- rubrica de scoring automatica
- regeneracion por falencias
- flujo de correo post-radicado
- sandbox formal de pruebas
- politica de reembolso cerrada
