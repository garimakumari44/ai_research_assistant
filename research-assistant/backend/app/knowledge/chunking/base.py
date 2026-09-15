from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import UUID


@dataclass(slots=True)
class ChunkingConfig:
    """
    Configuration shared by all chunking strategies.

    The values are intentionally strategy-agnostic so that the same
    configuration object can be passed to different chunkers.
    """

    max_tokens: int = 500
    min_tokens: int = 50
    overlap_tokens: int = 50

    preserve_sentences: bool = True
    preserve_paragraphs: bool = True
    preserve_sections: bool = True

    include_metadata: bool = True

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")

        if self.min_tokens < 0:
            raise ValueError("min_tokens cannot be negative.")

        if self.min_tokens > self.max_tokens:
            raise ValueError(
                "min_tokens cannot be greater than max_tokens."
            )

        if self.overlap_tokens < 0:
            raise ValueError("overlap_tokens cannot be negative.")

        if self.overlap_tokens >= self.max_tokens:
            raise ValueError(
                "overlap_tokens must be smaller than max_tokens."
            )


@dataclass(slots=True)
class Chunk:
    """
    Canonical chunk representation produced by a chunking strategy.

    This object is deliberately independent from SQLAlchemy/database
    models. A repository can later convert Chunk into a database model.
    """

    text: str

    chunk_index: int

    document_id: UUID | str | None = None
    section_id: UUID | str | None = None

    page_start: int | None = None
    page_end: int | None = None

    token_count: int = 0
    character_count: int = 0

    chunk_type: str = "text"

    metadata: dict[str, Any] = field(default_factory=dict)

    previous_chunk_index: int | None = None
    next_chunk_index: int | None = None

    def __post_init__(self) -> None:
        self.text = self.text.strip()

        if not self.text:
            raise ValueError("Chunk text cannot be empty.")

        if self.chunk_index < 0:
            raise ValueError("chunk_index cannot be negative.")

        if self.character_count == 0:
            self.character_count = len(self.text)

    @property
    def idempotency_key(self) -> str:
        """
        Stable logical identifier useful for deduplication.

        This is not a database primary key.
        """

        document = str(self.document_id) if self.document_id else "unknown"
        return f"{document}:{self.chunk_index}"


@dataclass(slots=True)
class ChunkingResult:
    """
    Result returned by a chunking strategy.
    """

    chunks: list[Chunk]

    strategy: str

    config: ChunkingConfig

    document_id: UUID | str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.chunks)

    @property
    def total_characters(self) -> int:
        return sum(chunk.character_count for chunk in self.chunks)

    @property
    def total_tokens(self) -> int:
        return sum(chunk.token_count for chunk in self.chunks)

    def validate(self) -> None:
        """
        Validate ordering and basic chunk invariants.
        """

        expected_index = 0

        for chunk in self.chunks:
            if chunk.chunk_index != expected_index:
                raise ValueError(
                    "Chunks must have contiguous chunk indexes."
                )

            expected_index += 1

        for index, chunk in enumerate(self.chunks):
            expected_previous = index - 1 if index > 0 else None
            expected_next = (
                index + 1
                if index < len(self.chunks) - 1
                else None
            )

            if chunk.previous_chunk_index != expected_previous:
                raise ValueError(
                    f"Invalid previous_chunk_index for chunk {index}."
                )

            if chunk.next_chunk_index != expected_next:
                raise ValueError(
                    f"Invalid next_chunk_index for chunk {index}."
                )


class BaseChunker(ABC):
    """
    Abstract interface for all chunking strategies.
    """

    strategy_name: str = "base"

    def __init__(
        self,
        config: ChunkingConfig | None = None,
    ) -> None:
        self.config = config or ChunkingConfig()

    @abstractmethod
    def chunk(
        self,
        text: str,
        *,
        document_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ChunkingResult:
        """
        Chunk raw document text.
        """

    def estimate_tokens(self, text: str) -> int:
        """
        Lightweight token approximation.

        This intentionally avoids coupling the chunking layer to a
        particular tokenizer.

        A later embedding/LLM layer can replace this with an exact
        tokenizer when required.
        """

        if not text:
            return 0

        words = text.split()

        if not words:
            return 0

        # Approximation:
        # ~1.3 tokens per whitespace-delimited word.
        return max(1, int(len(words) * 1.3))

    def normalize_text(self, text: str) -> str:
        """
        Normalize whitespace while preserving paragraph boundaries.
        """

        if not text:
            return ""

        lines = [
            line.strip()
            for line in text.replace("\r\n", "\n").replace("\r", "\n").split(
                "\n"
            )
        ]

        normalized: list[str] = []

        previous_blank = False

        for line in lines:
            if not line:
                if not previous_blank:
                    normalized.append("")

                previous_blank = True
                continue

            normalized.append(line)
            previous_blank = False

        return "\n".join(normalized).strip()

    def build_chunk(
        self,
        text: str,
        *,
        chunk_index: int,
        document_id: UUID | str | None = None,
        section_id: UUID | str | None = None,
        page_start: int | None = None,
        page_end: int | None = None,
        chunk_type: str = "text",
        metadata: Mapping[str, Any] | None = None,
    ) -> Chunk:
        """
        Construct a canonical Chunk object.
        """

        normalized = text.strip()

        if not normalized:
            raise ValueError("Cannot create a chunk from empty text.")

        token_count = self.estimate_tokens(normalized)

        return Chunk(
            text=normalized,
            chunk_index=chunk_index,
            document_id=document_id,
            section_id=section_id,
            page_start=page_start,
            page_end=page_end,
            token_count=token_count,
            character_count=len(normalized),
            chunk_type=chunk_type,
            metadata=dict(metadata or {}),
        )

    def finalize(
        self,
        chunks: list[Chunk],
        *,
        document_id: UUID | str | None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ChunkingResult:
        """
        Finalize chunks by fixing indexes and neighbor relationships.
        """

        finalized: list[Chunk] = []

        for index, chunk in enumerate(chunks):
            chunk.chunk_index = index
            chunk.previous_chunk_index = (
                index - 1 if index > 0 else None
            )
            chunk.next_chunk_index = (
                index + 1
                if index < len(chunks) - 1
                else None
            )

            finalized.append(chunk)

        result = ChunkingResult(
            chunks=finalized,
            strategy=self.strategy_name,
            config=self.config,
            document_id=document_id,
            metadata=dict(metadata or {}),
        )

        result.validate()

        return result