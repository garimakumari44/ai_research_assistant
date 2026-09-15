
"""
Data models for reranking.

These models represent retrieved chunks, reranked chunks,
and the final ranked results passed to the context
compression pipeline.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RetrievedChunk(BaseModel):
    """
    A chunk returned from the retrieval engine.

    This model is the canonical input contract for the
    CrossEncoderReranker.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    chunk_id: str
    document_id: str

    text: str

    retrieval_score: float = Field(
        default=0.0,
        description="Score assigned by the retrieval system.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class RankedChunk(RetrievedChunk):
    """
    Retrieved chunk after cross-encoder reranking.
    """

    rerank_score: float = Field(
        default=0.0,
        description="Score assigned by the reranker.",
    )

    normalized_score: float = Field(
        default=0.0,
        description="Normalized relevance score in the range 0-1.",
    )

    rank: int = Field(
        default=0,
        ge=0,
    )


class RankingResult(BaseModel):
    """
    Final reranking output.

    The CrossEncoderReranker returns this object rather than
    returning a raw list of chunks.
    """

    query: str

    chunks: list[RankedChunk]

    total_candidates: int

    returned_chunks: int

    reranker: str

    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
    )


__all__ = [
    "RetrievedChunk",
    "RankedChunk",
    "RankingResult",
]

