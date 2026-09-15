from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """
    Application configuration.

    Values are loaded from environment variables and/or .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================================================
    # APPLICATION
    # ========================================================================

    APP_NAME: str = "AI Research Assistant"

    APP_VERSION: str = "1.0.0"

    APP_DESCRIPTION: str = (
        "Backend API for the AI Research Assistant platform."
    )

    ENVIRONMENT: str = Field(
        default="development",
        description="development | testing | staging | production",
    )

    DEBUG: bool = False

    API_PREFIX: str = "/api"

    # ========================================================================
    # SERVER
    # ========================================================================

    HOST: str = "0.0.0.0"

    PORT: int = 8000

    # ========================================================================
    # DATABASE
    # ========================================================================

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@"
        "127.0.0.1:5432/adaptive_rag"
    )

    DB_ECHO: bool = False

    DB_POOL_SIZE: int = 10

    DB_MAX_OVERFLOW: int = 20

    DB_POOL_TIMEOUT: int = 30

    DB_POOL_RECYCLE: int = 1800

    # ========================================================================
    # REDIS
    # ========================================================================

    REDIS_URL: str = (
        "redis://127.0.0.1:6379/0"
    )

    # ========================================================================
    # SECURITY / JWT
    # ========================================================================

    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ========================================================================
    # CORS
    # ========================================================================

    CORS_ORIGINS: str = (
        "http://localhost:3000"
    )

    # ========================================================================
    # FRONTEND
    # ========================================================================

    NEXT_PUBLIC_API_URL: str = (
        "http://localhost:8000"
    )

    # ========================================================================
    # RESEARCH PROVIDERS
    # ========================================================================

    OPENALEX_API_URL: str = (
        "https://api.openalex.org"
    )

    SEMANTIC_SCHOLAR_API_URL: str = (
        "https://api.semanticscholar.org/graph/v1"
    )

    CROSSREF_API_URL: str = (
        "https://api.crossref.org"
    )

    ARXIV_API_URL: str = (
        "https://export.arxiv.org/api/query"
    )

    SEMANTIC_SCHOLAR_API_KEY: str | None = None

    # ========================================================================
    # HTTP PROVIDER SETTINGS
    # ========================================================================

    PROVIDER_TIMEOUT_SECONDS: float = 30.0

    PROVIDER_MAX_RETRIES: int = 3

    # ========================================================================
    # LLM
    # ========================================================================

    LLM_PROVIDER: str = "ollama"

    # ------------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------------

    LLM_OPENAI_API_KEY: str | None = None

    LLM_OPENAI_MODEL: str = "gpt-5-mini"

    # ------------------------------------------------------------------------
    # Gemini
    # ------------------------------------------------------------------------

    LLM_GEMINI_API_KEY: str | None = None

    LLM_GEMINI_MODEL: str = "gemini-2.5-flash"

    # ------------------------------------------------------------------------
    # Ollama
    # ------------------------------------------------------------------------

    LLM_OLLAMA_BASE_URL: str = (
        "http://localhost:11434"
    )

    LLM_OLLAMA_MODEL: str = "qwen3:8b"

    # ------------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------------

    LLM_TEMPERATURE: float = 0.2

    LLM_MAX_TOKENS: int = 1024

    LLM_TOP_P: float = 1.0

    LLM_TIMEOUT: int = 120

    LLM_MAX_RETRIES: int = 3

    # ========================================================================
    # LOGGING
    # ========================================================================

    LOG_LEVEL: str = "INFO"

    LOG_FORMAT: str = "standard"

    # ========================================================================
    # SEARCH
    # ========================================================================

    DEFAULT_PAGE_SIZE: int = 20

    MAX_PAGE_SIZE: int = 100

    # ========================================================================
    # HELPERS
    # ========================================================================

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Convert comma-separated CORS origins into a list.
        """

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """

    return Settings()


settings = get_settings()