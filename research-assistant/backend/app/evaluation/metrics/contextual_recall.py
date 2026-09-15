from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field



class ContextualRecallResult(BaseModel):
    """
    Result of contextual recall evaluation.
    """

    score: float = Field(
        ...,
        description="Recall score between 0 and 1",
    )

    explanation: str = Field(
        ...,
        description="Evaluation explanation",
    )

    covered_information: List[str] = Field(
        default_factory=list,
        description="Information found in retrieved context",
    )

    missing_information: List[str] = Field(
        default_factory=list,
        description="Required information missing from retrieval",
    )



class ContextualRecallMetric:
    """
    Measures whether retrieved contexts
    contain all information required
    to answer the question.

    Similar to:
    DeepEval ContextualRecallMetric
    """

    name = "contextual_recall"



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
        expected_answer: str,
        contexts: List[str],
    ) -> ContextualRecallResult:
        """
        Evaluate whether retrieval contains
        required answer information.
        """


        if not contexts:

            return ContextualRecallResult(
                score=0.0,
                explanation=(
                    "No contexts retrieved"
                ),
                missing_information=[
                    expected_answer
                ],
            )



        context_text = "\n\n".join(
            contexts
        )


        prompt = f"""
You are an AI retrieval evaluator.

Determine whether the retrieved context
contains enough information to answer
the question correctly.


Question:
----------------
{question}
----------------


Expected Answer:
----------------
{expected_answer}
----------------


Retrieved Context:
----------------
{context_text}
----------------


Evaluate:

1. Extract important facts from expected answer.
2. Check if those facts exist in retrieved context.
3. Identify missing facts.


Scoring:

1.0 = All required information retrieved
0.5 = Some information missing
0.0 = Retrieval failed


Return JSON:

{{
    "score": float,
    "explanation": string,
    "covered_information": [],
    "missing_information": []
}}
"""


        if self.llm_client:

            response = await self.llm_client.generate(
                prompt
            )

            return ContextualRecallResult(
                **response
            )


        return self._basic_check(
            expected_answer,
            contexts,
        )



    def _basic_check(
        self,
        expected_answer: str,
        contexts: List[str],
    ) -> ContextualRecallResult:
        """
        CPU fallback evaluator.

        Checks if expected answer
        information exists in context.
        """

        context_text = (
            " ".join(contexts)
            .lower()
        )


        answer_words = [
            word.strip(
                ".,!?;:"
            )
            for word in expected_answer.lower().split()
        ]


        covered = []
        missing = []


        for word in answer_words:

            if len(word) < 3:
                continue


            if word in context_text:

                covered.append(word)

            else:

                missing.append(word)



        total = len(
            covered
        ) + len(
            missing
        )


        score = (
            len(covered)
            /
            max(total, 1)
        )



        return ContextualRecallResult(

            score=round(
                score,
                3,
            ),

            explanation=(
                "Calculated using "
                "expected answer coverage."
            ),

            covered_information=covered,

            missing_information=missing,
        )



    def is_successful(
        self,
        result: ContextualRecallResult,
    ) -> bool:
        """
        Check threshold.
        """

        return result.score >= self.threshold