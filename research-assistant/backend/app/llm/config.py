
from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.llm.models import ProviderType


class LLMSettings(BaseSettings):
    """
    Application-wide LLM configuration.

    OpenRouter is the only supported provider.

    Environment variables use the LLM_ prefix.

    Required:

        LLM_OPENROUTER_API_KEY=...

    Optional:

        LLM_OPENROUTER_MODEL=...
    """

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ============================================================
    # PROVIDER
    # ============================================================

    provider: ProviderType = Field(
        default=ProviderType.OPENROUTER,
    )

    # ============================================================
    # OPENROUTER
    # ============================================================

    openrouter_api_key: SecretStr = Field(
        default=SecretStr(""),
    )

    openrouter_model: str = Field(
        default="openrouter/free",
        min_length=1,
    )

    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
    )

    openrouter_http_referer: str = Field(
        default="http://localhost:3000",
    )

    openrouter_app_name: str = Field(
        default="AI Research Assistant",
    )

    # ============================================================
    # GENERATION
    # ============================================================

    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
    )

    max_tokens: int = Field(
        default=1024,
        gt=0,
    )

    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
    )

    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
    )

    # ============================================================
    # NETWORKING
    # ============================================================

    timeout: float = Field(
        default=120.0,
        gt=0.0,
    )

    max_retries: int = Field(
        default=3,
        ge=0,
    )

    verify_ssl: bool = True

    stream: bool = True

    # ============================================================
    # VALIDATION
    # ============================================================

    def get_openrouter_api_key(self) -> str:
        """Return the configured OpenRouter key."""

        value = self.openrouter_api_key.get_secret_value().strip()

        if not value:
            raise ValueError(
                "LLM_OPENROUTER_API_KEY is not configured."
            )

        return value


settings = LLMSettings()

