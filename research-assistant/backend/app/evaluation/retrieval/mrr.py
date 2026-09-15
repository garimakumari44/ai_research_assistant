from __future__ import annotations

from typing import List


def mean_reciprocal_rank(
    retrieved_documents: List[str],
    relevant_documents: List[str],
) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).

    Measures the rank position of the
    first relevant retrieved document.

    Args:
        retrieved_documents:
            Ordered list of retrieved documents.

        relevant_documents:
            Ground truth relevant documents.

    Returns:
        MRR score between 0 and 1.
    """

    if not retrieved_documents:
        return 0.0


    if not relevant_documents:
        return 0.0


    relevant_set = set(
        relevant_documents
    )


    for rank, document in enumerate(
        retrieved_documents,
        start=1,
    ):

        if document in relevant_set:

            return 1 / rank


    return 0.0