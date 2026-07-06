"""Application configuration. Single source for all env-driven settings.

All secrets/credentials are read from the environment. Never hardcode secrets.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    app_name: str = "Nexus"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = True
    api_prefix: str = "/api"

    # --- Database ---
    # async driver, e.g. postgresql+asyncpg://user:pass@host/db
    database_url: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexus"

    # --- Redis / queue ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Security ---
    # 32-byte urlsafe base64 key for Fernet credential encryption. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = "dev-only-CHANGE-ME-generate-a-real-fernet-key=="
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Firebase (auth) ---
    # Path to service-account json, OR set FIREBASE_CREDENTIALS_JSON with inline json.
    firebase_project_id: str = ""
    firebase_credentials_path: str = ""
    firebase_credentials_json: str = ""
    # When true (local dev) skip real Firebase verification and trust a dev header.
    auth_dev_bypass: bool = True

    # --- Engine limits ---
    run_max_seconds: int = 300
    node_default_timeout_seconds: int = 60
    node_default_max_attempts: int = 3
    delay_inline_max_seconds: int = 300
    max_executions_per_hour: int = 100

    # --- AI (Gemini) ---
    # System-level Gemini key used for workflow generation when user hasn't provided one.
    # Get a free key at aistudio.google.com
    gemini_api_key: str = ""

    # --- OAuth providers ---
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # Base URL for OAuth callbacks (e.g. https://api.nexus.app or http://localhost:8000)
    api_base_url: str = "http://localhost:8000"

    @property
    def is_local(self) -> bool:
        return self.environment == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
