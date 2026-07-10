"""Application configuration loaded from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    database_url: str = ""
    supabase_url: str = ""
    supabase_key: str = ""
    jwt_secret: str = ""
    google_client_id: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]
    chroma_persist_dir: str = "../vector_db"
    upload_dir: str = "../uploads"
    environment: str = "development"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
