from __future__ import annotations

from enum import StrEnum
from typing import Any, Mapping
from uuid import UUID

from app.knowledge.chunking.base import (
    BaseChunker,
    ChunkingConfig,
    ChunkingResult,
)
from app.knowledge.chunking.semantic import SemanticChunker
from app.knowledge.chunking.structural import StructuralChunker


class ChunkingStrategyName(StrEnum):
    """
    Supported chunking strategies.
    """

    SEMANTIC = "semantic"
    STRUCTURAL = "structural"


class ChunkingStrategy:
    """
    Strategy selector and orchestration layer.

    The rest of the application should depend on this class rather
    than directly instantiating individual chunkers.
    """

    def __init__(
        self,
        config: ChunkingConfig | None = None,
    ) -> None:

        self.config = config or ChunkingConfig()

        self._chunkers: dict[str, BaseChunker] = {
            ChunkingStrategyName.SEMANTIC: SemanticChunker(
                self.config
            ),
            ChunkingStrategyName.STRUCTURAL: StructuralChunker(
                self.config
            ),
        }

    def register(
        self,
        name: str,
        chunker: BaseChunker,
    ) -> None:
        """
        Register a custom chunking strategy.
        """

        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError("Chunking strategy name cannot be empty.")

        self._chunkers[normalized_name] = chunker

    def get(
        self,
        strategy: str | ChunkingStrategyName,
    ) -> BaseChunker:
        """
        Return a registered chunker.
        """

        name = str(strategy).strip().lower()

        chunker = self._chunkers.get(name)

        if chunker is None:
            available = ", ".join(sorted(self._chunkers))

            raise ValueError(
                f"Unknown chunking strategy '{name}'. "
                f"Available strategies: {available}"
            )

        return chunker

    def chunk(
        self,
        text: str,
        *,
        strategy: str | ChunkingStrategyName = ChunkingStrategyName.STRUCTURAL,
        document_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ChunkingResult:
        """
        Chunk a document using the selected strategy.
        """

        chunker = self.get(strategy)

        result = chunker.chunk(
            text,
            document_id=document_id,
            metadata=metadata,
        )

        result.metadata.setdefault(
            "requested_strategy",
            str(strategy),
        )

        result.metadata.setdefault(
            "chunker",
            chunker.__class__.__name__,
        )

        return result

    def available_strategies(self) -> list[str]:
        """
        Return all registered strategy names.
        """

        return sorted(self._chunkers.keys())

    def semantic(
        self,
        text: str,
        *,
        document_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ChunkingResult:
        """
        Convenience method for semantic chunking.
        """

        return self.chunk(
            text,
            strategy=ChunkingStrategyName.SEMANTIC,
            document_id=document_id,
            metadata=metadata,
        )

    def structural(
        self,
        text: str,
        *,
        document_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ChunkingResult:
        """
        Convenience method for structural chunking.
        """

        return self.chunk(
            text,
            strategy=ChunkingStrategyName.STRUCTURAL,
            document_id=document_id,
            metadata=metadata,
        )