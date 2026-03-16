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
    notification_smtp_host: str = os.getenv("NOTIFICATION_SMTP_HOST", "")
    notification_smtp_port: int = int(os.getenv("NOTIFICATION_SMTP_PORT", "587"))
    notification_smtp_user: str = os.getenv("NOTIFICATION_SMTP_USER", "")
    notification_smtp_password: str = os.getenv("NOTIFICATION_SMTP_PASSWORD", "")
    notification_smtp_use_ssl: bool = os.getenv("NOTIFICATION_SMTP_USE_SSL", "false").lower() == "true"
    notification_smtp_use_starttls: bool = os.getenv("NOTIFICATION_SMTP_USE_STARTTLS", "true").lower() == "true"
    internal_admin_emails: list[str] = None  # type: ignore[assignment]
    cors_origins: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        configured = _split_csv(os.getenv("CORS_ORIGINS"))
        defaults = _derive_default_origins(self.frontend_url, self.backend_url)
        self.cors_origins = [origin for origin in configured or defaults if origin]
        self.internal_admin_emails = [email.lower() for email in _split_csv(os.getenv("INTERNAL_ADMIN_EMAILS"))]


settings = Settings()
