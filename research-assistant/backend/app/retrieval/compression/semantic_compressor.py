from __future__ import annotations

from typing import List

import numpy as np

from app.indexing.embeddings.model import (
    get_embedding_model,
)
from app.retrieval.compression.base import BaseCompressor
from app.retrieval.compression.models import (
    CompressionChunk,
    CompressionRequest,
    CompressionResult,
)
from app.retrieval.compression.utils import (
    estimate_token_count,
)


class SemanticCompressor(BaseCompressor):
    """
    Compress retrieved context using semantic similarity.

    The compressor keeps only the chunks that are most
    relevant to the user's query.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.55,
    ) -> None:

        self.similarity_threshold = similarity_threshold
        self.model = get_embedding_model()

    @property
    def name(self) -> str:
        return "semantic_compressor"

    def compress(
        self,
        request: CompressionRequest,
    ) -> CompressionResult:

        if not request.chunks:
            return CompressionResult(
                chunks=[],
                total_tokens=0,
            )

        query = request.metadata.get("query", "")

        if not query:
            return CompressionResult(
                chunks=request.chunks,
                total_tokens=sum(c.token_count for c in request.chunks),
                compression_ratio=1.0,
                metadata={
                    "compressor": self.name,
                    "reason": "no_query",
                },
            )

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        selected_chunks: List[CompressionChunk] = []

        for chunk in request.chunks:

            text = chunk.compressed_text or chunk.text

            embedding = self.model.encode(
                text,
                normalize_embeddings=True,
            )

            similarity = float(
                np.dot(
                    query_embedding,
                    embedding,
                )
            )

            if similarity >= self.similarity_threshold:

                chunk.token_count = estimate_token_count(text)

                chunk.metadata["semantic_score"] = similarity

                selected_chunks.append(chunk)

        selected_chunks.sort(
            key=lambda c: c.metadata["semantic_score"],
            reverse=True,
        )

        total_tokens = sum(
            chunk.token_count
            for chunk in selected_chunks
        )

        return CompressionResult(
            chunks=selected_chunks,
            total_tokens=total_tokens,
            removed_duplicates=0,
            removed_for_budget=0,
            compression_ratio=(
                len(selected_chunks) / len(request.chunks)
                if request.chunks
                else 1.0
            ),
            metadata={
                "compressor": self.name,
                "threshold": self.similarity_threshold,
            },
        )