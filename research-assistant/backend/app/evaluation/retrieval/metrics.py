from __future__ import annotations

from typing import Dict, List


from app.evaluation.retrieval.recall import (
    recall_at_k,
)

from app.evaluation.retrieval.precision import (
    precision_at_k,
)

from app.evaluation.retrieval.mrr import (
    mean_reciprocal_rank,
)

from app.evaluation.retrieval.ndcg import (
    calculate_ndcg,
)



def evaluate_retrieval(
    retrieved_documents: List[str],
    relevant_documents: List[str],
    relevance_scores: List[float],
) -> Dict[str, float]:
    """
    Run complete retrieval evaluation.

    Calculates:

    - Recall@K
    - Precision@K
    - MRR
    - nDCG

    Args:

        retrieved_documents:
            Documents returned by retriever.

        relevant_documents:
            Ground truth relevant documents.

        relevance_scores:
            Relevance score of each retrieved
            document in ranking order.

    Returns:

        Dictionary containing retrieval metrics.
    """


    return {

        "recall@k": recall_at_k(
            retrieved_documents,
            relevant_documents,
        ),


        "precision@k": precision_at_k(
            retrieved_documents,
            relevant_documents,
        ),


        "mrr": mean_reciprocal_rank(
            retrieved_documents,
            relevant_documents,
        ),


        "ndcg": calculate_ndcg(
            relevance_scores,
        ),

    }