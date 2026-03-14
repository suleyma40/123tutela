CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entidades (
    id BIGSERIAL PRIMARY KEY,
    modulo TEXT,
    paso_flujo TEXT,
    nombre_entidad TEXT NOT NULL,
    canal_envio TEXT,
    contacto_envio TEXT,
    genera_radicado BOOLEAN DEFAULT FALSE,
    plazo_respuesta TEXT,
    observaciones TEXT,
    automatizable BOOLEAN DEFAULT TRUE,
    prioridad INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT entidades_unique_target UNIQUE (nombre_entidad, canal_envio, contacto_envio)
);

CREATE TABLE IF NOT EXISTS juzgados (
    id BIGSERIAL PRIMARY KEY,
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS business_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    action_text TEXT,
    priority TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS casos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    usuario_nombre TEXT NOT NULL,
    usuario_email TEXT NOT NULL,
    usuario_ciudad TEXT,
    usuario_departamento TEXT,
    categoria TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    attachments JSONB NOT NULL DEFAULT '[]'::JSONB,
    facts JSONB NOT NULL DEFAULT '{}'::JSONB,
    legal_analysis JSONB NOT NULL DEFAULT '{}'::JSONB,
    routing JSONB NOT NULL DEFAULT '{}'::JSONB,
    recommended_action TEXT,
    strategy_text TEXT,
    generated_document TEXT,
    estado TEXT NOT NULL DEFAULT 'borrador',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE casos ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_departamento TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS categoria TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS attachments JSONB NOT NULL DEFAULT '[]'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS facts JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS legal_analysis JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS routing JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS recommended_action TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS strategy_text TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS generated_document TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS estado TEXT DEFAULT 'borrador';
ALTER TABLE casos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

UPDATE casos
SET categoria = COALESCE(categoria, tipo_problema, 'General')
WHERE categoria IS NULL;

UPDATE casos
SET descripcion = COALESCE(descripcion, diagnostico_ia, 'Caso importado desde versión previa')
WHERE descripcion IS NULL;

UPDATE casos
SET estado = COALESCE(estado, estado_envio, 'borrador')
WHERE estado IS NULL;

UPDATE casos
SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_casos_user_id ON casos(user_id);
CREATE INDEX IF NOT EXISTS idx_casos_created_at ON casos(created_at DESC);
