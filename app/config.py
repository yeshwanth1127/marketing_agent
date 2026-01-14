"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/marketing_agent"

    # OpenAI
    openai_api_key: str

    # Qdrant Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    api_port: int = 8000

    # Security
    secret_key: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()





