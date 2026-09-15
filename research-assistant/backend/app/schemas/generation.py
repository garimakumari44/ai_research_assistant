"""
Pydantic schemas for the generation layer.

These schemas define the API-facing contract for:

    Evidence
        ↓
    Synthesis
        ↓
    Citation validation
        ↓
    Verification
        ↓
    Final generated answer

The schemas intentionally do not depend on the internal generation
dataclasses so that the API contract remains stable if the internal
implementation changes.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class GenerationEvidence(BaseModel):
    """
    Evidence supplied to the generation layer.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    id: str = Field(
        ...,
        min_length=1,
        description="Unique evidence identifier, e.g. E1.",
    )

    content: str = Field(
        ...,
        min_length=1,
        description="Evidence text used to support the answer.",
    )

    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional relevance score.",
    )

    source: str | None = Field(
        default=None,
        description="Human-readable source identifier.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional evidence metadata.",
    )

    @field_validator("id")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        """
        Normalize simple evidence IDs.

        E01 -> E1
        e1  -> E1

        Non-standard identifiers are preserved.
        """

        normalized = value.strip().upper()

        if normalized.startswith("E"):
            numeric_part = normalized[1:]

            if numeric_part.isdigit():
                return f"E{int(numeric_part)}"

        return normalized

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """
        Remove accidental surrounding whitespace.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Evidence content cannot be empty."
            )

        return value


# ---------------------------------------------------------------------------
# Generation configuration
# ---------------------------------------------------------------------------


class GenerationConfig(BaseModel):
    """
    Configuration controlling answer generation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    provider: str = Field(
        default="ollama",
        description="LLM provider.",
    )

    model: str = Field(
        default="llama3.2:3b",
        description="LLM model name.",
    )

    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="LLM sampling temperature.",
    )

    max_tokens: int = Field(
        default=2048,
        ge=128,
        le=32768,
        description="Maximum generated tokens.",
    )

    concise: bool = Field(
        default=False,
        description="Whether to generate a concise answer.",
    )

    require_citations: bool = Field(
        default=True,
        description="Require the generated answer to contain citations.",
    )

    verify: bool = Field(
        default=True,
        description="Whether to run answer verification.",
    )

    minimum_grounding_score: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Minimum grounding score required for verification.",
    )

    reject_invalid_citations: bool = Field(
        default=True,
        description="Reject citations that do not map to supplied evidence.",
    )

    max_unsupported_claims: int = Field(
        default=0,
        ge=0,
        description="Maximum unsupported claims allowed.",
    )


# ---------------------------------------------------------------------------
# Generation request
# ---------------------------------------------------------------------------


class GenerationRequest(BaseModel):
    """
    Request for generating an answer from selected evidence.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    question: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="User's research question.",
    )

    evidence: list[GenerationEvidence] = Field(
        default_factory=list,
        description="Evidence selected by the retrieval/RAG layer.",
    )

    config: GenerationConfig = Field(
        default_factory=GenerationConfig,
        description="Generation configuration.",
    )

    request_id: str | None = Field(
        default=None,
        description="Optional request identifier.",
    )

    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation identifier.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional request metadata.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Question cannot be empty."
            )

        return value


# ---------------------------------------------------------------------------
# Citation schemas
# ---------------------------------------------------------------------------


class CitationReference(BaseModel):
    """
    A citation found in the generated answer.
    """

    evidence_id: str = Field(
        ...,
        min_length=1,
        description="Referenced evidence ID.",
    )

    position: int = Field(
        ...,
        ge=0,
        description="Character position of the citation in the answer.",
    )

    raw_text: str = Field(
        ...,
        min_length=1,
        description="Original citation text.",
    )


class CitationValidationResponse(BaseModel):
    """
    Result of citation validation.
    """

    valid: bool

    citations: list[CitationReference] = Field(
        default_factory=list,
    )

    valid_ids: list[str] = Field(
        default_factory=list,
    )

    invalid_ids: list[str] = Field(
        default_factory=list,
    )

    missing_ids: list[str] = Field(
        default_factory=list,
    )

    duplicate_ids: list[str] = Field(
        default_factory=list,
    )

    warnings: list[str] = Field(
        default_factory=list,
    )


# ---------------------------------------------------------------------------
# Verification schemas
# ---------------------------------------------------------------------------


class VerificationResponse(BaseModel):
    """
    Structured verification result.
    """

    passed: bool = Field(
        description="Whether the answer passed verification.",
    )

    grounding_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall evidence-grounding score.",
    )

    citation_validation: CitationValidationResponse

    supported_claims: list[str] = Field(
        default_factory=list,
    )

    unsupported_claims: list[str] = Field(
        default_factory=list,
    )

    warnings: list[str] = Field(
        default_factory=list,
    )

    reasons: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------------
# Generated answer
# ---------------------------------------------------------------------------


class GeneratedAnswerResponse(BaseModel):
    """
    Generated answer returned by the synthesis layer.
    """

    answer: str = Field(
        ...,
        description="Generated natural-language answer.",
    )

    question: str = Field(
        ...,
        description="Original user question.",
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence IDs supplied to generation.",
    )

    model: str = Field(
        ...,
        description="LLM model used for generation.",
    )

    provider: str = Field(
        ...,
        description="LLM provider used for generation.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------------
# Complete generation response
# ---------------------------------------------------------------------------


class GenerationResponse(BaseModel):
    """
    Complete API response from the generation pipeline.
    """

    success: bool = True

    answer: str

    question: str

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    citations: CitationValidationResponse

    verification: VerificationResponse | None = None

    model: str

    provider: str

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------------
# Generation status
# ---------------------------------------------------------------------------


GenerationStage = Literal[
    "received",
    "evidence_prepared",
    "synthesizing",
    "citations_validated",
    "verifying",
    "completed",
    "failed",
]


class GenerationStatusResponse(BaseModel):
    """
    Lightweight status response useful for frontend progress UI.
    """

    request_id: str | None = None

    stage: GenerationStage

    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    message: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------


class GenerationErrorResponse(BaseModel):
    """
    Standard generation-layer error response.
    """

    success: bool = False

    error: str

    error_type: str = "generation_error"

    request_id: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
    )