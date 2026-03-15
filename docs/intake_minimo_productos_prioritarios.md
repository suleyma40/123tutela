# Intake Minimo de Productos Prioritarios

Objetivo: definir qué debe pedir la app antes de permitir la generación de documentos de alta sensibilidad jurídica. Este documento aterriza la matriz de calidad en preguntas operativas.

## 1. Principio general

No debe existir una sola caja de texto para todos los productos. El intake debe mezclar:

- campos estructurados
- texto libre guiado
- preguntas condicionales
- bloqueos por insuficiencia

La app debe preferir pedir un dato adicional antes que generar un documento débil.

## 2. Accion de tutela

### 2.1 Campos minimos obligatorios

- nombre completo del accionante
- documento de identidad
- ciudad y departamento
- entidad, autoridad o particular accionado
- categoria del caso
- relato cronologico de hechos
- fecha o periodo aproximado de ocurrencia
- derecho o necesidad afectada
- daño actual o riesgo concreto
- que solicita exactamente

### 2.2 Campos dinamicos recomendados

Salud / EPS:
- EPS
- IPS o clinica
- diagnostico o condicion medica
- orden medica o tratamiento requerido
- fecha de negativa, demora o barrera
- si existe urgencia manifiesta

Laboral:
- tipo de relacion laboral
- fecha del despido o acto cuestionado
- si existe afectacion a minimo vital
- si hay estabilidad reforzada o condicion especial

Datos / Habeas data:
- entidad fuente o base de datos
- fecha de reclamacion previa
- respuesta recibida
- daño actual por el reporte o dato

Servicios / Consumidor:
- empresa o prestador
- reclamacion previa
- fecha de corte, cobro o incumplimiento
- afectacion concreta a derecho fundamental

### 2.3 Texto libre guiado

Prompt sugerido para el usuario:

"Cuéntanos qué pasó, en qué fechas, qué pediste antes, qué te respondió la entidad y por qué hoy necesitas protección urgente. Escribe hechos concretos, no opiniones generales."

### 2.4 Validaciones minimas

Bloquear generación si falta alguno de estos puntos:

- no se identifica el accionado
- el relato tiene menos de contexto mínimo útil
- no hay daño actual o riesgo explicado
- no existe pretensión clara

### 2.5 Alertas que deben disparar repregunta

- parece haber vía previa no agotada y no hay urgencia
- el usuario menciona perjuicio pero no lo concreta
- la entidad accionada no está clara
- hay contradicción temporal
- la solicitud al juez es ambigua

## 3. Derecho de peticion

### 3.1 Campos minimos obligatorios

- nombre completo
- documento de identidad
- correo o dirección para respuesta
- destinatario o entidad
- tipo de petición:
  - información
  - documentos
  - consulta
  - interés particular o general
- objeto exacto de la solicitud
- hechos que justifican la petición

### 3.2 Campos adicionales que mejoran calidad

- numero de caso, contrato, afiliacion o referencia
- fecha de hechos
- peticiones numeradas que espera obtener
- anexos disponibles

### 3.3 Texto libre guiado

Prompt sugerido:

"Describe qué necesitas que la entidad responda, entregue o haga, por qué lo solicitas y qué antecedentes existen. Si ya escribiste antes, indícalo."

### 3.4 Validaciones minimas

Bloquear si:

- no hay destinatario
- no hay canal de respuesta del usuario
- no se entiende qué pide exactamente
- los hechos son insuficientes para responder de fondo

### 3.5 Mejora automatica sugerida

La app debe convertir la petición en:

- objeto claro
- hechos breves
- solicitudes numeradas
- cierre con canal de respuesta

## 4. Habeas data

### 4.1 Campos minimos obligatorios

- nombre completo
- documento de identidad
- entidad fuente, operador o base de datos
- dato que quiere corregir, actualizar o eliminar
- motivo de la solicitud
- qué pide exactamente:
  - corrección
  - actualización
  - supresión
  - prueba de autorización
- canal de respuesta

### 4.2 Campos recomendados

- fecha de reporte o hallazgo del dato
- evidencia del dato erróneo
- reclamacion previa y respuesta, si ya existe
- daño actual generado por el tratamiento del dato

### 4.3 Texto libre guiado

Prompt sugerido:

"Explica qué dato está mal, dónde aparece, desde cuándo lo conoces, qué efecto te está causando y qué quieres que la entidad haga exactamente."

### 4.4 Validaciones minimas

Bloquear si:

- no se identifica la entidad que trata el dato
- no se identifica qué dato se discute
- no se define la acción solicitada

### 4.5 Regla juridica importante

Si el usuario quiere tutela directa, la app debe revisar primero si falta reclamacion previa, salvo daño grave o urgencia demostrable.

## 5. Estados operativos sugeridos

Cada intake debería poder cerrar en uno de estos estados:

- `suficiente_para_generar`
- `requiere_mas_datos`
- `riesgo_de_improcedencia`
- `debe_sugerir_otro_producto`

## 6. Lo que sigue

Después de estos tres productos prioritarios, hay que diseñar intake específico para:

- carta formal
- queja formal
- reclamo administrativo
- recurso de reposición o apelación
- queja disciplinaria
- acción de cumplimiento
- impugnación de tutela
- incidente de desacato
- acción popular
