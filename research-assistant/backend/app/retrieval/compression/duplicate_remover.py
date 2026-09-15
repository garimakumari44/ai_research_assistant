from __future__ import annotations

from difflib import SequenceMatcher
from typing import List

from app.retrieval.compression.base import BaseCompressor
from app.retrieval.compression.models import (
    CompressionChunk,
    CompressionRequest,
    CompressionResult,
)
from app.retrieval.compression.utils import (
    estimate_token_count,
    normalize_whitespace,
    sort_by_score,
)


class DuplicateRemover(BaseCompressor):
    """
    Removes exact and near-duplicate retrieved chunks.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.90,
    ) -> None:
        self.similarity_threshold = similarity_threshold

    @property
    def name(self) -> str:
        return "duplicate_remover"

    def compress(
        self,
        request: CompressionRequest,
    ) -> CompressionResult:
        """
        Remove duplicate chunks while preserving the
        highest-scoring version.
        """

        ranked_chunks = sort_by_score(request.chunks)

        unique_chunks: List[CompressionChunk] = []
        removed_duplicates = 0

        for chunk in ranked_chunks:

            chunk.text = normalize_whitespace(chunk.text)
            chunk.token_count = estimate_token_count(chunk.text)

            duplicate = False

            for existing in unique_chunks:

                similarity = self._similarity(
                    chunk.text,
                    existing.text,
                )

                if similarity >= self.similarity_threshold:
                    duplicate = True
                    removed_duplicates += 1
                    break

            if not duplicate:
                unique_chunks.append(chunk)

        return CompressionResult(
            chunks=unique_chunks,
            total_tokens=sum(
                chunk.token_count
                for chunk in unique_chunks
            ),
            removed_duplicates=removed_duplicates,
            removed_for_budget=0,
            compression_ratio=(
                len(unique_chunks) / len(request.chunks)
                if request.chunks
                else 1.0
            ),
            metadata={
                "compressor": self.name,
                "similarity_threshold": self.similarity_threshold,
            },
        )

    @staticmethod
    def _similarity(
        text1: str,
        text2: str,
    ) -> float:
        """
        Compute similarity between two texts.
        """

        return SequenceMatcher(
            None,
            text1.lower(),
            text2.lower(),
        ).ratio()