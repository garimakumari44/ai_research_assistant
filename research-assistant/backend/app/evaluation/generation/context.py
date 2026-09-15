from __future__ import annotations

from typing import List



def calculate_context_precision(
    retrieved_documents: List[str],
    relevant_documents: List[str],
) -> float:
    """
    Calculate Context Precision.

    Measures how many retrieved documents
    are relevant.

    Formula:

    Relevant Retrieved Documents
    ----------------------------
    Total Retrieved Documents
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


    useful_documents = (
        retrieved_set
        .intersection(
            relevant_set
        )
    )


    return (
        len(useful_documents)
        /
        len(retrieved_set)
    )



def calculate_context_recall(
    retrieved_documents: List[str],
    relevant_documents: List[str],
) -> float:
    """
    Calculate Context Recall.

    Measures how much of the required
    context was successfully retrieved.

    Formula:

    Relevant Retrieved Documents
    ----------------------------
    Total Relevant Documents
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


    captured_documents = (
        retrieved_set
        .intersection(
            relevant_set
        )
    )


    return (
        len(captured_documents)
        /
        len(relevant_set)
    )