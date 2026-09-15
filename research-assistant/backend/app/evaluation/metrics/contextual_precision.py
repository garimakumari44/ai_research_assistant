from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field



class ContextualPrecisionResult(BaseModel):
    """
    Result of contextual precision evaluation.
    """

    score: float = Field(
        ...,
        description="Precision score between 0 and 1",
    )

    explanation: str = Field(
        ...,
        description="Evaluation explanation",
    )

    relevant_contexts: List[str] = Field(
        default_factory=list,
        description="Useful retrieved contexts",
    )

    irrelevant_contexts: List[str] = Field(
        default_factory=list,
        description="Noise contexts",
    )



class ContextualPrecisionMetric:
    """
    Measures whether retrieved contexts
    are relevant to answering the query.

    Similar to:
    DeepEval ContextualPrecisionMetric
    """

    name = "contextual_precision"



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
        contexts: List[str],
    ) -> ContextualPrecisionResult:
        """
        Evaluate retrieval precision.
        """


        if not contexts:

            return ContextualPrecisionResult(
                score=0.0,
                explanation="No retrieved contexts found",
                irrelevant_contexts=[],
            )


        prompt = f"""
You are an AI retrieval evaluator.

Determine whether the retrieved contexts
are useful for answering the question.


Question:
----------------
{question}
----------------


Retrieved Contexts:

{contexts}


Evaluate:

1. Which contexts contain useful evidence?
2. Which contexts are irrelevant?
3. Are useful contexts ranked higher?


Scoring:

1.0 = All top contexts are relevant
0.5 = Mixed quality retrieval
0.0 = Mostly irrelevant retrieval


Return JSON:

{{
    "score": float,
    "explanation": string,
    "relevant_contexts": [],
    "irrelevant_contexts": []
}}
"""


        if self.llm_client:

            response = await self.llm_client.generate(
                prompt
            )

            return ContextualPrecisionResult(
                **response
            )


        return self._basic_check(
            question,
            contexts,
        )



    def _basic_check(
        self,
        question: str,
        contexts: List[str],
    ) -> ContextualPrecisionResult:
        """
        Lightweight CPU fallback.

        Uses keyword overlap between
        query and retrieved chunks.
        """


        query_words = set(
            question.lower().split()
        )


        relevant = []
        irrelevant = []


        scores = []


        for context in contexts:

            context_words = set(
                context.lower().split()
            )


            overlap = (
                query_words
                &
                context_words
            )


            score = (
                len(overlap)
                /
                max(len(query_words), 1)
            )


            scores.append(score)


            if score >= 0.3:

                relevant.append(context)

            else:

                irrelevant.append(context)



        final_score = sum(scores) / len(scores)



        return ContextualPrecisionResult(

            score=round(
                min(final_score, 1.0),
                3,
            ),

            explanation=(
                "Calculated using "
                "retrieval-context keyword overlap."
            ),

            relevant_contexts=relevant,

            irrelevant_contexts=irrelevant,
        )



    def is_successful(
        self,
        result: ContextualPrecisionResult,
    ) -> bool:
        """
        Check metric threshold.
        """

        return result.score >= self.threshold