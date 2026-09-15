from __future__ import annotations

from typing import List, Dict, Any



class DeepEvalEvaluator:
    """
    DeepEval integration wrapper.

    Provides evaluation for:

    - Faithfulness
    - Answer relevancy
    - Contextual precision
    - Contextual recall

    Keeps DeepEval isolated from
    application logic.
    """



    def __init__(
        self,
        model=None,
    ):
        """
        Initialize DeepEval evaluator.

        model:
            Optional judge LLM.
        """

        self.model = model



    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        expected_answer: str | None = None,
    ) -> Dict[str, Any]:
        """
        Execute DeepEval evaluation.
        """


        try:

            from deepeval.test_case import (
                LLMTestCase,
            )


            from evaluation.metrics import (

                FaithfulnessMetric,

                AnswerRelevancyMetric,

                ContextualPrecisionMetric,

                ContextualRecallMetric,

            )



            test_case = LLMTestCase(

                input=question,

                actual_output=answer,

                retrieval_context=contexts,

                expected_output=expected_answer,

            )



            metrics = [

                FaithfulnessMetric(
                    model=self.model
                ),

                AnswerRelevancyMetric(
                    model=self.model
                ),

                ContextualPrecisionMetric(
                    model=self.model
                ),

                ContextualRecallMetric(
                    model=self.model
                ),

            ]



            results = {}



            for metric in metrics:

                metric.measure(
                    test_case
                )


                results[
                    metric.__class__.__name__
                ] = {

                    "score":
                        metric.score,

                    "reason":
                        metric.reason,

                }



            return results



        except Exception as error:

            return {
                "error": str(error)
            }