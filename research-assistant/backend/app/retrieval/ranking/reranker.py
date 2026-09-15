from __future__ import annotations

from typing import List

from sentence_transformers import CrossEncoder

from app.retrieval.models import RetrievedDocument


class CrossEncoderReranker:
    """
    Cross-encoder reranker.

    The reranker changes ranking relevance but preserves
    the original retrieval score in metadata.
    """

    def __init__(
        self,
        model_name: str = (
            "cross-encoder/"
            "ms-marco-MiniLM-L-6-v2"
        ),
        model: CrossEncoder | None = None,
    ) -> None:

        self.model_name = model_name

        self.model = (
            model
            or CrossEncoder(
                model_name
            )
        )

    @property
    def name(self) -> str:
        return self.model_name

    # ========================================================================
    # RERANK
    # ========================================================================

    def rerank(
        self,
        query: str,
        documents: List[
            RetrievedDocument
        ],
        top_k: int = 5,
    ) -> List[
        RetrievedDocument
    ]:
        """
        Rerank retrieved documents.
        """

        if (
            not documents
            or top_k <= 0
        ):
            return []

        query = query.strip()

        if not query:
            return documents[:top_k]

        pairs = [
            [
                query,
                document.text,
            ]
            for document in documents
        ]

        scores = self.model.predict(
            pairs
        )

        for document, score in zip(
            documents,
            scores,
        ):

            try:
                rerank_score = float(
                    score
                )
            except (
                TypeError,
                ValueError,
            ):
                rerank_score = 0.0

            # Preserve original retrieval score.
            original_score = (
                document.score
            )

            document.metadata[
                "original_retrieval_score"
            ] = original_score

            document.metadata[
                "rerank_score"
            ] = rerank_score

            # Final document score becomes reranker score.
            document.score = rerank_score

        ranked_documents = sorted(
            documents,
            key=lambda document: (
                document.score,
                document.id,
            ),
            reverse=True,
        )

        ranked_documents = (
            ranked_documents[:top_k]
        )

        for rank, document in enumerate(
            ranked_documents,
            start=1,
        ):
            document.metadata[
                "rerank_rank"
            ] = rank

        return ranked_documents


__all__ = [
    "CrossEncoderReranker",
]