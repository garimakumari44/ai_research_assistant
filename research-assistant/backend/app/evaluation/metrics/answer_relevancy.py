from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class AnswerRelevancyResult(BaseModel):
    """
    Result of answer relevancy evaluation.
    """

    score: float = Field(
        ...,
        description="Relevancy score between 0 and 1",
    )

    explanation: str = Field(
        ...,
        description="Reason for score",
    )

    relevant_points: List[str] = Field(
        default_factory=list,
        description="Parts of answer relevant to query",
    )

    irrelevant_points: List[str] = Field(
        default_factory=list,
        description="Parts unrelated to query",
    )



class AnswerRelevancyMetric:
    """
    Evaluates whether the generated answer
    is relevant to the user question.

    Similar to:
    DeepEval AnswerRelevancyMetric
    """


    name = "answer_relevancy"



    def __init__(
        self,
        llm_client=None,
        threshold: float = 0.7,
    ):
        self.llm_client = llm_client
        self.threshold = threshold



    async def evaluate(
        self,
        question: str,
        answer: str,
    ) -> AnswerRelevancyResult:
        """
        Evaluate answer relevance.
        """


        prompt = f"""
You are an AI evaluation judge.

Determine how relevant the answer is
to the user's question.


Question:
----------------
{question}
----------------


Answer:
----------------
{answer}
----------------


Evaluate:

1. Does the answer directly answer the question?
2. Does it contain unnecessary information?
3. Does it miss important parts of the question?


Scoring:

1.0 = Perfectly relevant
0.5 = Partially relevant
0.0 = Completely irrelevant


Return JSON:

{{
    "score": float,
    "explanation": string,
    "relevant_points": [],
    "irrelevant_points": []
}}
"""


        if self.llm_client:

            response = await self.llm_client.generate(
                prompt
            )

            return AnswerRelevancyResult(
                **response
            )


        return self._basic_check(
            question,
            answer,
        )



    def _basic_check(
        self,
        question: str,
        answer: str,
    ) -> AnswerRelevancyResult:
        """
        Simple CPU fallback evaluator.

        Uses keyword overlap between
        question and answer.
        """


        question_words = set(
            question.lower().split()
        )


        answer_words = set(
            answer.lower().split()
        )


        overlap = (
            question_words
            &
            answer_words
        )


        score = len(overlap) / max(
            len(question_words),
            1,
        )


        if score >= 0.7:

            explanation = (
                "Answer contains most "
                "important query terms."
            )

        elif score >= 0.3:

            explanation = (
                "Answer partially matches "
                "the question."
            )

        else:

            explanation = (
                "Answer has low alignment "
                "with question."
            )



        return AnswerRelevancyResult(

            score=round(
                min(score, 1.0),
                3,
            ),

            explanation=explanation,

            relevant_points=[
                " ".join(overlap)
            ]
            if overlap
            else [],

            irrelevant_points=[],
        )



    def is_successful(
        self,
        result: AnswerRelevancyResult,
    ) -> bool:
        """
        Check if metric passes threshold.
        """

        return result.score >= self.threshold