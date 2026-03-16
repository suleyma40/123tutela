# Checklist de Arquitectura Legal IA

Objetivo: convertir la nueva arquitectura legal IA en una hoja de control operativa para 123tutela. Esta checklist debe usarse para priorizar desarrollo, QA, validacion juridica, despliegue y mejoras sucesivas del sistema.

Regla maestra:

- no generar documento final sin DX preliminar
- no citar soporte juridico no verificable
- no redactar cuando falten hechos esenciales
- no tratar todos los casos como tutela
- no sacrificar procedencia por velocidad de salida

## 0. Orden de prioridad

### Materias prioritarias

- [ ] Salud + tutela
- [ ] Derecho de peticion
- [ ] Bancos + habeas data

### Criterio de avance

- [ ] No abrir una materia nueva sin tener intake minimo, DX, motor de procedencia, fuentes oficiales, redaccion y QA final de la materia actual
- [ ] Toda mejora transversal debe aplicarse a caso nuevo, expediente activo y regeneracion de documento
- [ ] Toda mejora debe reflejarse en frontend, backend, persistencia y validacion final

## 1. DX gratis y obligatorio

### Salidas minimas del DX

- [ ] Viabilidad preliminar: verde, amarillo, naranja o rojo
- [ ] Tipo de documento sugerido
- [ ] Ruta del caso: A, B o C
- [ ] Nivel de urgencia
- [ ] Nivel de riesgo de improcedencia
- [ ] Lista de datos faltantes criticos
- [ ] Lista de soportes minimos faltantes
- [ ] Recomendacion siguiente: generar, preguntar mas, redirigir o escalar

### Reglas de control

- [ ] El DX debe correr antes de analisis profundo
- [ ] El DX no debe depender de investigacion juridica costosa
- [ ] El DX debe bloquear generacion si el caso es claramente improcedente o insuficiente
- [ ] El DX debe guardar su salida estructurada en base de datos

## 2. Clasificacion operativa del caso

### Ruta A: automatizable

- [ ] Tipo documental claro
- [ ] Hechos suficientes
- [ ] Entidad o destinatario identificable
- [ ] Soporte minimo disponible o razonablemente describible
- [ ] Complejidad juridica baja o media

### Ruta B: requiere preguntas adicionales

- [ ] Faltan fechas
- [ ] Faltan montos, referencias o numeros de caso
- [ ] No esta clara la entidad accionada
- [ ] No esta clara la pretension concreta
- [ ] No esta claro el dano actual o la urgencia

### Ruta C: escalar a revision humana

- [ ] Multiples entidades o responsabilidades cruzadas
- [ ] Alto riesgo de improcedencia
- [ ] Posible conflicto normativo serio
- [ ] Posible caducidad, subsidiariedad o temeridad compleja
- [ ] Materia sancionatoria, patrimonial compleja, providencia judicial o familia compleja

## 3. Asistente del caso transversal

### Reglas generales

- [ ] Debe aparecer en todos los productos prioritarios
- [ ] Debe estar disponible en caso nuevo, expediente activo y regeneracion
- [ ] Debe preguntar solo faltantes relevantes, no formularios eternos
- [ ] Debe guardar cada respuesta como dato estructurado
- [ ] Debe poder repreguntar si detecta contradiccion o vacio critico

### Campos transversales que debe intentar extraer

- [ ] Fecha o periodo de los hechos
- [ ] Entidad o destinatario
- [ ] Pretension concreta
- [ ] Dano actual o riesgo
- [ ] Gestion previa
- [ ] Canal de respuesta
- [ ] Pruebas disponibles
- [ ] Referencia o numero relacionado

### UX minima obligatoria

- [ ] Mostrar ejemplos concretos por materia
- [ ] Mostrar opciones desplegables cuando haya catalogos
- [ ] Prellenar datos ya conocidos del usuario o del expediente
- [ ] Explicar que tipo de prueba puede subir el usuario
- [ ] No depender de una sola caja de texto libre

## 4. Fuentes juridicas verificables

### Jerarquia obligatoria

- [ ] Nivel 1: fuentes oficiales
- [ ] Nivel 2: fuentes secundarias permitidas
- [ ] Nivel 3: fuentes no aptas como sustento principal

### Metadatos minimos por fuente

- [ ] tipo_fuente
- [ ] corporacion o entidad emisora
- [ ] numero o referencia oficial
- [ ] fecha
- [ ] url_verificada
- [ ] extracto_relevante
- [ ] tema_juridico
- [ ] nivel_confiabilidad

### Reglas antifabulacion

- [ ] No inventar sentencias
- [ ] No inventar articulos o extractos
- [ ] No presentar jurisprudencia no verificada como soporte principal
- [ ] Si no hay soporte verificable, advertirlo de forma conservadora
- [ ] Todo soporte usado en documento final debe quedar persistido

## 5. Persistencia del expediente por capas

### Estados minimos del caso

- [ ] caso_creado
- [ ] dx_inicial_completado
- [ ] informacion_incompleta
- [ ] caso_no_viable
- [ ] caso_viable
- [ ] tipo_documento_detectado
- [ ] analisis_juridico_generado
- [ ] investigacion_juridica_generada
- [ ] preguntas_adicionales_requeridas
- [ ] escalar_revision_humana
- [ ] documento_borrador_generado
- [ ] documento_validado
- [ ] documento_entregado
- [ ] documento_radicado_por_usuario
- [ ] cerrado

### Salidas estructuradas minimas

- [ ] dx_result
- [ ] route
- [ ] pending_questions
- [ ] procedencia_preliminar
- [ ] fuentes_verificadas
- [ ] draft_metadata
- [ ] final_validation
- [ ] audit_events

### Regla de arquitectura

- [ ] Cada capa debe leer estado previo estructurado
- [ ] Cada capa debe escribir salida estructurada
- [ ] No depender solo de texto libre para pasar contexto entre capas

## 6. Control de costo y latencia

### Ejecucion por fases

- [ ] DX gratis o de bajo costo
- [ ] Analisis juridico intermedio solo si pasa DX
- [ ] Investigacion juridica solo en casos suficientes y viables
- [ ] Redaccion final solo cuando ya paso controles minimos

### Reglas de ahorro

- [ ] No investigar si faltan hechos esenciales
- [ ] No redactar si la ruta correcta no esta clara
- [ ] No gastar tokens premium en casos rojos o claramente inviables
- [ ] Permitir upsell entre DX, analisis premium y documento estrategico

## 7. Motor de procedencia e improcedencia

### Tutela: controles minimos

- [ ] Legitimacion por activa
- [ ] Legitimacion por pasiva
- [ ] Inmediatez
- [ ] Subsidiariedad
- [ ] Perjuicio irremediable
- [ ] Hecho superado
- [ ] Carencia actual de objeto
- [ ] Temeridad
- [ ] Prueba minima

### Salida estructurada

- [ ] procedencia = alta, media o baja
- [ ] riesgo_improcedencia = bajo, medio o alto
- [ ] causales_detectadas = []
- [ ] faltantes_criticos = []
- [ ] recomendacion = redactar, pedir mas datos, no recomendar o escalar

### Extensiones futuras obligatorias

- [ ] Replicar motor de reglas para derecho de peticion
- [ ] Replicar motor de reglas para habeas data
- [ ] Replicar motor de reglas para reclamacion financiera

## 8. Checklist especifica por materia

### 8.1 Salud + tutela

#### Intake

- [ ] EPS identificada
- [ ] IPS, clinica o prestador si aplica
- [ ] Diagnostico o condicion medica
- [ ] Orden medica o tratamiento requerido
- [ ] Fecha de negativa, demora o barrera
- [ ] Riesgo actual: salud, dolor, agravacion, continuidad del tratamiento
- [ ] Medicamento, procedimiento, cita o insumo identificado
- [ ] Soportes sugeridos: formula, historia clinica, negacion, autorizacion, pantallazo, radicado

#### Procedencia

- [ ] Riesgo real a salud o vida digna
- [ ] Continuidad del tratamiento evaluada
- [ ] Urgencia o perjuicio irremediable evaluado
- [ ] Via previa revisada sin frenar casos urgentes

#### Fuentes oficiales

- [ ] Constitucion art. 86
- [ ] Ley Estatutaria de Salud 1751 de 2015
- [ ] Decreto 2591 de 1991
- [ ] Lineamientos oficiales MinSalud o SuperSalud segun caso
- [ ] Jurisprudencia verificada util y no ornamental

#### QA final

- [ ] Hechos cronologicos claros
- [ ] Derecho a salud correctamente conectado
- [ ] Pretensiones medicas ejecutables
- [ ] No prometer resultado judicial

### 8.2 Derecho de peticion

#### Intake

- [ ] Destinatario identificado
- [ ] Objeto exacto de la peticion
- [ ] Tipo de peticion definido
- [ ] Hechos base suficientes
- [ ] Canal de respuesta del peticionario
- [ ] Referencia o numero de caso si existe
- [ ] Soportes sugeridos: radicado previo, contrato, afiliacion, acto, correo, PDF

#### Procedencia y estructura

- [ ] Solicitudes numeradas y concretas
- [ ] Hechos breves y claros
- [ ] No mezclar queja, tutela y peticion sin justificar
- [ ] Cierre con canal de respuesta correcto

#### Fuentes oficiales

- [ ] Constitucion art. 23
- [ ] Ley 1755 de 2015
- [ ] SUIN o fuente oficial vigente
- [ ] Guias institucionales solo como fuente secundaria

#### QA final

- [ ] El destinatario puede responder de fondo
- [ ] Lo pedido se entiende con precision
- [ ] No hay solicitudes ambiguas o imposibles

### 8.3 Bancos + habeas data

#### Intake

- [ ] Entidad financiera o fuente de datos identificada
- [ ] Producto o dato cuestionado identificado
- [ ] Fecha del primer cobro o reporte
- [ ] Monto o afectacion economica cuando aplique
- [ ] Reclamacion previa y respuesta
- [ ] Dano actual: reporte, cobro, bloqueo, negacion, mora
- [ ] Medio para devolucion o correccion si aplica
- [ ] Soportes sugeridos: extractos, chat, correo, pantallazo, contrato, reporte, radicado

#### Procedencia

- [ ] No disparar tutela si primero corresponde reclamacion o habeas data, salvo urgencia grave
- [ ] Revisar via previa
- [ ] Revisar dano actual o impacto serio
- [ ] Revisar soporte minimo del cobro, reporte o tratamiento de datos

#### Fuentes oficiales

- [ ] Regimen oficial de habeas data aplicable
- [ ] Regimen financiero oficial aplicable
- [ ] SIC, Superfinanciera o fuente oficial segun asunto
- [ ] Jurisprudencia verificada solo si coincide con el punto juridico

#### QA final

- [ ] No usar placeholders como destinatario
- [ ] No repetir palabras crudas del usuario como texto final
- [ ] Solicitudes claras: eliminar, corregir, devolver, responder, actualizar

## 9. Redaccion juridica y calidad del documento

### Reglas de estilo

- [ ] No copiar literalmente la narracion cruda del cliente como salida final
- [ ] Transformar el relato en redaccion formal
- [ ] Ordenar hechos cronologicamente
- [ ] Identificar fallas atribuibles a la entidad
- [ ] Conectar hechos, fundamento y pretensiones
- [ ] Evitar enumerar cada parrafo sin necesidad
- [ ] Mantener solicitudes numeradas solo donde juridicamente aporta valor

### Controles de calidad previos a entrega

- [ ] El documento corresponde al tipo de accion correcto
- [ ] La entidad accionada o destinataria esta clara
- [ ] Los hechos son consistentes y cronologicos
- [ ] Las pretensiones corresponden al caso
- [ ] Las citas usadas fueron verificadas
- [ ] No hay contradiccion entre hechos y solicitudes
- [ ] No se promete un resultado judicial
- [ ] Si el caso es complejo, se advierte necesidad de revision humana

### Salida final

- [ ] apto_para_entrega = si o no
- [ ] Si no, explicar si debe pedir mas datos, corregir o escalar

## 10. QA tecnico y despliegue

### Antes de merge o deploy

- [ ] Probar caso nuevo
- [ ] Probar expediente activo
- [ ] Probar regeneracion
- [ ] Probar caso pagado y no pagado cuando aplique
- [ ] Probar ruta A, B y C
- [ ] Validar que el asistente aparece donde corresponde
- [ ] Validar que el autocomplete funciona
- [ ] Validar que los faltantes cambian por materia
- [ ] Validar que la API no rompe por campos nuevos
- [ ] Validar que CORS y response codes son correctos

### Antes de considerar una materia como lista

- [ ] Tiene intake guiado suficiente
- [ ] Tiene fuentes oficiales verificables
- [ ] Tiene motor minimo de procedencia
- [ ] Tiene documento final juridicamente presentable
- [ ] Tiene validacion final
- [ ] Tiene pruebas reales o simuladas satisfactorias

## 11. Regla de seguimiento

- [ ] Cada avance relevante debe reflejarse en esta checklist
- [ ] Cada materia debe cerrarse con evidencia de pruebas
- [ ] Cada bug recurrente debe convertirse en control o validacion nueva
- [ ] Ninguna mejora debe quedarse solo en el frontend o solo en el backend
