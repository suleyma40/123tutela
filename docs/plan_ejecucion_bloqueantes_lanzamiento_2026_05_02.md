# Plan de Ejecucion de Bloqueantes de Lanzamiento (2026-05-02)

Objetivo: cerrar en orden los 5 bloqueantes de salida controlada del bloque salud.

## 1) QA juridico final (bloqueante)

Estado de inicio: en ejecucion.

Acciones inmediatas:
- Correr regresion funcional y de flujo:
  - `python -B execution/health_case_regression.py`
  - `python -B execution/health_flow_smoke.py`
- Tomar 10 expedientes anonimizados reales y revisar manualmente:
  - claridad de hechos cronologicos
  - derecho vulnerado bien conectado
  - pretensiones concretas y ejecutables
  - accionado correcto (EPS vs IPS)
  - urgencia/continuidad sin exageracion

Evidencia exigida:
- Acta firmada en `docs/acta_qa_juridica_salud_2026_05_02.md`
- Lista de hallazgos bloqueantes vs warnings
- Decision por tipo de documento: `apto` / `requiere ajuste`

Criterio de cierre:
- 0 hallazgos bloqueantes en muestra final.
- Consistencia en tutela, peticion, impugnacion y desacato.

## 2) Trazabilidad de pagos completa (bloqueante)

Estado de inicio: en ejecucion.

Acciones inmediatas:
- Auditar punta a punta por referencia Wompi:
  - session creada
  - transaccion conciliada
  - webhook recibido
  - estado final de orden/caso
- Validar idempotencia en reintentos de webhook:
  - mismo `transaction_id` no debe duplicar efectos
  - no debe crear doble pago ni doble cambio de estado

Evidencia exigida:
- Reporte en `docs/acta_trazabilidad_pagos_wompi_2026_05_02.md`
- 5 referencias reales/sandbox con:
  - `reference`
  - `transaction_id`
  - timestamps
  - estado final
  - resultado de reintento webhook

Criterio de cierre:
- 100% de casos auditados con trazabilidad completa.
- Reintentos webhook sin duplicidad.

## 3) Radicacion y evidencia operativa (bloqueante)

Estado de inicio: en ejecucion.

Acciones inmediatas:
- Cerrar matriz final por documento:
  - canal principal
  - fallback
  - comprobante interno guardado
  - comprobante visible al cliente
- Validar en panel que el cliente ve estado operativo correcto.

Evidencia exigida:
- Acta en `docs/acta_radicacion_evidencia_operativa_2026_05_02.md`
- 1 caso por tipo de documento con evidencia de envio/radicado o fallback.

Criterio de cierre:
- Canales y comprobantes definidos y probados en los 4 documentos de salud.

## 4) QA E2E con casos reales/anonimizados (bloqueante)

Estado de inicio: en ejecucion.

Acciones inmediatas:
- Ejecutar corrida formal usando `docs/casos_qa_lanzamiento_salud.md`.
- Registrar resultados en `docs/matriz_ejecucion_qa_lanzamiento_salud.md`.

Evidencia exigida:
- Acta de ejecucion en `docs/acta_qa_e2e_salud_2026_05_02.md`
- Resultado por caso:
  - pasa
  - pasa con observacion
  - no pasa

Criterio de cierre:
- 100% de casos criticos pasan.
- Observaciones no bloqueantes con plan y fecha.

## 5) Go-live controlado (bloqueante de negocio)

Estado de inicio: en ejecucion.

Acciones inmediatas:
- Abrir trafico solo salud.
- Monitoreo semanal fijo de:
  - conversion a pago
  - expedientes incompletos postpago
  - bloqueos de QA juridico
  - incidencias de pago/radicacion
  - casos que requieren soporte manual

Evidencia exigida:
- Bitacora en `docs/bitacora_go_live_salud_semana_1.md`
- Corte semanal con decisiones:
  - mantener
  - ajustar
  - pausar

Criterio de cierre:
- Operacion estable 7 dias sin incidentes severos.
- Errores recurrentes convertidos en regla/validacion.
