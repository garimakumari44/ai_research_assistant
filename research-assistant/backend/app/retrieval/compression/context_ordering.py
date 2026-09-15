from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from app.retrieval.compression.base import BaseCompressor
from app.retrieval.compression.models import (
    CompressionChunk,
    CompressionRequest,
    CompressionResult,
)


class ContextOrdering(BaseCompressor):
    """
    Orders context to maximize LLM answer quality.

    Strategy:
    - Group chunks by source document.
    - Sort chunks within each source by chunk index.
    - Rank document groups by their highest chunk score.
    """

    @property
    def name(self) -> str:
        return "context_ordering"

    def compress(
        self,
        request: CompressionRequest,
    ) -> CompressionResult:

        grouped: Dict[str, List[CompressionChunk]] = defaultdict(list)

        for chunk in request.chunks:
            source = chunk.source or "unknown"
            grouped[source].append(chunk)

        # Preserve document order
        for chunks in grouped.values():
            chunks.sort(
                key=lambda c: c.metadata.get("chunk_index", 0)
            )

        # Rank documents by their best chunk
        ordered_groups = sorted(
            grouped.values(),
            key=lambda chunks: max(c.score for c in chunks),
            reverse=True,
        )

        ordered_chunks: List[CompressionChunk] = []

        for group in ordered_groups:
            ordered_chunks.extend(group)

        total_tokens = sum(
            chunk.token_count
            for chunk in ordered_chunks
        )

        return CompressionResult(
            chunks=ordered_chunks,
            total_tokens=total_tokens,
            removed_duplicates=0,
            removed_for_budget=0,
            compression_ratio=1.0,
            metadata={
                "compressor": self.name,
                "documents": len(grouped),
            },
        )