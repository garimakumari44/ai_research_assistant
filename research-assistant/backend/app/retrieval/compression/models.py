from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CompressionChunk(BaseModel):
    """
    A retrieved chunk before and after compression.
    """

    id: str = Field(..., description="Unique chunk ID")

    text: str = Field(..., description="Chunk text")

    score: float = Field(
        default=0.0,
        description="Retrieval or reranking score",
    )

    source: Optional[str] = Field(
        default=None,
        description="Source document",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    # NEW
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Embedding vector used for semantic operations.",
    )

    token_count: int = Field(
        default=0,
        ge=0,
        description="Estimated number of tokens",
    )

    is_duplicate: bool = Field(
        default=False,
        description="Whether this chunk was marked as duplicate",
    )

    compressed_text: Optional[str] = Field(
        default=None,
        description="Compressed version of the chunk",
    )


class CompressionRequest(BaseModel):
    """
    Input to the compression pipeline.
    """

    # NEW
    query: str = Field(
        default="",
        description="Original user query.",
    )

    chunks: List[CompressionChunk]

    token_budget: int = Field(
        default=4096,
        gt=0,
    )

    remove_duplicates: bool = True

    compress_sentences: bool = True

    optimize_budget: bool = True

    reorder_context: bool = True

    # NEW
    use_semantic_compression: bool = False


class CompressionResult(BaseModel):
    """
    Output from the compression pipeline.
    """

    chunks: List[CompressionChunk]

    total_tokens: int = Field(
        default=0,
        ge=0,
    )

    removed_duplicates: int = Field(
        default=0,
        ge=0,
    )

    removed_for_budget: int = Field(
        default=0,
        ge=0,
    )

    compression_ratio: float = Field(
        default=1.0,
        ge=0.0,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )