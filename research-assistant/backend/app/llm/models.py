
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# PROVIDER
# ============================================================


class ProviderType(str, Enum):
    """
    LLM providers supported by the application.

    OpenRouter is intentionally the only active provider.
    """

    OPENROUTER = "openrouter"


# ============================================================
# MESSAGE ROLES
# ============================================================


class MessageRole(str, Enum):
    """Standard chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# ============================================================
# CHAT MESSAGE
# ============================================================


class ChatMessage(BaseModel):
    """A single normalized chat message."""

    role: MessageRole
    content: str

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# CITATION
# ============================================================


class Citation(BaseModel):
    """Citation attached to an LLM-generated answer."""

    source_id: str
    title: str
    url: str | None = None
    page: int | None = None
    chunk_id: str | None = None
    score: float | None = None


# ============================================================
# TOKEN USAGE
# ============================================================


class Usage(BaseModel):
    """Normalized token usage."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


# ============================================================
# GENERATION CONFIGURATION
# ============================================================


class GenerationConfig(BaseModel):
    """Parameters controlling generation."""

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

    stop_sequences: list[str] = Field(
        default_factory=list,
    )

    stream: bool = False


# ============================================================
# LLM REQUEST
# ============================================================


class LLMRequest(BaseModel):
    """Normalized request sent to the configured LLM provider."""

    messages: list[ChatMessage]

    config: GenerationConfig = Field(
        default_factory=GenerationConfig,
    )

    model: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# STREAMING CHUNK
# ============================================================


class StreamingChunk(BaseModel):
    """Single normalized streaming chunk."""

    text: str
    finished: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# LLM RESPONSE
# ============================================================


class LLMResponse(BaseModel):
    """Normalized response returned by an LLM provider."""

    text: str

    provider: ProviderType

    model: str

    usage: Usage = Field(
        default_factory=Usage,
    )

    citations: list[Citation] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


# ============================================================
# MODEL INFORMATION
# ============================================================


class ModelInfo(BaseModel):
    """Metadata describing an OpenRouter model."""

    provider: ProviderType

    model_name: str

    context_window: int = 0

    supports_streaming: bool = True

    supports_tools: bool = False

    supports_vision: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

