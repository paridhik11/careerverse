"""Application configuration loaded from environment variables."""

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = "AQ.Ab8RN6IuQopD0IlEc_FOJ14OZwfYhvpb8yiyZ7pY_ppdaVi8vA"
    # Empty string → SQLite fallback in app.core.database (local MVP without Postgres).
    database_url: str = ""
    supabase_url: str = ""
    supabase_key: str = ""
    # Empty string → insecure dev-only secret in app.core.security.
    jwt_secret: str = ""
    google_client_id: str = "975859875433-qb73fkkgu8rpnp31ob2vbk7ga20fh1ug.apps.googleusercontent.com"
    # NoDecode: pydantic-settings otherwise JSON-parses list fields and rejects the
    # comma-separated form documented in .env.example (e.g. http://localhost:5173).
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    chroma_persist_dir: str = "../vector_db"
    upload_dir: str = "../uploads"
    environment: str = "development"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None or value == "":
            return ["http://localhost:5173"]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", "jwt_secret", "gemini_api_key", mode="before")
    @classmethod
    def empty_string_ok(cls, value: object) -> object:
        # Missing/blank env vars should not crash startup — callers already
        # treat empty strings as "use the local/dev fallback".
        if value is None:
            return ""
        return value


settings = Settings()
