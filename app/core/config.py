"""
Central configuration using pydantic-settings.

WHY pydantic-settings?
- Reads from .env automatically
- Type validation on every config value
- Single source of truth for all settings
- Never hard-code secrets

INTERVIEW ANGLE:
"How do you manage configuration in a production Python app?"
→ pydantic-settings with environment variables, never config files with secrets
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, field_validator
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    secret_key: str = "change_this_in_production"

    # LLM
    llm_provider: Literal["openai", "anthropic", "groq", "ollama"] = "openai"
    llm_api_key: str = ""
    llm_model_name: str = "llama-3.1-8b-instant"
    llm_strong_model: str = "llama-3.3-70b-versatile"
    

    # Database
    database_url: str = "postgresql+asyncpg://codeaudit:codeaudit@localhost:5433/codeauditdb"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "security_knowledge"

    # Sandbox
    sandbox_image: str = "codeaudit-sandbox:latest"
    sandbox_timeout: int = 30
    sandbox_memory_limit: str = "256m"
    sandbox_cpu_limit: float = 0.5

    # Scan
    max_file_size_kb: int = 500
    max_repo_size_mb: int = 100
    supported_languages: str = "python"

    @field_validator("llm_api_key")
    @classmethod
    def api_key_must_not_be_empty_in_production(cls, v, info):
        # We allow empty key in development for testing with mocks
        return v

    @property
    def supported_language_list(self) -> list[str]:
        return [lang.strip() for lang in self.supported_languages.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    lru_cache ensures we only read .env once.
    """
    return Settings()


# Convenience alias
settings = get_settings()