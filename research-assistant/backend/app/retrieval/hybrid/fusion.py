from __future__ import annotations

from typing import Dict, List

from app.retrieval.models import (
    DenseSearchResult,
    HybridSearchResult,
    SparseSearchResult,
)


class HybridFusion:
    """
    Combines dense and sparse retrieval scores.

    Formula:

        hybrid =
            dense_weight * normalized_dense
            +
            sparse_weight * normalized_sparse
    """

    def __init__(
        self,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
    ) -> None:

        if dense_weight < 0:
            raise ValueError(
                "dense_weight must be >= 0"
            )

        if sparse_weight < 0:
            raise ValueError(
                "sparse_weight must be >= 0"
            )

        if (
            dense_weight == 0
            and sparse_weight == 0
        ):
            raise ValueError(
                "At least one fusion weight must be > 0"
            )

        total = (
            dense_weight
            + sparse_weight
        )

        self.dense_weight = (
            dense_weight / total
        )

        self.sparse_weight = (
            sparse_weight / total
        )

    # ========================================================================
    # SCORE NORMALIZATION
    # ========================================================================

    @staticmethod
    def normalize_scores(
        results,
    ) -> Dict[str, float]:
        """
        Min-max normalize scores into [0, 1].
        """

        if not results:
            return {}

        scores = [
            float(item.score)
            for item in results
        ]

        minimum = min(scores)
        maximum = max(scores)

        if maximum == minimum:
            return {
                str(item.id): 1.0
                for item in results
            }

        return {
            str(item.id): (
                float(item.score)
                - minimum
            )
            / (
                maximum
                - minimum
            )
            for item in results
        }

    # ========================================================================
    # FUSION
    # ========================================================================

    def fuse(
        self,
        dense_results: List[
            DenseSearchResult
        ],
        sparse_results: List[
            SparseSearchResult
        ],
    ) -> List[HybridSearchResult]:
        """
        Fuse dense and sparse results.
        """

        dense_scores = (
            self.normalize_scores(
                dense_results
            )
        )

        sparse_scores = (
            self.normalize_scores(
                sparse_results
            )
        )

        all_ids = (
            set(dense_scores)
            | set(sparse_scores)
        )

        results: List[
            HybridSearchResult
        ] = []

        for doc_id in all_ids:

            dense_score = (
                dense_scores.get(
                    doc_id,
                    0.0,
                )
            )

            sparse_score = (
                sparse_scores.get(
                    doc_id,
                    0.0,
                )
            )

            fusion_score = (
                self.dense_weight
                * dense_score
                +
                self.sparse_weight
                * sparse_score
            )

            results.append(
                HybridSearchResult(
                    id=doc_id,
                    dense_score=dense_score,
                    sparse_score=sparse_score,
                    fusion_score=fusion_score,
                    score=fusion_score,
                )
            )

        results.sort(
            key=lambda item: (
                item.fusion_score,
                item.id,
            ),
            reverse=True,
        )

        return results


__all__ = [
    "HybridFusion",
]