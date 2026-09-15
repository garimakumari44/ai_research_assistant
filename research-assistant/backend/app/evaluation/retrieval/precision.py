from __future__ import annotations

from typing import List


def precision_at_k(
    retrieved_documents: List[str],
    relevant_documents: List[str],
) -> float:
    """
    Calculate Precision@K.

    Measures the proportion of retrieved
    documents that are actually relevant.

    Args:
        retrieved_documents:
            Documents returned by retrieval.

        relevant_documents:
            Ground truth relevant documents.

    Returns:
        Precision score between 0 and 1.
    """

    if not retrieved_documents:
        return 0.0


    if not relevant_documents:
        return 0.0


    retrieved_set = set(
        retrieved_documents
    )

    relevant_set = set(
        relevant_documents
    )


    relevant_retrieved = (
        retrieved_set
        .intersection(relevant_set)
    )


    return (
        len(relevant_retrieved)
        /
        len(retrieved_set)
    )