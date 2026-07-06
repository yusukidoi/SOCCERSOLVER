"""Application configuration, sourced from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root for the backend service (…/backend).
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Runtime settings. Values can be overridden via environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    csv_path: str = Field(default="data/players.csv")
    backend_port: int = Field(default=8000)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow CORS_ORIGINS to be given as a comma-separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def resolved_csv_path(self) -> Path:
        """Absolute path to the dataset, resolving relative paths from BACKEND_ROOT."""
        path = Path(self.csv_path)
        return path if path.is_absolute() else BACKEND_ROOT / path


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
