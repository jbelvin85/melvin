from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


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

    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    initial_admin_username: str = "admin"
    initial_admin_username: str = "admin"
    initial_admin_password: str = "ChangeMe!123"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
