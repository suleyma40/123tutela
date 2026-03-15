# Matriz Inicial de Calidad Juridica

Objetivo: convertir requisitos juridicos y de calidad documental en reglas operativas para 123tutela. Este documento no reemplaza revision profesional final; sirve como base para prompts, validaciones, intake y QA.

## 0. Alcance real del producto

123tutela no solo genera tutelas. Esta matriz debe cubrir todo documento permitido para actuacion directa del ciudadano sin necesidad de abogado, al menos en esta fase:

- accion de tutela
- derecho de peticion
- carta formal a entidad
- queja formal
- reclamo administrativo
- habeas data
- recurso de reposicion o apelacion cuando proceda sin apoderado
- queja disciplinaria
- accion de cumplimiento
- impugnacion de tutela
- incidente de desacato
- accion popular en los escenarios habilitados para actuacion ciudadana

Regla base:

- cada producto requiere criterio propio de procedencia
- cada producto exige una estructura narrativa distinta
- cada producto debe pedir informacion minima distinta
- la IA no debe convertir todo en tutela por defecto
- la seleccion del remedio correcto es tan importante como la redaccion

## 1. Principios rectores

- No generar documentos que suenen juridicos pero sean improcedentes, incompletos o debiles.
- No inventar hechos, anexos, autoridades, respuestas previas ni citas.
- Exigir hechos verificables, fechas, entidad o accionado y pretensiones claras.
- El objetivo no es producir plantillas genericas de dos parrafos; el objetivo es producir documentos que un juez o entidad tome en serio, con calidad comparable a la de un abogado competente.
- Separar con rigor:
  - hechos
  - problema juridico
  - derechos o intereses comprometidos
  - fundamento normativo
  - pretensiones
  - anexos
  - canal de radicacion
- Si falta informacion critica, la IA debe pedirla antes de redactar.

Estándar minimo transversal de calidad:

- identificacion completa de las partes
- hechos cronologicos, claros y detallados
- derecho vulnerado o interes juridico identificado con precision
- fundamentacion juridica suficiente
- jurisprudencia aplicable cuando aporte regla util
- pruebas enumeradas y referenciadas
- pretensiones claras, concretas y ejecutables
- datos de notificacion del usuario y, cuando aplique, del destinatario o accionado

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
- direccion de residencia
- telefono o celular
- correo electronico recomendado
- ciudad y departamento
- entidad, autoridad o particular accionado
- direccion de la entidad accionada
- representante legal, si se conoce
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

- encabezado con despacho de reparto y referencia constitucional
- identificacion del accionante
- identificacion del accionado
- legitimacion por activa y por pasiva
- hechos cronologicos, concretos y no inflados
- derechos fundamentales vulnerados o amenazados
- fundamentos constitucionales y legales pertinentes
- justificacion de procedencia:
  - subsidiariedad
  - inmediatez
  - urgencia o perjuicio irremediable si aplica
- pretensiones especificas, medibles y ejecutables
- solicitud de medida provisional si de verdad se justifica
- anexos
- juramento o manifestacion equivalente cuando corresponda
- notificaciones

Regla fuerte:

- los hechos de tutela deben salir numerados y en cronologia estricta
- cada hecho relevante debe poder vincularse a una prueba o anexo
- la IA no debe mezclar multiples eventos complejos en un solo hecho

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
- no incluye juramento de no temeridad
- no incluye datos de notificacion del accionante
- no identifica que orden concreta deberia impartir el juez
- no aporta o no referencia pruebas minimas para hechos clave

### 2.9 Checklist reforzado de tutela

- nombre completo y cedula del accionante
- accionado identificado con direccion o medio de notificacion razonable
- minimo funcional de hechos cronologicos suficientes
- derecho fundamental conectado con articulo constitucional
- explicacion de por que ese derecho esta vulnerado en este caso
- soporte normativo suficiente
- soporte jurisprudencial util cuando realmente agrega valor
- argumentacion de procedencia frente a subsidiariedad e inmediatez
- pretensiones concretas con terminos o acciones verificables
- pruebas enumeradas como anexos
- juramento de no temeridad
- notificaciones

### 2.10 Jurisprudencia base sugerida por area

Salud:
- T-760 de 2008
- T-121 de 2015
- SU-508 de 2020

Laboral:
- SU-049 de 2017
- T-320 de 2016
- T-572 de 2017

Datos y financiero:
- C-748 de 2011
- T-729 de 2002
- T-260 de 2012

Servicios publicos y consumidor:
- T-578 de 2018
- T-793 de 2012
- C-1141 de 2000

Regla:

- estas referencias deben verificarse y usarse solo cuando la regla juridica realmente coincide con el caso

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
- telefono o medio complementario de contacto
- hechos o razones de la peticion
- lo que solicita exactamente
- tipo de peticion
- anexos si existen

### 3.3 Calidad minima de la peticion

- objeto claro desde el inicio
- solicitudes numeradas
- lenguaje respetuoso
- sin exceso de citas innecesarias
- debe permitir respuesta de fondo
- debe incluir el termino legal de respuesta aplicable
- debe advertir que el incumplimiento puede habilitar tutela cuando corresponda

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

### 3.6 Checklist reforzado de derecho de peticion

- peticionario identificado
- destinatario identificado
- objeto claro y especifico
- hechos de soporte suficientes
- fundamento juridico base: articulo 23 CP y Ley 1755 de 2015
- termino legal de respuesta visible
- advertencia de falta disciplinaria o consecuencias de no responder cuando sea pertinente
- canal de notificacion del usuario

## 4. Otros productos del catalogo

### 4.1 Carta formal a entidad

Usar cuando:

- el usuario necesita dejar constancia formal
- quiere pedir, advertir, insistir o requerir sin activar todavía un mecanismo más técnico

Minimos:

- destinatario claro
- hechos resumidos
- solicitud concreta
- tono respetuoso y firme
- fecha, ciudad y medio de respuesta

No debe parecer:

- ni tutela disfrazada
- ni derecho de petición cuando no se busca respuesta formal bajo ese marco

### 4.2 Queja formal

Usar cuando:

- hay mala atención, irregularidad, incumplimiento o conducta reprochable y el objetivo principal es dejar inconformidad formal y pedir intervención

Minimos:

- conducta o hecho que genera la queja
- fecha o periodo
- entidad o funcionario involucrado
- efecto para el usuario
- solicitud de revisión o corrección

### 4.3 Reclamo administrativo

Usar cuando:

- el usuario exige corrección, revisión o solución frente a un acto, servicio o decisión administrativa o contractual no judicial

Minimos:

- actuación o servicio reclamado
- por qué se considera incorrecto o insuficiente
- qué solución pide
- soporte documental si existe

### 4.4 Habeas data

Usar cuando:

- el usuario busca corrección, actualización, supresión o prueba de autorización sobre datos personales

Minimos:

- base de datos o entidad fuente
- dato cuestionado
- qué se pide exactamente: corregir, actualizar, eliminar o informar
- reclamación previa si aplica
- daño actual o riesgo concreto

Regla fuerte:

- no convertir automáticamente cualquier problema de centrales de riesgo en tutela

### 4.5 Recurso de reposicion o apelacion

Usar cuando:

- existe una decisión previa recurrible
- el usuario está dentro del término o al menos puede justificar situación sobre el término

Minimos:

- acto o decisión recurrida
- fecha de notificación o conocimiento
- errores o razones de inconformidad
- lo que se pide al resolver el recurso

Bloqueo:

- si no existe acto recurrible identificable

### 4.6 Queja disciplinaria

Usar cuando:

- se denuncia conducta de servidor o funcionario público con posible relevancia disciplinaria

Minimos:

- funcionario o dependencia
- hechos verificables
- fecha o periodo
- soporte o testigos si existen
- petición de investigación

Regla:

- no confundir con denuncia penal, petición o simple queja de servicio

### 4.7 Accion de cumplimiento

Usar cuando:

- el usuario busca que una autoridad cumpla una norma con fuerza obligatoria o un acto administrativo claro y exigible

Minimos:

- norma o acto incumplido
- autoridad obligada
- requerimiento previo cuando proceda
- incumplimiento concreto

Bloqueo:

- si no hay deber claro, expreso y exigible

### 4.8 Impugnacion de tutela

Usar cuando:

- existe fallo de tutela de primera instancia y el usuario busca controvertirlo

Minimos:

- fecha del fallo
- sentido de la decisión
- errores concretos del fallo
- puntos no valorados o mal valorados
- lo que se pide en segunda instancia

### 4.9 Incidente de desacato

Usar cuando:

- ya existe fallo o orden de tutela
- la autoridad o particular obligado incumple total o parcialmente

Minimos:

- copia o datos del fallo
- orden concreta incumplida
- pruebas del incumplimiento
- fechas posteriores al fallo

Bloqueo:

- si todavía no existe orden judicial identificable

Calidad reforzada:

- debe dirigirse al mismo juez que conocio la tutela en primera instancia
- debe identificar el fallo, fecha y orden incumplida
- debe explicar el incumplimiento con hechos posteriores al fallo
- debe pedir simultaneamente sancion y cumplimiento inmediato

### 4.11 Requisitos reforzados de impugnacion de tutela

- debe revisar la fecha de notificacion del fallo
- debe identificar las razones exactas por las que el juez nego o limito la tutela
- debe contraargumentar cada razon relevante del fallo
- debe aportar pruebas nuevas si la debilidad del primer fallo fue probatoria

Bloqueo:

- si no hay fallo identificable
- si el usuario no describe por que el fallo debe revocarse

### 4.12 Mapa inicial de autoridades y canales por tipo de queja o reclamo

- Supersalud: salud y EPS
- Superfinanciera: bancos, seguros, pensiones
- SIC datos: habeas data y proteccion de datos
- SIC consumidor: garantias y publicidad engañosa
- Superservicios: servicios publicos
- Ministerio del Trabajo: asuntos laborales administrativos
- Procuraduria: queja disciplinaria contra servidor publico
- Personeria: defensa ciudadana y acompanamiento

Regla:

- la IA debe distinguir entre documento para entidad origen y documento para autoridad de control

### 4.10 Accion popular

Usar cuando:

- el problema afecta derechos o intereses colectivos y no solo un perjuicio individual

Minimos:

- colectivo afectado
- hecho u omisión
- riesgo o daño colectivo
- autoridad o responsable
- prueba inicial de afectación general

Bloqueo:

- si el caso en realidad es individual y corresponde a tutela, reclamación o petición

## 5. Politica de citas y soporte

- citar primero norma basica aplicable
- citar jurisprudencia solo cuando aporte una regla util al caso
- no citar sentencias de memoria sin soporte verificable
- no llenar el documento de citas si el caso no lo requiere
- la fuerza del documento debe venir de hechos bien planteados + pretensiones bien construidas
- si se cita jurisprudencia, idealmente debe quedar:
  - numero de sentencia
  - año
  - magistrado ponente, si se valida
  - regla juridica aplicable al caso

## 6. Intake recomendado para la IA

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

Adicionalmente, debe existir intake especifico por producto. No basta una sola caja de texto para todo el sistema.

## 7. QA minimo antes de entregar al cliente

- el documento identifica sujeto activo y pasivo
- los hechos tienen secuencia
- las pretensiones se pueden cumplir o negar de forma concreta
- no hay contradicciones internas
- no hay citas inventadas
- el remedio escogido coincide con el caso
- si es tutela, hay una justificacion razonable de procedencia
- si es derecho de peticion, la solicitud puede responderse de fondo
- si es recurso, existe decision recurrible
- si es desacato, existe orden judicial incumplida
- si es accion de cumplimiento, existe deber claro y exigible
- si es accion popular, el daño es realmente colectivo
- si es tutela, el documento no se siente como una carta informal sino como una accion constitucional completa
- si es derecho de peticion, el destinatario podria responder de fondo sin adivinar lo que se pide

## 8. Implicaciones para producto

- el formulario de intake no puede ser solo texto libre
- debe haber preguntas dinamicas por tipo de caso
- la IA necesita checklists de suficiencia antes de generar
- algunas salidas deben quedar en estado `insuficiente informacion`
- la app debe preferir pedir un dato mas antes que entregar una tutela debil

## 9. Fuentes oficiales base

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

Pendientes de respaldo oficial especifico para ampliar esta matriz:

- recursos administrativos
- queja disciplinaria
- accion de cumplimiento
- accion popular
- habeas data y protección de datos
- desacato e impugnacion

## 10. Estado

Esto es una matriz inicial. Falta convertirla en:

- prompts estructurados
- validaciones de intake
- reglas por categoria
- reglas por producto completo
- pruebas con casos reales anonimizados
- criterios de scoring de calidad de salida

Fuente adicional ya incorporada:

- Documento local del usuario: `123tutela_Requisitos_Juridicos_Documentos_Calidad.docx`
