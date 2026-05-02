# Bitacora Go-Live Salud Semana 1

Estado: preparado para iniciar.

## Regla de lanzamiento
- Trafico controlado solo para `salud`.
- Sin apertura de otras materias durante semana 1.

## Corte diario
| Fecha | Casos creados | Pagos aprobados | Expedientes completos | Bloqueos QA | Incidencias pago | Incidencias radicacion | Soporte manual | Decision del dia |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2026-05-02 |  |  |  |  |  |  |  |  |
| 2026-05-03 |  |  |  |  |  |  |  |  |
| 2026-05-04 |  |  |  |  |  |  |  |  |
| 2026-05-05 |  |  |  |  |  |  |  |  |
| 2026-05-06 |  |  |  |  |  |  |  |  |
| 2026-05-07 |  |  |  |  |  |  |  |  |
| 2026-05-08 |  |  |  |  |  |  |  |  |

## Umbrales de control
- Incidencia severa de pago: > 5% de pagos no reflejados en 30 min.
- Incidencia severa de radicacion: > 10% de casos con estado incoherente.
- Bloqueos QA juridico: > 20% de documentos generados.

Si se supera umbral severo:
- congelar incremento de trafico
- aplicar fix
- rerun de QA E2E del bloque afectado
