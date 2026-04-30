from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _derive_default_origins(frontend_url: str, backend_url: str) -> list[str]:
    app_url = os.getenv("APP_URL", "")
    root_domain = os.getenv("ROOT_DOMAIN", "")
    frontend_domain = os.getenv("FRONTEND_DOMAIN", "")

    candidates = {
        frontend_url,
        app_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    }

    for domain in {root_domain.strip(), frontend_domain.strip()}:
        if not domain:
            continue
        candidates.add(f"https://{domain}")
        candidates.add(f"https://www.{domain}")
        candidates.add(f"http://{domain}")
        candidates.add(f"http://www.{domain}")

    candidates.discard(backend_url)
    return [origin for origin in candidates if origin]


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "123tutela")
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    database_url: str = os.getenv("DATABASE_URL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-0")
    knowledge_base_json: str = os.getenv("KNOWLEDGE_BASE_JSON", "knowledge_base/marcos_normativos.json")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-session")
    uploads_dir: str = os.getenv("UPLOADS_DIR", str(ROOT / ".tmp" / "uploads"))
    wompi_environment: str = os.getenv("WOMPI_ENVIRONMENT", "sandbox")
    wompi_public_key: str = os.getenv("WOMPI_PUBLIC_KEY", "")
    wompi_integrity_secret: str = os.getenv("WOMPI_INTEGRITY_SECRET", "")
    wompi_event_secret: str = os.getenv("WOMPI_EVENT_SECRET", "")
    wompi_payment_redirect_url: str = os.getenv("WOMPI_PAYMENT_REDIRECT_URL", "http://localhost:5173/pago/resultado")
    wompi_widget_url: str = os.getenv("WOMPI_WIDGET_URL", "https://checkout.wompi.co/widget.js")
    notification_from_email: str = os.getenv("NOTIFICATION_FROM_EMAIL", "")
    notification_reply_to: str = os.getenv("NOTIFICATION_REPLY_TO", "")
    notification_provider: str = os.getenv("NOTIFICATION_PROVIDER", "resend")
    radications_email: str = os.getenv("RADICATIONS_EMAIL", "radicaciones@123tutelaapp.com")
    support_email: str = os.getenv("SUPPORT_EMAIL", "soporte@123tutelaapp.com")
    notifications_email: str = os.getenv("NOTIFICATIONS_EMAIL", "notificaciones@123tutelaapp.com")
    qa_test_email: str = os.getenv("QA_TEST_EMAIL", "su-ley23@hotmail.com")
    qa_test_radicado_email: str = os.getenv("QA_TEST_RADICADO_EMAIL", "su-ley23@hotmail.com")
    qa_test_emails: list[str] = None  # type: ignore[assignment]
    n8n_whatsapp_webhook_url: str = os.getenv("N8N_WHATSAPP_WEBHOOK_URL", "")
    n8n_ops_webhook_url: str = os.getenv("N8N_OPS_WEBHOOK_URL", "")
    evolution_base_url: str = os.getenv("EVOLUTION_BASE_URL", "")
    evolution_api_key: str = os.getenv("EVOLUTION_API_KEY", "")
    evolution_instance: str = os.getenv("EVOLUTION_INSTANCE", "")
    evolution_api_version: str = os.getenv("EVOLUTION_API_VERSION", "v2")
    notification_smtp_host: str = os.getenv("NOTIFICATION_SMTP_HOST", "")
    notification_smtp_port: int = int(os.getenv("NOTIFICATION_SMTP_PORT", "587"))
    notification_smtp_user: str = os.getenv("NOTIFICATION_SMTP_USER", "")
    notification_smtp_password: str = os.getenv("NOTIFICATION_SMTP_PASSWORD", "")
    radications_smtp_user: str = os.getenv("RADICATIONS_SMTP_USER", "")
    radications_smtp_password: str = os.getenv("RADICATIONS_SMTP_PASSWORD", "")
    notification_smtp_use_ssl: bool = os.getenv("NOTIFICATION_SMTP_USE_SSL", "false").lower() == "true"
    notification_smtp_use_starttls: bool = os.getenv("NOTIFICATION_SMTP_USE_STARTTLS", "true").lower() == "true"
    internal_admin_emails: list[str] = None  # type: ignore[assignment]
    cors_origins: list[str] = None  # type: ignore[assignment]
    trusted_hosts: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        configured = _split_csv(os.getenv("CORS_ORIGINS"))
        defaults = _derive_default_origins(self.frontend_url, self.backend_url)
        self.cors_origins = [origin for origin in configured or defaults if origin]
        internal_configured = {email.lower() for email in _split_csv(os.getenv("INTERNAL_ADMIN_EMAILS"))}
        internal_defaults = {"mariibpa25@gmail.com", "su-ley23@hotmail.com"}
        self.internal_admin_emails = sorted(email for email in (internal_configured or internal_defaults) if email)
        qa_defaults = {self.qa_test_email.strip().lower(), "mariibpa25@gmail.com"}
        qa_configured = {email.lower() for email in _split_csv(os.getenv("QA_TEST_EMAILS"))}
        self.qa_test_emails = sorted(email for email in (qa_configured or qa_defaults) if email)
        trusted = _split_csv(os.getenv("TRUSTED_HOSTS"))
        if trusted:
            self.trusted_hosts = trusted
        else:
            self.trusted_hosts = ["localhost", "127.0.0.1", "123tutelaapp.com", "*.123tutelaapp.com"]


settings = Settings()
