from __future__ import annotations

from typing import List



def calculate_answer_relevance(
    question: str,
    answer: str,
) -> float:
    """
    Estimate answer relevance.

    Measures overlap between:
    - User question
    - Generated answer

    Lightweight implementation.

    Production systems should replace
    this with embedding similarity or
    LLM-based evaluation.
    """

    if not question:
        return 0.0


    if not answer:
        return 0.0


    question_words = set(
        question
        .lower()
        .split()
    )


    answer_words = set(
        answer
        .lower()
        .split()
    )


    if not question_words:
        return 0.0


    overlap = (
        question_words
        .intersection(answer_words)
    )


    return (
        len(overlap)
        /
        len(question_words)
    )