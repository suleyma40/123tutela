CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    document_number TEXT,
    phone TEXT,
    city TEXT,
    department TEXT,
    address TEXT,
    role TEXT NOT NULL DEFAULT 'citizen',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE app_users ADD COLUMN IF NOT EXISTS document_number TEXT;
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS department TEXT;
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'citizen';
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

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
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE business_rules ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::JSONB;

CREATE TABLE IF NOT EXISTS conocimiento_legal (
    id BIGSERIAL PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    contenido JSONB NOT NULL,
    fuente TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS casos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES app_users(id),
    usuario_nombre TEXT NOT NULL,
    usuario_email TEXT NOT NULL,
    usuario_documento TEXT,
    usuario_telefono TEXT,
    usuario_ciudad TEXT,
    usuario_departamento TEXT,
    usuario_direccion TEXT,
    workflow_type TEXT NOT NULL DEFAULT 'reclamacion',
    categoria TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    attachments JSONB NOT NULL DEFAULT '[]'::JSONB,
    facts JSONB NOT NULL DEFAULT '{}'::JSONB,
    legal_analysis JSONB NOT NULL DEFAULT '{}'::JSONB,
    routing JSONB NOT NULL DEFAULT '{}'::JSONB,
    prerequisites JSONB NOT NULL DEFAULT '[]'::JSONB,
    warnings JSONB NOT NULL DEFAULT '[]'::JSONB,
    manual_contact JSONB NOT NULL DEFAULT '{}'::JSONB,
    submission_summary JSONB NOT NULL DEFAULT '{}'::JSONB,
    recommended_action TEXT,
    strategy_text TEXT,
    generated_document TEXT,
    payment_status TEXT NOT NULL DEFAULT 'pendiente',
    payment_reference TEXT,
    estado TEXT NOT NULL DEFAULT 'borrador',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE casos ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_nombre TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_email TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_documento TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_telefono TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_ciudad TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_departamento TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS usuario_direccion TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS workflow_type TEXT NOT NULL DEFAULT 'reclamacion';
ALTER TABLE casos ADD COLUMN IF NOT EXISTS categoria TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS attachments JSONB NOT NULL DEFAULT '[]'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS facts JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS legal_analysis JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS routing JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS prerequisites JSONB NOT NULL DEFAULT '[]'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS warnings JSONB NOT NULL DEFAULT '[]'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS manual_contact JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS submission_summary JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS recommended_action TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS strategy_text TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS generated_document TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS payment_status TEXT NOT NULL DEFAULT 'pendiente';
ALTER TABLE casos ADD COLUMN IF NOT EXISTS payment_reference TEXT;
ALTER TABLE casos ADD COLUMN IF NOT EXISTS estado TEXT NOT NULL DEFAULT 'borrador';
ALTER TABLE casos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'casos' AND column_name = 'tipo_problema'
    ) THEN
        EXECUTE $sql$
            UPDATE casos
            SET categoria = COALESCE(categoria, tipo_problema, 'General')
            WHERE categoria IS NULL
        $sql$;
    ELSE
        UPDATE casos
        SET categoria = COALESCE(categoria, 'General')
        WHERE categoria IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'casos' AND column_name = 'diagnostico_ia'
    ) THEN
        EXECUTE $sql$
            UPDATE casos
            SET descripcion = COALESCE(descripcion, diagnostico_ia, 'Caso importado desde version previa')
            WHERE descripcion IS NULL
        $sql$;
    ELSE
        UPDATE casos
        SET descripcion = COALESCE(descripcion, 'Caso importado desde version previa')
        WHERE descripcion IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'casos' AND column_name = 'estado_envio'
    ) THEN
        EXECUTE $sql$
            UPDATE casos
            SET estado = COALESCE(estado, estado_envio, 'borrador')
            WHERE estado IS NULL
        $sql$;
    ELSE
        UPDATE casos
        SET estado = COALESCE(estado, 'borrador')
        WHERE estado IS NULL;
    END IF;
END $$;

UPDATE casos
SET payment_status = COALESCE(payment_status, 'pendiente')
WHERE payment_status IS NULL;

UPDATE casos
SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

CREATE TABLE IF NOT EXISTS case_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES casos(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES app_users(id),
    file_kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'attached',
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    relative_path TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submission_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    destination_name TEXT,
    destination_contact TEXT,
    subject TEXT,
    cc JSONB NOT NULL DEFAULT '[]'::JSONB,
    status TEXT NOT NULL,
    radicado TEXT,
    response_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL DEFAULT 'system',
    actor_id UUID,
    payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL DEFAULT 'wompi',
    environment TEXT NOT NULL DEFAULT 'sandbox',
    product_code TEXT NOT NULL,
    product_name TEXT NOT NULL,
    include_filing BOOLEAN NOT NULL DEFAULT FALSE,
    amount_cop INTEGER NOT NULL,
    amount_in_cents BIGINT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'COP',
    reference TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    provider_transaction_id TEXT,
    provider_status TEXT,
    checkout_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    webhook_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_casos_user_id ON casos(user_id);
CREATE INDEX IF NOT EXISTS idx_casos_estado ON casos(estado);
CREATE INDEX IF NOT EXISTS idx_casos_created_at ON casos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_case_files_case_id ON case_files(case_id);
CREATE INDEX IF NOT EXISTS idx_case_files_uploaded_by ON case_files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_submission_attempts_case_id ON submission_attempts(case_id);
CREATE INDEX IF NOT EXISTS idx_case_events_case_id ON case_events(case_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_case_id ON payment_orders(case_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_user_id ON payment_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_reference ON payment_orders(reference);
CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status);
CREATE INDEX IF NOT EXISTS idx_payment_orders_provider_transaction_id ON payment_orders(provider_transaction_id);
