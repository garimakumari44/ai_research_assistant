from __future__ import annotations

from typing import List, Dict, Any

from pydantic import BaseModel, Field


class FaithfulnessResult(BaseModel):
    """
    Result of faithfulness evaluation.
    """

    score: float = Field(
        ...,
        description="Faithfulness score between 0 and 1",
    )

    explanation: str = Field(
        ...,
        description="Reasoning behind the score",
    )

    supported_claims: List[str] = Field(
        default_factory=list,
        description="Claims supported by context",
    )

    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Claims not supported by context",
    )


class FaithfulnessMetric:
    """
    Evaluates whether an answer is faithful
    to the provided retrieval context.

    Measures:
    - Hallucination
    - Unsupported statements
    - Context grounding

    Similar to:
    DeepEval FaithfulnessMetric
    """

    name = "faithfulness"


    def __init__(
        self,
        llm_client=None,
        threshold: float = 0.7,
    ):
        self.llm_client = llm_client
        self.threshold = threshold



    async def evaluate(
        self,
        answer: str,
        contexts: List[str],
    ) -> FaithfulnessResult:
        """
        Evaluate answer against retrieved contexts.
        """


        if not contexts:
            return FaithfulnessResult(
                score=0.0,
                explanation="No context provided",
                unsupported_claims=[
                    answer
                ],
            )


        context_text = "\n\n".join(contexts)


        prompt = f"""
You are an AI evaluation judge.

Determine whether the answer is fully supported
by the provided context.

Context:
----------------
{context_text}
----------------


Answer:
----------------
{answer}
----------------


Tasks:

1. Extract claims from the answer.
2. Check each claim against the context.
3. Identify unsupported claims.
4. Give a score from 0 to 1.

Scoring:

1.0 = Completely supported
0.5 = Partially supported
0.0 = Hallucinated


Return JSON:

{{
    "score": float,
    "explanation": string,
    "supported_claims": [],
    "unsupported_claims": []
}}
"""


        if self.llm_client:

            response = await self.llm_client.generate(
                prompt
            )

            return FaithfulnessResult(
                **response
            )


        # fallback heuristic mode
        return self._basic_check(
            answer,
            contexts,
        )



    def _basic_check(
        self,
        answer: str,
        contexts: List[str],
    ) -> FaithfulnessResult:
        """
        Lightweight CPU-only fallback.

        Used when no LLM judge exists.
        """

        context = " ".join(contexts).lower()

        sentences = [
            s.strip()
            for s in answer.split(".")
            if s.strip()
        ]


        supported = []
        unsupported = []


        for sentence in sentences:

            words = sentence.lower().split()

            overlap = sum(
                1
                for word in words
                if word in context
            )


            ratio = overlap / max(
                len(words),
                1,
            )


            if ratio >= 0.3:
                supported.append(sentence)

            else:
                unsupported.append(sentence)



        score = len(supported) / max(
            len(sentences),
            1,
        )


        return FaithfulnessResult(
            score=round(score, 3),

            explanation=(
                "Calculated using lexical overlap "
                "fallback evaluator."
            ),

            supported_claims=supported,

            unsupported_claims=unsupported,
        )



    def is_successful(
        self,
        result: FaithfulnessResult,
    ) -> bool:
        """
        Check if metric passes.
        """

        return result.score >= self.threshold