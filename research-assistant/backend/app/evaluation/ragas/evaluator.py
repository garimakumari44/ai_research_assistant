from __future__ import annotations

from typing import List, Dict, Any


class RagasEvaluator:
    """
    Wrapper around RAGAS evaluation.

    Evaluates:

    - Faithfulness
    - Answer relevance
    - Context precision
    - Context recall

    This class isolates RAGAS dependency
    from the rest of the application.
    """


    def __init__(
        self,
        llm=None,
        embeddings=None,
    ):
        """
        Initialize evaluator.

        llm:
            LLM used by RAGAS judge.

        embeddings:
            Embedding model used by RAGAS.
        """

        self.llm = llm

        self.embeddings = embeddings



    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str | None = None,
    ) -> Dict[str, Any]:
        """
        Run RAGAS evaluation.

        Returns:
            Evaluation scores.
        """


        try:

            from datasets import Dataset


            from ragas import evaluate


            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            )


            data = {
                "question": [
                    question
                ],

                "answer": [
                    answer
                ],

                "contexts": [
                    contexts
                ],

            }


            if ground_truth:

                data[
                    "ground_truth"
                ] = [
                    ground_truth
                ]



            dataset = Dataset.from_dict(
                data
            )



            result = evaluate(
                dataset,

                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                ],

                llm=self.llm,

                embeddings=self.embeddings,
            )


            return result



        except Exception as error:

            return {
                "error": str(error)
            }