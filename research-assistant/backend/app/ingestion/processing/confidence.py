from __future__ import annotations

from typing import Any


class PaperConfidenceScorer:
    """
    Calculates a deterministic confidence score for paper metadata.

    Score range: 0.0 - 1.0
    """

    def score(self, paper: dict[str, Any]) -> float:
        score = 0.0

        if paper.get("title"):
            score += 0.25

        if paper.get("abstract"):
            score += 0.15

        if paper.get("authors"):
            score += 0.15

        if paper.get("publication_date"):
            score += 0.10

        if paper.get("doi"):
            score += 0.15

        if paper.get("venue"):
            score += 0.05

        if paper.get("publisher"):
            score += 0.05

        if paper.get("url"):
            score += 0.05

        if paper.get("external_ids"):
            score += 0.05

        return min(round(score, 4), 1.0)

    def classify(self, score: float) -> str:
        if score >= 0.85:
            return "high"

        if score >= 0.60:
            return "medium"

        return "low"

    def calculate(
        self,
        paper: dict[str, Any],
    ) -> dict[str, Any]:
        score = self.score(paper)

        result = dict(paper)

        result["confidence_score"] = score
        result["confidence_level"] = self.classify(score)

        return result