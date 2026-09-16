"""
Embedding generator.

Creates vectors from document chunks.

The underlying embedding model is loaded lazily.
"""

from __future__ import annotations

from typing import Any

from app.processing.embeddings.model import get_embedding_model


class EmbeddingGenerator:
    """
    Generate embeddings for document chunks.

    Construction is lightweight. The actual SentenceTransformer
    model is loaded only when generate() is called.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        self.model = get_embedding_model(
            model_name
        )

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    def generate(
        self,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Generate embeddings for chunks.

        Expected input:

            [
                {
                    "id": "...",
                    "text": "..."
                }
            ]

        Returns:

            [
                {
                    "id": "...",
                    "text": "...",
                    "embedding": [...]
                }
            ]
        """

        if not chunks:
            return []

        # --------------------------------------------------------------
        # Validate and extract text
        # --------------------------------------------------------------

        valid_chunks: list[dict[str, Any]] = []
        texts: list[str] = []

        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue

            text = chunk.get("text")

            if not isinstance(text, str):
                continue

            text = text.strip()

            if not text:
                continue

            valid_chunks.append(chunk)
            texts.append(text)

        if not valid_chunks:
            return []

        # --------------------------------------------------------------
        # Generate embeddings
        #
        # This is the first point at which the underlying BGE model
        # will actually be loaded.
        # --------------------------------------------------------------

        embeddings = self.model.encode(
            texts
        )

        # --------------------------------------------------------------
        # Build results
        # --------------------------------------------------------------

        results: list[dict[str, Any]] = []

        for chunk, vector in zip(
            valid_chunks,
            embeddings,
        ):
            results.append(
                {
                    **chunk,
                    "embedding": vector.tolist(),
                }
            )

        return results