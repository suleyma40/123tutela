# Plan de Lanzamiento Salud

Objetivo: usar este documento como checklist operativo para abrir `123tutela` con alcance exclusivo en `salud`, siguiendo un orden de ejecucion claro.

Regla de uso:

- No abrir trafico amplio hasta completar todos los items `Bloqueante`.
- Los items `Importante` deben cerrarse antes o durante el soft launch controlado.
- Los items `Post-lanzamiento` no frenan la salida inicial.
- Cada item debe marcarse solo cuando exista evidencia real de cierre.

## Tabla de seguimiento

| ID | Frente | Tarea | Prioridad | Responsable sugerido | Estado | Evidencia de cierre |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Comercial/Legal | Cerrar nombre visible, descripcion exacta y alcance de cada producto de salud | Bloqueante | Producto + Legal | Pendiente | Copy final aprobado en landing, wizard, checkout y dashboard |
| 2 | Comercial/Legal | Confirmar precios oficiales de salud y que incluye cada opcion (`solo documento`, `documento + radicacion`) | Bloqueante | Founders + Producto | Pendiente | Tabla oficial de precios y alcance publicada en frontend |
| 3 | Comercial/Legal | Cerrar texto legal previo al pago y promesa comercial sin sobreventa | Bloqueante | Legal + Producto | Pendiente | Texto aprobado integrado en checkout |
| 4 | Comercial/Legal | Definir y aprobar politica de reembolso para salud | Bloqueante | Founders + Legal | Pendiente | Politica escrita y visible antes o durante compra |
| 5 | Juridico | Hacer ronda final fuerte de pulido de `Accion de tutela en salud` | Bloqueante | Legal/Juridico | Pendiente | Casos de prueba revisados y documento final aprobado |
| 6 | Juridico | Afinar `Impugnacion de tutela` e `Incidente de desacato` como productos de continuidad | Bloqueante | Legal/Juridico | Pendiente | Plantillas y reglas finales aprobadas |
| 7 | Juridico/QA | Confirmar reglas finales de recomendacion entre `Derecho de peticion` y `Tutela` en salud | Bloqueante | Juridico + Backend | Pendiente | Matriz de criterios y pruebas de casos borde pasando |
| 8 | Intake/Producto | Cerrar intake definitivo de salud por etapa (`preview`, `save`, `generate`) | Bloqueante | Producto + Backend | Pendiente | Campos obligatorios y bloqueos documentados y validados |
| 9 | QA | Ejecutar QA end to end con casos reales o anonimizados de cliente | Bloqueante | Operaciones + QA + Backend | Pendiente | Lote de casos completos con resultado documentado |
| 10 | Operaciones | Crear SOP para `pago aprobado no reflejado` | Bloqueante | Operaciones | Pendiente | Procedimiento escrito con pasos y responsable |
| 11 | Operaciones | Crear SOP para `pago rechazado` y conciliacion manual por referencia | Bloqueante | Operaciones | Pendiente | Procedimiento escrito y probado con caso de ejemplo |
| 12 | Operaciones | Crear SOP para `documento bloqueado por QA juridico` | Bloqueante | Operaciones + Juridico | Pendiente | Flujo de escalamiento y respuesta definido |
| 13 | Operaciones | Crear SOP para `radicado sin comprobante visible` y seguimiento manual | Bloqueante | Operaciones | Pendiente | Procedimiento escrito y mensaje tipo para cliente |
| 14 | Pagos | Cerrar trazabilidad completa de Wompi: referencia, transaccion, estado, timestamps y payload | Importante | Backend | Pendiente | Registro auditable completo en base de datos |
| 15 | Pagos | Validar reintentos de webhook sin duplicar efectos | Importante | Backend | Pendiente | Prueba controlada pasando sin duplicados |
| 16 | Radicacion | Confirmar politica final de radicacion por tipo de documento y evidencia al cliente | Importante | Operaciones + Producto | Pendiente | Regla operativa cerrada y visible en panel/correo |
| 17 | UX | Revisar que landing, wizard, checkout y dashboard mantengan foco exclusivo en salud | Importante | Producto + Frontend | Pendiente | Recorrido completo sin mensajes ambiguos |
| 18 | UX | Mejorar presentacion del seguimiento del caso para cliente final | Importante | Producto + Frontend | Pendiente | Panel muestra estado, siguiente paso y evidencia clara |
| 19 | Continuidad | Mostrar `Impugnacion` y `Desacato` solo como continuidad cuando aplique | Importante | Producto + Frontend + Backend | Pendiente | UX y reglas alineadas con ese criterio |
| 20 | Lanzamiento | Abrir soft launch controlado solo para salud y medir conversion, bloqueos y soporte manual | Importante | Founders + Operaciones | Pendiente | Primera cohorte operando con metricas semanales |
| 21 | Canales | Integrar WhatsApp en forma operativa | Post-lanzamiento | Operaciones + Backend | Pendiente | Canal funcionando sin prometer mas de lo que soporta |
| 22 | Automatizacion | Extender automatizaciones con `n8n` o Evolution | Post-lanzamiento | Backend/Ops | Pendiente | Flujos adicionales desplegados y monitoreados |
| 23 | Expansion | Evaluar apertura a nuevas materias distintas de salud | Post-lanzamiento | Founders + Producto | Pendiente | Decision basada en evidencia de estabilidad de salud |

## Orden de ejecucion recomendado

### Fase 1. Cierre de venta y cobertura legal

- [ ] Item 1
- [ ] Item 2
- [ ] Item 3
- [ ] Item 4

### Fase 2. Cierre juridico del producto

- [ ] Item 5
- [ ] Item 6
- [ ] Item 7
- [ ] Item 8

### Fase 3. QA y operacion minima

- [ ] Item 9
- [ ] Item 10
- [ ] Item 11
- [ ] Item 12
- [ ] Item 13

### Fase 4. Robustez antes de abrir

- [ ] Item 14
- [ ] Item 15
- [ ] Item 16
- [ ] Item 17
- [ ] Item 18
- [ ] Item 19

### Fase 5. Salida controlada

- [ ] Item 20

### Fase 6. Despues del lanzamiento

- [ ] Item 21
- [ ] Item 22
- [ ] Item 23

## Criterio practico de salida

No se abre el lanzamiento controlado de `salud` hasta que esten cerrados, como minimo:

- Item 1 al 13 completos
- Trazabilidad base de pagos util para soporte
- Politica operativa de radicacion clara
- Recorrido UX sin ambiguedad de alcance

## Cadencia sugerida de seguimiento

- Revision diaria de estado: 15 minutos
- Revision de bloqueantes: al inicio y al cierre del dia
- Revision ejecutiva: una vez por semana con decision de `seguir`, `bloquear` o `abrir soft launch`

## Decision semanal

Usar esta plantilla al cierre de cada semana:

| Semana | Bloqueantes cerrados | Riesgo principal | Decision |
| --- | --- | --- | --- |
| Semana 1 | 0/13 | Pendiente | Pendiente |

