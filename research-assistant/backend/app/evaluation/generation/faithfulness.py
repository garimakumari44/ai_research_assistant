from __future__ import annotations

from typing import List


def calculate_faithfulness(
    answer: str,
    context_documents: List[str],
) -> float:
    """
    Estimate answer faithfulness.

    Checks whether answer claims
    are supported by retrieved context.

    This is a lightweight implementation.
    Production systems can replace this
    with LLM-based evaluation (RAGAS).
    """

    if not answer:
        return 0.0


    if not context_documents:
        return 0.0


    context = " ".join(
        context_documents
    ).lower()


    answer_words = (
        answer
        .lower()
        .split()
    )


    supported_words = [
        word
        for word in answer_words
        if word in context
    ]


    if not answer_words:
        return 0.0


    return (
        len(supported_words)
        /
        len(answer_words)
    )