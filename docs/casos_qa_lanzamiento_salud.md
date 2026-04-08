# Casos QA Lanzamiento Salud

Objetivo: validar el lanzamiento controlado del bloque de salud con un set corto de casos que cubra entrada, pago, documento, radicacion y seguimiento.

## Regla de uso

Cada caso debe revisarse en estas capas:
- recomendacion inicial correcta
- bloqueo o avance del intake
- producto correcto en pago
- documento correcto al generar
- radicacion o siguiente paso correcto

## Caso 1. Derecho de peticion ordinario a EPS

Nombre corto: `peticion_eps_respuesta_ordinaria`

Escenario:
- usuario pide copia de autorizacion y reprogramacion de cita
- no hay riesgo vital inmediato
- ya hubo solicitud previa sin respuesta clara

Resultado esperado:
- ruta: `Derecho de peticion en salud`
- no debe empujar a tutela de entrada
- debe pedir EPS, fechas, solicitud concreta y soporte basico

Criterio de aprobado:
- preview viable
- producto visible correcto
- documento tipo peticion

## Caso 2. Tutela por continuidad de tratamiento

Nombre corto: `tutela_continuidad_tratamiento`

Escenario:
- menor con tratamiento continuo interrumpido
- orden medica vigente
- barrera actual de EPS

Resultado esperado:
- ruta: `Tutela en salud`
- viabilidad alta
- no bloquear por no tener una via previa adicional si la urgencia ya es actual

Criterio de aprobado:
- recomendacion a tutela
- preguntas finas de urgencia y continuidad
- documento de tutela listo al completar datos

## Caso 3. Tutela improcedente o debil

Nombre corto: `tutela_debil_sin_datos`

Escenario:
- relato vago
- sin EPS clara
- sin diagnostico
- sin tratamiento identificado

Resultado esperado:
- no debe generar tutela fuerte
- debe pedir mas datos
- puede quedarse en requerimiento de informacion o ruta conservadora

Criterio de aprobado:
- bloqueo de generacion
- preguntas faltantes visibles

## Caso 4. Impugnacion con fallo adverso legible

Nombre corto: `impugnacion_fallo_negado`

Escenario:
- usuario aporta fallo de tutela negado
- la IA puede leer juzgado, fecha y decision
- existe motivo concreto de inconformidad

Resultado esperado:
- ruta: `Impugnacion`
- producto visible correcto
- no permitir avanzar sin fallo adjunto

Criterio de aprobado:
- con fallo legible avanza
- sin fallo no avanza
- documento de impugnacion usa decision y juzgado del fallo

## Caso 5. Desacato con fallo favorable incumplido

Nombre corto: `desacato_incumplimiento_fallo`

Escenario:
- usuario aporta fallo favorable
- existe orden concreta incumplida
- la EPS no cumple en el plazo fijado

Resultado esperado:
- ruta: `Desacato`
- no permitir avanzar sin fallo adjunto
- siguiente paso posterior debe enfocarse en cumplimiento

Criterio de aprobado:
- con fallo legible avanza
- sin fallo no avanza
- documento usa orden judicial incumplida

## Caso 6. Pago aprobado y documento desbloqueado

Nombre corto: `pago_aprobado_documento_activo`

Escenario:
- orden de pago creada
- pago aprobado por webhook o conciliacion

Resultado esperado:
- expediente en `pagado`
- referencia visible
- documento desbloqueado

Criterio de aprobado:
- panel muestra estado confirmado
- timeline muestra orden y confirmacion
- siguiente paso lleva a documento

## Caso 7. Pago rechazado o con error

Nombre corto: `pago_rechazado_o_error`

Escenario:
- intento de pago termina en `rechazado` o `error`

Resultado esperado:
- no desbloquear documento
- mostrar mensaje claro
- conservar referencia trazable

Criterio de aprobado:
- panel distingue `rechazado` o `error`
- timeline muestra evento de pago
- usuario entiende que debe reintentar o conciliar

## Caso 8. Seguimiento despues del radicado

Nombre corto: `seguimiento_post_radicado`

Escenario:
- documento ya radicado
- cliente reporta llamada, correo o requerimiento nuevo

Resultado esperado:
- novedad se registra en expediente
- panel muestra ultimo reporte
- panel muestra que vigilar y cuando cambia el siguiente paso

Criterio de aprobado:
- `follow-up` queda visible
- siguiente paso es entendible
- si aplica, se sugiere impugnacion o desacato

## Cobertura minima por producto

- `Derecho de peticion`: caso 1
- `Tutela`: casos 2 y 3
- `Impugnacion`: caso 4
- `Desacato`: caso 5
- `Pagos`: casos 6 y 7
- `Seguimiento`: caso 8

## Secuencia recomendada de corrida

1. Caso 1
2. Caso 2
3. Caso 3
4. Caso 4
5. Caso 5
6. Caso 6
7. Caso 7
8. Caso 8

## Criterio de salida de QA corto

El bloque salud puede considerarse listo para soft launch cuando:
- los 5 casos juridicos pasan sin desviar al producto equivocado
- los 2 casos de pago muestran estado y accion correcta
- el caso de seguimiento deja claro el siguiente paso
- no aparece una regresion en `tutela en salud`

## Documento para ejecutar

Usar esta hoja de control al correr los casos:
- `docs/matriz_ejecucion_qa_lanzamiento_salud.md`
