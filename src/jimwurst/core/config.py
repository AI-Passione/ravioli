import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Postgres Configuration
    postgres_user: str = "jimwurst_user"
    postgres_password: str = "jimwurst_password"
    postgres_db: str = "jimwurst_db"
    db_host: str = "localhost"
    db_port: int = 5432

    # Local data path
    local_data_path: Path = Path.home() / "Documents" / "jimwurst_local_data"

    # Ollama Configuration
    ollama_model: str = "qwen2.5:3b"
    ollama_host: str = "http://localhost:11434"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.db_host}:{self.db_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        env_file=(".env", "docker/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
