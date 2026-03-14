from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "123tutela")
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    database_url: str = os.getenv("DATABASE_URL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    knowledge_base_json: str = os.getenv(
        "KNOWLEDGE_BASE_JSON", "knowledge_base/marcos_normativos.json"
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-session")
    cors_origins: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        configured = _split_csv(os.getenv("CORS_ORIGINS"))
        defaults = {
            self.frontend_url,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
        }
        self.cors_origins = [origin for origin in configured or defaults if origin]


settings = Settings()
