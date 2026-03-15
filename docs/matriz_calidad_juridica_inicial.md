# Matriz Inicial de Calidad Juridica

Objetivo: convertir requisitos juridicos y de calidad documental en reglas operativas para 123tutela. Este documento no reemplaza revision profesional final; sirve como base para prompts, validaciones, intake y QA.

## 1. Principios rectores

- No generar documentos que suenen juridicos pero sean improcedentes, incompletos o debiles.
- No inventar hechos, anexos, autoridades, respuestas previas ni citas.
- Exigir hechos verificables, fechas, entidad o accionado y pretensiones claras.
- Separar con rigor:
  - hechos
  - problema juridico
  - derechos o intereses comprometidos
  - fundamento normativo
  - pretensiones
  - anexos
  - canal de radicacion
- Si falta informacion critica, la IA debe pedirla antes de redactar.

## 2. Accion de tutela

### 2.1 Regla de procedencia minima

La tutela debe tratarse como ruta fuerte solo si, al menos preliminarmente, se cumplen estas condiciones:

- hay amenaza o vulneracion actual o inminente de un derecho fundamental
- el accionante puede identificarse con claridad
- existe un accionado identificable o al menos determinable
- no hay otro medio judicial idoneo y eficaz para la proteccion inmediata, o existe riesgo de perjuicio irremediable
- los hechos son recientes o existe justificacion razonable de inmediatez

### 2.2 Señales para no recomendar tutela automaticamente

- el caso es puramente patrimonial sin conexion clara con derecho fundamental
- no se sabe que hizo o dejo de hacer la entidad o particular
- no hay fechas, ni respuesta previa, ni urgencia, ni daño concreto
- existe via ordinaria claramente idonea y no hay urgencia manifiesta
- el usuario solo tiene inconformidad general, pero no identifica vulneracion concreta

### 2.3 Informacion minima obligatoria para redactar tutela

- nombre del accionante
- documento de identidad
- ciudad y departamento
- entidad, autoridad o particular accionado
- relato claro de hechos en orden cronologico
- fecha o periodo aproximado de ocurrencia
- que se solicito antes, si hubo solicitud previa
- que respondio la entidad, si respondio
- cual derecho fundamental se siente afectado
- que daño actual o riesgo concreto existe
- que se pide exactamente al juez

### 2.4 Informacion que mejora mucho la calidad

- soportes medicos, administrativos o contractuales
- numero de radicado previo
- fecha exacta de negativa o silencio
- diagnostico, formula o concepto medico
- prueba del perjuicio actual
- identificacion precisa del despacho o canal sugerido

### 2.5 Estructura obligatoria de la tutela

- identificacion del accionante
- identificacion del accionado
- hechos cronologicos, concretos y no inflados
- derechos fundamentales vulnerados o amenazados
- fundamentos constitucionales y legales solo si son pertinentes
- justificacion de procedencia:
  - subsidiariedad
  - inmediatez
  - urgencia o perjuicio irremediable si aplica
- pretensiones especificas, medibles y ejecutables
- solicitud de medida provisional si de verdad se justifica
- anexos
- juramento o manifestacion equivalente cuando corresponda

### 2.6 Calidad narrativa exigida

- narracion cronologica
- frases cortas y verificables
- una afirmacion relevante por idea
- evitar grandilocuencia moral o dramatizacion vacia
- no repetir citas o articulos por adornar
- conectar cada pretension con un hecho concreto

### 2.7 Errores que deben bloquear o degradar la salida

- no se identifica accionado
- no se identifica derecho comprometido
- no hay pretension concreta
- no hay hechos fechables
- no hay explicacion de urgencia en un caso que parece ordinario
- el texto mezcla queja emocional con hechos sin separar
- la IA propone tutela pero el propio caso muestra que falta via previa evidente sin urgencia

### 2.8 Heuristicas iniciales por categoria

Salud / EPS:
- favorecer tutela si hay urgencia, continuidad de tratamiento, medicamento, cita prioritaria, procedimiento o riesgo de agravacion
- pedir siempre: diagnostico, orden medica, negativa o demora, EPS, IPS y fechas

Habeas data:
- no disparar tutela primero si falta reclamacion previa, salvo afectacion grave o urgencia
- pedir: reporte, entidad fuente, reclamacion previa, respuesta y daño actual

Laboral:
- no vender tutela automatica por cualquier conflicto laboral
- pedir: tipo de relacion, despido o acto concreto, fecha, afectacion a minimo vital, estabilidad reforzada o condicion de debilidad manifiesta

Servicios y consumidor:
- no usar tutela si el conflicto es ordinario y no hay derecho fundamental comprometido
- pedir siempre prueba de reclamacion previa y daño real

## 3. Derecho de peticion

### 3.1 Cuando debe sugerirse

- cuando se necesita respuesta formal de fondo de una autoridad o particular obligado
- cuando la via previa mejora o condiciona un paso posterior
- cuando falta constancia escrita de la solicitud del usuario

### 3.2 Informacion minima obligatoria

- autoridad o destinatario
- nombre e identificacion del peticionario
- direccion fisica o electronica para respuesta
- hechos o razones de la peticion
- lo que solicita exactamente
- anexos si existen

### 3.3 Calidad minima de la peticion

- objeto claro desde el inicio
- solicitudes numeradas
- lenguaje respetuoso
- sin exceso de citas innecesarias
- debe permitir respuesta de fondo

### 3.4 Plazos que la app debe tener presentes

- regla general: 15 dias para resolver de fondo
- documentos e informacion: 10 dias
- consultas: 30 dias

### 3.5 Señales para mejorar o bloquear

- la solicitud no dice que se quiere exactamente
- no identifica destinatario
- no deja canal de respuesta
- confunde queja, denuncia y peticion en un solo texto desordenado
- el usuario necesita una pretension mas concreta para que la respuesta sea util

## 4. Politica de citas y soporte

- citar primero norma basica aplicable
- citar jurisprudencia solo cuando aporte una regla util al caso
- no citar sentencias de memoria sin soporte verificable
- no llenar el documento de citas si el caso no lo requiere
- la fuerza del documento debe venir de hechos bien planteados + pretensiones bien construidas

## 5. Intake recomendado para la IA

Antes de redactar una tutela o un derecho de peticion, la IA deberia confirmar:

- que paso exactamente
- cuando paso
- contra quien
- que pidio el usuario antes
- que respondieron
- que daño esta sufriendo hoy
- que necesita que ocurra
- que pruebas tiene

Si dos o mas de esas respuestas faltan, la IA no deberia cerrar un documento final sin repreguntar.

## 6. QA minimo antes de entregar al cliente

- el documento identifica sujeto activo y pasivo
- los hechos tienen secuencia
- las pretensiones se pueden cumplir o negar de forma concreta
- no hay contradicciones internas
- no hay citas inventadas
- el remedio escogido coincide con el caso
- si es tutela, hay una justificacion razonable de procedencia
- si es derecho de peticion, la solicitud puede responderse de fondo

## 7. Implicaciones para producto

- el formulario de intake no puede ser solo texto libre
- debe haber preguntas dinamicas por tipo de caso
- la IA necesita checklists de suficiencia antes de generar
- algunas salidas deben quedar en estado `insuficiente informacion`
- la app debe preferir pedir un dato mas antes que entregar una tutela debil

## 8. Fuentes oficiales base

- Constitución Política, artículo 86: acción de tutela
  - https://www.suin-juriscol.gov.co/legislacion/accionesconstitucionales.html
- Decreto 2591 de 1991, artículo 14: contenido e informalidad de la solicitud de tutela
  - https://www.suin-juriscol.gov.co/viewDocument.asp?id=1470723
- Reglas de competencia y reparto relacionadas con tutela
  - https://www.suin-juriscol.gov.co/legislacion/accionesconstitucionales.html
- Derecho de petición: objeto, modalidades, contenido y términos
  - https://www.suin-juriscol.gov.co/legislacion/derechodepeticion.html
- Referencia administrativa sobre términos de respuesta y contenido de la petición
  - https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=170948
  - https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=266477

## 9. Estado

Esto es una matriz inicial. Falta convertirla en:

- prompts estructurados
- validaciones de intake
- reglas por categoria
- pruebas con casos reales anonimizados
- criterios de scoring de calidad de salida
