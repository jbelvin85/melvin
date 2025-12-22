from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Melvin"
    environment: str = "development"
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    data_root: Path = Path(__file__).resolve().parents[3] / "data"
    raw_data_dir: Path = Path(__file__).resolve().parents[3] / "data" / "raw"
    processed_data_dir: Path = Path(__file__).resolve().parents[3] / "data" / "processed"
    frontend_dist: Path | None = None

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "melvin"
    postgres_password: str = "melvin"
    postgres_db: str = "melvin"

    mongo_uri: str = "mongodb://mongo:27017"
    mongo_db: str = "melvin"

    ollama_host: str = "ollama"
    ollama_port: int = 11434
    ollama_model: str = "llama2"

    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:8001", "http://127.0.0.1:8001"]
    )
    initial_admin_username: str = "admin"
    initial_admin_password: str = "ChangeMe!123"
    scryfall_base_url: str = "https://api.scryfall.com"
    scryfall_cache_ttl_seconds: int = 60 * 60  # 1 hour default cache TTL
    # Optional Redis URL for shared caching (example: redis://redis:6379/0)
    redis_url: str | None = None

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                import json

                try:
                    return json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError("Invalid JSON for allowed_origins") from exc
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        json_loads=lambda value: value,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
