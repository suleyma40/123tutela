ALTER TABLE casos ADD COLUMN IF NOT EXISTS public_token TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS casos_public_token_key ON casos (public_token) WHERE public_token IS NOT NULL;

ALTER TABLE payment_orders ALTER COLUMN user_id DROP NOT NULL;
