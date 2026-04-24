import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Postgres Configuration
    postgres_user: str = "ravioli_user"
    postgres_password: str = "ravioli_password"
    postgres_db: str = "ravioli_db"
    db_host: str = "postgres"
    db_port: int = 5432

    # Local data path
    local_data_path: Path = Path("/local_data")
    duckdb_path: Path = Path("/local_data/ravioli.duckdb")

    # Ollama Configuration
    ollama_model: str = "qwen2.5:3b"
    ollama_host: str = "http://ollama:11434"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.db_host}:{self.db_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
