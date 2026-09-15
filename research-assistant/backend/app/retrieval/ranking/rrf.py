from __future__ import annotations

from typing import Dict, List, Sequence

from app.retrieval.models import RRFResult


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion.

    RRF score:

        score(d) = Σ 1 / (k + rank)

    The RRF implementation deliberately knows nothing about dense
    retrieval, sparse retrieval, documents, or database objects.

    Its only contract is:

        ranked ID lists
              ↓
        RRFResult list

    Example:

        rankings = [
            ["a", "b", "c"],
            ["b", "c", "d"],
        ]

        rrf.fuse(rankings)
    """

    def __init__(
        self,
        k: int = 60,
    ) -> None:
        if k < 1:
            raise ValueError(
                "RRF k must be >= 1"
            )

        self.k = k

    # ==================================================================
    # FUSE RANKINGS
    # ==================================================================

    def fuse(
        self,
        rankings: Sequence[Sequence[str]],
    ) -> List[RRFResult]:
        """
        Combine multiple ranked ID lists.

        Parameters
        ----------
        rankings:
            A sequence of ranked ID sequences.

        Returns
        -------
        list[RRFResult]
            Results sorted by descending RRF score.
        """

        if not rankings:
            return []

        scores: Dict[str, float] = {}

        for ranking in rankings:
            if not ranking:
                continue

            seen: set[str] = set()

            for position, raw_id in enumerate(
                ranking,
                start=1,
            ):
                doc_id = str(
                    raw_id
                )

                if not doc_id:
                    continue

                # A duplicate within the same ranking should not
                # artificially increase the RRF score.
                if doc_id in seen:
                    continue

                seen.add(
                    doc_id
                )

                contribution = (
                    1.0
                    /
                    (
                        self.k
                        + position
                    )
                )

                scores[doc_id] = (
                    scores.get(
                        doc_id,
                        0.0,
                    )
                    + contribution
                )

        if not scores:
            return []

        ranked = sorted(
            scores.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )

        return [
            RRFResult(
                id=doc_id,
                score=score,
                rank=rank,
            )
            for rank, (
                doc_id,
                score,
            ) in enumerate(
                ranked,
                start=1,
            )
        ]

    # ==================================================================
    # RETRIEVAL-RESULT CONVENIENCE API
    # ==================================================================

    def fuse_results(
        self,
        dense_results=None,
        sparse_results=None,
    ) -> List[RRFResult]:
        """
        Convenience adapter for dense/sparse retrieval result objects.

        This method converts retrieval objects into ranked ID lists and
        then delegates to the canonical fuse() method.
        """

        rankings: list[list[str]] = []

        dense_ranking = self._extract_ids(
            dense_results
        )

        sparse_ranking = self._extract_ids(
            sparse_results
        )

        if dense_ranking:
            rankings.append(
                dense_ranking
            )

        if sparse_ranking:
            rankings.append(
                sparse_ranking
            )

        return self.fuse(
            rankings
        )

    # ==================================================================
    # HELPERS
    # ==================================================================

    @staticmethod
    def _extract_ids(
        results,
    ) -> list[str]:
        """
        Convert retrieval result objects/dictionaries into IDs.
        """

        if not results:
            return []

        output: list[str] = []

        for item in results:
            if isinstance(
                item,
                dict,
            ):
                value = item.get(
                    "id"
                )

                if value is None:
                    value = item.get(
                        "chunk_id"
                    )
            else:
                value = getattr(
                    item,
                    "id",
                    None,
                )

                if value is None:
                    value = getattr(
                        item,
                        "chunk_id",
                        None,
                    )

            if value is None:
                continue

            output.append(
                str(value)
            )

        return output


__all__ = [
    "ReciprocalRankFusion",
]