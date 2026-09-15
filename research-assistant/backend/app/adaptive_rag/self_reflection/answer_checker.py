
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class AnswerCheckResult:
    """
    Structured answer-quality result.
    """

    acceptable: bool
    relevance_score: float
    completeness_score: float
    grounded: bool
    reasons: tuple[str, ...] = ()
    missing_aspects: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


class AnswerChecker:
    """
    Checks whether a generated answer is relevant, reasonably complete,
    and grounded against the supplied evidence.

    This component intentionally avoids using an LLM so that it can act as
    a cheap first-stage validator before expensive reflection.
    """

    def __init__(
        self,
        *,
        min_relevance: float = 0.45,
        min_completeness: float = 0.45,
    ) -> None:
        self.min_relevance = min_relevance
        self.min_completeness = min_completeness

    def check(
        self,
        query: str,
        answer: str,
        evidence: Sequence[Any] | None = None,
    ) -> AnswerCheckResult:
        query = query.strip()
        answer = answer.strip()

        if not query:
            return AnswerCheckResult(
                acceptable=False,
                relevance_score=0.0,
                completeness_score=0.0,
                grounded=False,
                reasons=("Query is empty.",),
            )

        if not answer:
            return AnswerCheckResult(
                acceptable=False,
                relevance_score=0.0,
                completeness_score=0.0,
                grounded=False,
                reasons=("Answer is empty.",),
            )

        query_terms = self._important_terms(query)
        answer_terms = self._important_terms(answer)

        if query_terms:
            matched = query_terms & answer_terms
            relevance = len(matched) / len(query_terms)
        else:
            relevance = 1.0

        evidence_terms = self._evidence_terms(evidence or ())

        if evidence_terms:
            grounded_terms = answer_terms & evidence_terms

            completeness = (
                len(grounded_terms) / len(answer_terms)
                if answer_terms
                else 0.0
            )

            grounded = completeness >= self.min_completeness
        else:
            completeness = 0.0
            grounded = False

        missing = tuple(
            sorted(query_terms - answer_terms)
        )

        reasons: list[str] = []

        if relevance < self.min_relevance:
            reasons.append(
                f"Answer relevance {relevance:.3f} is below "
                f"threshold {self.min_relevance:.3f}."
            )

        if completeness < self.min_completeness:
            reasons.append(
                f"Answer grounding/completeness {completeness:.3f} is below "
                f"threshold {self.min_completeness:.3f}."
            )

        if missing:
            reasons.append(
                f"{len(missing)} important query term(s) are not addressed."
            )

        if not reasons:
            reasons.append("Answer passes deterministic checks.")

        acceptable = (
            relevance >= self.min_relevance
            and completeness >= self.min_completeness
            and grounded
        )

        return AnswerCheckResult(
            acceptable=acceptable,
            relevance_score=max(0.0, min(1.0, relevance)),
            completeness_score=max(0.0, min(1.0, completeness)),
            grounded=grounded,
            reasons=tuple(reasons),
            missing_aspects=missing[:20],
            metadata={
                "query_term_count": len(query_terms),
                "answer_term_count": len(answer_terms),
            },
        )

    def _evidence_terms(
        self,
        evidence: Sequence[Any],
    ) -> set[str]:
        terms: set[str] = set()

        for item in evidence:
            terms.update(
                self._important_terms(
                    self._content(item)
                )
            )

        return terms

    def _important_terms(self, text: str) -> set[str]:
        tokens = re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]{2,}\b",
            text.lower(),
        )

        stop_words = {
            "the",
            "and",
            "for",
            "that",
            "this",
            "with",
            "from",
            "what",
            "when",
            "where",
            "which",
            "who",
            "why",
            "how",
            "does",
            "did",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            "about",
            "into",
            "than",
            "then",
            "their",
            "there",
            "here",
            "please",
        }

        return {
            token
            for token in tokens
            if token not in stop_words
        }

    @staticmethod
    def _content(item: Any) -> str:
        if isinstance(item, Mapping):
            for key in (
                "content",
                "text",
                "chunk",
                "page_content",
            ):
                value = item.get(key)
                if value:
                    return str(value)

        for attr in (
            "content",
            "text",
            "chunk",
            "page_content",
        ):
            value = getattr(item, attr, None)
            if value:
                return str(value)

        return ""

