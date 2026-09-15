from __future__ import annotations

from typing import List, Dict, Any


from app.evaluation.models import (
    EvaluationResult,
    RetrievalScore,
    GenerationScore,
    PerformanceScore,
)


from app.evaluation.retrieval.metrics import (
    evaluate_retrieval,
)


from app.evaluation.generation.faithfulness import (
    calculate_faithfulness,
)


from app.evaluation.generation.relevance import (
    calculate_answer_relevance,
)


from app.evaluation.generation.context import (
    calculate_context_precision,
    calculate_context_recall,
)



class EvaluationPipeline:
    """
    Main evaluation orchestrator.

    Runs:

    1. Retrieval evaluation
    2. Generation evaluation
    3. Performance evaluation
    """



    def evaluate(
        self,
        question: str,
        retrieved_documents: List[str],
        relevant_documents: List[str],
        relevance_scores: List[float],
        answer: str,
        latency_metrics: Dict[str, float],
    ) -> EvaluationResult:
        """
        Execute complete evaluation.
        """


        #
        # Retrieval Metrics
        #

        retrieval_metrics = evaluate_retrieval(
            retrieved_documents,
            relevant_documents,
            relevance_scores,
        )


        retrieval_score = RetrievalScore(
            recall_at_k=
                retrieval_metrics[
                    "recall@k"
                ],

            precision_at_k=
                retrieval_metrics[
                    "precision@k"
                ],

            mrr=
                retrieval_metrics[
                    "mrr"
                ],

            ndcg=
                retrieval_metrics[
                    "ndcg"
                ],
        )


        #
        # Generation Metrics
        #

        generation_score = GenerationScore(

            faithfulness=
                calculate_faithfulness(
                    answer,
                    retrieved_documents,
                ),


            answer_relevance=
                calculate_answer_relevance(
                    question,
                    answer,
                ),


            context_precision=
                calculate_context_precision(
                    retrieved_documents,
                    relevant_documents,
                ),


            context_recall=
                calculate_context_recall(
                    retrieved_documents,
                    relevant_documents,
                ),
        )


        #
        # Performance Metrics
        #

        performance_score = PerformanceScore(

            latency_ms=
                latency_metrics.get(
                    "total_latency_ms",
                    0.0,
                ),


            retrieval_latency_ms=
                latency_metrics.get(
                    "retrieval_latency_ms",
                    0.0,
                ),


            generation_latency_ms=
                latency_metrics.get(
                    "generation_latency_ms",
                    0.0,
                ),
        )



        return EvaluationResult(

            retrieval=retrieval_score,

            generation=generation_score,

            performance=performance_score,

        )