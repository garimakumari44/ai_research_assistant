from __future__ import annotations

from typing import List

import numpy as np
from sklearn.metrics import ndcg_score



def calculate_ndcg(
    relevance_scores: List[float],
) -> float:
    """
    Calculate Normalized Discounted
    Cumulative Gain.

    Higher ranked relevant documents
    contribute more to the score.

    Args:
        relevance_scores:
            Relevance score for each
            retrieved document in ranking order.

    Returns:
        nDCG score between 0 and 1.
    """

    if not relevance_scores:
        return 0.0


    scores = np.asarray(
        [relevance_scores]
    )


    ideal_scores = np.asarray(
        [
            sorted(
                relevance_scores,
                reverse=True
            )
        ]
    )


    return float(
        ndcg_score(
            ideal_scores,
            scores,
        )
    )