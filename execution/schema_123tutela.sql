-- Esquema de Base de Datos para 123tutela 🇨🇴
-- Extensiones requeridas (Ya activadas previamente)
-- CREATE EXTENSION IF NOT EXISTS postgis;
-- CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Tabla de Entidades Destino
CREATE TABLE IF NOT EXISTS entidades (
    id SERIAL PRIMARY KEY,
    modulo TEXT,
    paso_flujo TEXT,
    nombre_entidad TEXT NOT NULL,
    canal_envio TEXT,
    contacto_envio TEXT, -- URL, Correo o Teléfono
    genera_radicado BOOLEAN DEFAULT FALSE,
    plazo_respuesta TEXT,
    observaciones TEXT,
    automatizable BOOLEAN DEFAULT TRUE,
    prioridad INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Juzgados (con soporte PostGIS)
CREATE TABLE IF NOT EXISTS juzgados (
    id SERIAL PRIMARY KEY,
    departamento TEXT,
    municipio TEXT,
    tipo_oficina TEXT,
    correo_reparto TEXT,
    correo_alternativo TEXT,
    tipo_tutela TEXT,
    asunto_recomendado TEXT,
    plataforma_oficial TEXT,
    url_referencia TEXT,
    codigo_interno TEXT UNIQUE,
    prioridad TEXT,
    notas TEXT,
    geom GEOMETRY(Point, 4326), -- Para ubicación geográfica si se requiere
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Base de Conocimiento Legal (con soporte PGVector)
CREATE TABLE IF NOT EXISTS conocimiento_legal (
    id SERIAL PRIMARY KEY,
    titulo TEXT,
    contenido TEXT,
    embedding VECTOR(1536), -- Para modelos de OpenAI/Gemini (ajustar dimensión si es necesario)
    fuente TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Registro de Casos y Trámites
CREATE TABLE IF NOT EXISTS casos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_nombre TEXT NOT NULL,
    usuario_email TEXT NOT NULL,
    usuario_ciudad TEXT,
    tipo_problema TEXT, -- Salud, Habeas Data, etc.
    diagnostico_ia TEXT,
    estado_pago BOOLEAN DEFAULT FALSE,
    documento_url TEXT,
    estado_envio TEXT DEFAULT 'pendiente', -- pendiente, enviado, error
    fecha_radicacion TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
