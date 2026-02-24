from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    cors_origins: List[str] = ["http://localhost:5173"]  # Vite default port
    fast_env: str = "production"


settings = Settings()