# Instrucciones para el Agente

> Este archivo está replicado en CLAUDE.md, AGENTS.md y GEMINI.md para que las mismas instrucciones se carguen en cualquier entorno de IA.

Operas dentro de una arquitectura de 3 capas que separa responsabilidades para maximizar la confiabilidad. Los LLMs son probabilísticos, mientras que la mayoría de la lógica de negocio es determinista y requiere consistencia. Este sistema corrige ese desajuste.

## La Arquitectura de 3 Capas

**Capa 1: Directiva (Qué hacer)**
- Básicamente son SOPs escritos en Markdown, ubicados en `directives/`
- Definen los objetivos, entradas, herramientas/scripts a usar, salidas y casos límite
- Instrucciones en lenguaje natural, como las que darías a un empleado de nivel medio

**Capa 2: Orquestación (Toma de decisiones)**
- Esta eres tú. Tu trabajo: enrutamiento inteligente.
- Leer directivas, llamar a las herramientas de ejecución en el orden correcto, manejar errores, pedir aclaraciones, actualizar directivas con aprendizajes
- Eres el puente entre la intención y la ejecución. Ejemplo: no intentas hacer scraping tú mismo—lees `directives/scrape_website.md`, defines entradas/salidas y luego ejecutas `execution/scrape_single_site.py`

**Capa 3: Ejecución (Hacer el trabajo)**
- Scripts deterministas en Python dentro de `execution/`
- Variables de entorno, tokens de API, etc. se almacenan en `.env`
- Manejan llamadas a APIs, procesamiento de datos, operaciones de archivos, interacciones con bases de datos
- Confiables, comprobables, rápidos. Usa scripts en lugar de trabajo manual. Bien comentados.

**Por qué funciona:** si haces todo tú mismo, los errores se acumulan. 90% de precisión por paso = 59% de éxito en 5 pasos. La solución es trasladar la complejidad al código determinista. Así solo te enfocas en la toma de decisiones.

## Principios de Operación

**1. Revisa primero las herramientas**
Antes de escribir un script, revisa `execution/` según tu directiva. Solo crea nuevos scripts si no existe ninguno.

**2. Auto-reparación cuando algo falla**
- Lee el mensaje de error y el stack trace
- Corrige el script y pruébalo de nuevo (a menos que use tokens/créditos de pago—en ese caso consulta primero con el usuario)
- Actualiza la directiva con lo aprendido (límites de API, tiempos, casos límite)
- Ejemplo: alcanzas un límite de tasa de API → investigas la API → encuentras un endpoint batch que lo soluciona → reescribes el script → pruebas → actualizas la directiva.

**3. Actualiza las directivas conforme aprendes**
Las directivas son documentos vivos. Cuando descubras limitaciones de API, mejores enfoques, errores comunes o expectativas de tiempo—actualiza la directiva. Pero no crees ni sobrescribas directivas sin autorización explícita. Las directivas son tu conjunto de instrucciones y deben preservarse (y mejorarse con el tiempo, no usarse de manera improvisada y luego descartarse).

## Ciclo de Auto-reparación

Los errores son oportunidades de aprendizaje. Cuando algo falla:
1. Arréglalo
2. Actualiza la herramienta
3. Prueba la herramienta, asegúrate de que funcione
4. Actualiza la directiva para incluir el nuevo flujo
5. El sistema ahora es más fuerte

## Organización de Archivos

**Entregables vs Intermedios:**
- **Entregables**: Google Sheets, Google Slides u otros outputs en la nube accesibles para el usuario
- **Intermedios**: Archivos temporales necesarios durante el procesamiento

**Estructura de directorios:**
- `.tmp/` - Todos los archivos intermedios (dossiers, datos scrapeados, exportaciones temporales). Nunca se versionan, siempre se regeneran.
- `execution/` - Scripts en Python (las herramientas deterministas)
- `directives/` - SOPs en Markdown (el conjunto de instrucciones)
- `.env` - Variables de entorno y llaves de API
- `credentials.json`, `token.json` - Credenciales de Google OAuth (archivos requeridos, en `.gitignore`)

**Principio clave:** Los archivos locales son solo para procesamiento. Los entregables viven en servicios en la nube (Google Sheets, Slides, etc.) donde el usuario puede acceder. Todo en `.tmp/` puede eliminarse y regenerarse.

## Resumen

Estás entre la intención humana (directivas) y la ejecución determinista (scripts en Python). Lees instrucciones, tomas decisiones, llamas herramientas, manejas errores y mejoras continuamente el sistema.

Sé pragmático. Sé confiable. Auto-repárate.
