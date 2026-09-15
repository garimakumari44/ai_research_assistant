
from __future__ import annotations

import logging
import re
from typing import Iterable
from uuid import uuid4

from app.research.models import (
    RetrievedDocument,
    Evidence,
)

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """
    Converts retrieved documents into normalized evidence.

    The collector is deterministic and does not call an LLM.

    Responsibilities:
        - validate retrieved documents
        - extract candidate claims
        - remove duplicate claims
        - preserve source linkage
        - calculate an initial confidence score
        - limit evidence volume

    Non-responsibilities:
        - semantic contradiction detection
        - LLM reasoning
        - final answer generation
    """

    def __init__(
        self,
        *,
        max_evidence_per_document: int = 5,
        max_total_evidence: int = 50,
        min_claim_length: int = 30,
    ) -> None:
        if max_evidence_per_document <= 0:
            raise ValueError(
                "max_evidence_per_document must be greater than zero"
            )

        if max_total_evidence <= 0:
            raise ValueError(
                "max_total_evidence must be greater than zero"
            )

        if min_claim_length < 1:
            raise ValueError(
                "min_claim_length must be greater than zero"
            )

        self.max_evidence_per_document = (
            max_evidence_per_document
        )
        self.max_total_evidence = max_total_evidence
        self.min_claim_length = min_claim_length

    def collect(
        self,
        documents: Iterable[RetrievedDocument],
    ) -> list[Evidence]:
        """
        Convert retrieved documents into evidence items.
        """

        if documents is None:
            return []

        evidence_items: list[Evidence] = []
        seen_claims: set[str] = set()

        for document in documents:
            if len(evidence_items) >= self.max_total_evidence:
                break

            if not self._is_valid_document(document):
                continue

            claims = self.extract_claims(document)

            document_count = 0

            for claim in claims:
                if (
                    len(evidence_items)
                    >= self.max_total_evidence
                ):
                    break

                normalized_claim = self._normalize_claim(
                    claim
                )

                if not normalized_claim:
                    continue

                dedup_key = self._claim_key(
                    normalized_claim
                )

                if dedup_key in seen_claims:
                    continue

                seen_claims.add(dedup_key)

                confidence = self.calculate_confidence(
                    document
                )

                try:
                    evidence = Evidence(
                        id=str(uuid4()),
                        claim=normalized_claim,
                        supporting_text=document.text.strip(),
                        source_id=document.source.id,
                        confidence=confidence,
                        relevance_score=self._safe_score(
                            document.score
                        ),
                    )
                except (TypeError, ValueError) as exc:
                    logger.warning(
                        "Unable to create evidence item",
                        extra={
                            "error": str(exc),
                            "source_id": getattr(
                                document.source,
                                "id",
                                None,
                            ),
                        },
                    )
                    continue

                evidence_items.append(evidence)
                document_count += 1

                if (
                    document_count
                    >= self.max_evidence_per_document
                ):
                    break

        return evidence_items

    def extract_claims(
        self,
        document: RetrievedDocument,
    ) -> list[str]:
        """
        Extract candidate claims using deterministic sentence splitting.

        This is deliberately conservative. It does not claim to perform
        semantic claim extraction.

        A future NLP/LLM claim extractor can replace this method while
        keeping the collector contract unchanged.
        """

        if not self._is_valid_document(document):
            return []

        text = document.text.strip()

        sentences = self._split_sentences(text)

        claims: list[str] = []

        for sentence in sentences:
            sentence = self._normalize_claim(sentence)

            if not sentence:
                continue

            if len(sentence) < self.min_claim_length:
                continue

            if not self._looks_like_claim(sentence):
                continue

            claims.append(sentence)

        return claims

    def calculate_confidence(
        self,
        document: RetrievedDocument,
    ) -> float:
        """
        Calculate an initial evidence confidence.

        Current deterministic factors:

            retrieval score
            content availability
            source availability

        This is intentionally NOT presented as semantic truth confidence.
        """

        retrieval_score = self._safe_score(
            document.score
        )

        content = document.text.strip()

        if not content:
            return 0.0

        content_quality = 1.0

        if len(content) < 50:
            content_quality = 0.5
        elif len(content) < 100:
            content_quality = 0.75

        source_quality = 1.0

        if not getattr(document, "source", None):
            source_quality = 0.5

        confidence = (
            retrieval_score * 0.7
            + content_quality * 0.2
            + source_quality * 0.1
        )

        return round(
            max(0.0, min(1.0, confidence)),
            4,
        )

    def _is_valid_document(
        self,
        document: RetrievedDocument | None,
    ) -> bool:
        if document is None:
            return False

        text = getattr(document, "text", None)

        if not isinstance(text, str):
            return False

        if not text.strip():
            return False

        source = getattr(document, "source", None)

        if source is None:
            return False

        source_id = getattr(source, "id", None)

        if not source_id:
            return False

        return True

    @staticmethod
    def _split_sentences(
        text: str,
    ) -> list[str]:
        """
        Conservative sentence segmentation.

        Handles common '.', '!' and '?' boundaries without depending
        on an NLP package.
        """

        parts = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    def _looks_like_claim(
        self,
        sentence: str,
    ) -> bool:
        """
        Filter obvious non-claims.

        This intentionally does not attempt semantic classification.
        """

        lowered = sentence.lower()

        if lowered.endswith("?"):
            return False

        if lowered.startswith(
            (
                "figure ",
                "table ",
                "reference ",
                "references ",
                "http://",
                "https://",
            )
        ):
            return False

        return True

    @staticmethod
    def _normalize_claim(
        claim: str,
    ) -> str:
        if not isinstance(claim, str):
            return ""

        claim = " ".join(
            claim.strip().split()
        )

        return claim.rstrip(".!?;:")

    @staticmethod
    def _claim_key(
        claim: str,
    ) -> str:
        return " ".join(
            claim.lower().split()
        )

    @staticmethod
    def _safe_score(
        value: object,
    ) -> float:
        try:
            score = float(value)

            if score != score:
                return 0.0

            if score == float("inf"):
                return 0.0

            if score == float("-inf"):
                return 0.0

            return max(
                0.0,
                min(1.0, score),
            )

        except (TypeError, ValueError):
            return 0.0

