from __future__ import annotations

from typing import List


def recall_at_k(
    retrieved_documents: List[str],
    relevant_documents: List[str],
) -> float:
    """
    Calculate Recall@K.

    Measures how many relevant documents
    were successfully retrieved.

    Args:
        retrieved_documents:
            Documents returned by retriever.

        relevant_documents:
            Ground truth relevant documents.

    Returns:
        Recall score between 0 and 1.
    """

    if not relevant_documents:
        return 0.0


    if not retrieved_documents:
        return 0.0


    retrieved_set = set(
        retrieved_documents
    )

    relevant_set = set(
        relevant_documents
    )


    retrieved_relevant = (
        retrieved_set
        .intersection(relevant_set)
    )


    return (
        len(retrieved_relevant)
        /
        len(relevant_set)
    )