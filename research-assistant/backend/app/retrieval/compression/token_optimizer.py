from __future__ import annotations

from typing import List

from app.retrieval.compression.base import BaseCompressor
from app.retrieval.compression.models import (
    CompressionChunk,
    CompressionRequest,
    CompressionResult,
)
from app.retrieval.compression.utils import (
    estimate_token_count,
    sort_by_score,
)


class TokenOptimizer(BaseCompressor):
    """
    Ensures the retrieved context fits within
    the configured token budget.
    """

    def __init__(
        self,
        default_budget: int = 4096,
    ) -> None:
        self.default_budget = default_budget

    @property
    def name(self) -> str:
        return "token_optimizer"

    def compress(
        self,
        request: CompressionRequest,
    ) -> CompressionResult:
        """
        Select the highest-value chunks while
        respecting the token budget.
        """

        budget = request.token_budget or self.default_budget

        ranked_chunks = sort_by_score(request.chunks)

        selected_chunks: List[CompressionChunk] = []

        current_tokens = 0
        removed = 0

        for chunk in ranked_chunks:

            text = chunk.compressed_text or chunk.text

            chunk.token_count = estimate_token_count(text)

            if current_tokens + chunk.token_count <= budget:
                selected_chunks.append(chunk)
                current_tokens += chunk.token_count
            else:
                removed += 1

        original_tokens = sum(
            estimate_token_count(
                c.compressed_text or c.text
            )
            for c in request.chunks
        )

        compression_ratio = (
            current_tokens / original_tokens
            if original_tokens > 0
            else 1.0
        )

        return CompressionResult(
            chunks=selected_chunks,
            total_tokens=current_tokens,
            removed_duplicates=0,
            removed_for_budget=removed,
            compression_ratio=compression_ratio,
            metadata={
                "compressor": self.name,
                "token_budget": budget,
                "original_tokens": original_tokens,
                "final_tokens": current_tokens,
            },
        )