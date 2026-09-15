from __future__ import annotations

from typing import Dict, List, Optional


from app.research.models import (
    Evidence,
    ResearchSource,
)



class EvidenceTracker:
    """
    Tracks relationships between:

    Claim
        |
        v
    Evidence
        |
        v
    Source


    Used for:

    - Source attribution
    - Citation generation
    - Hallucination reduction
    - Research transparency

    """



    def __init__(self):

        self.evidence_map: Dict[
            str,
            Evidence
        ] = {}


        self.source_map: Dict[
            str,
            ResearchSource
        ] = {}



    def register_source(
        self,
        source: ResearchSource,
    ):
        """
        Store a research source.
        """

        self.source_map[
            source.id
        ] = source



    def register_evidence(
        self,
        evidence: Evidence,
    ):
        """
        Store evidence item.
        """

        self.evidence_map[
            evidence.id
        ] = evidence



    def add_evidence_batch(
        self,
        evidence_items: List[Evidence],
    ):
        """
        Register multiple evidence items.
        """

        for evidence in evidence_items:

            self.register_evidence(
                evidence
            )



    def get_source_for_evidence(
        self,
        evidence_id: str,
    ) -> Optional[ResearchSource]:
        """
        Find original source
        for an evidence item.
        """

        evidence = self.evidence_map.get(
            evidence_id
        )


        if not evidence:
            return None


        return self.source_map.get(
            evidence.source_id
        )



    def get_evidence_chain(
        self,
        evidence_id: str,
    ) -> Dict:
        """
        Return complete attribution chain.

        Example:

        Claim
          |
          v
        Evidence
          |
          v
        Source

        """

        evidence = self.evidence_map.get(
            evidence_id
        )


        if not evidence:
            return {}


        source = self.source_map.get(
            evidence.source_id
        )


        return {

            "claim":
            evidence.claim,


            "supporting_text":
            evidence.supporting_text,


            "confidence":
            evidence.confidence,


            "source":
            {

                "id":
                source.id if source else None,


                "title":
                source.title if source else None,


                "type":
                source.source_type
                if source else None,


                "url":
                source.url
                if source else None,

            }
        }



    def find_supporting_evidence(
        self,
        claim: str,
    ) -> List[Evidence]:
        """
        Find evidence supporting a claim.

        Later improvements:

        - Semantic similarity search
        - Embeddings
        - Cross encoder ranking

        """

        results = []


        claim_words = set(
            claim.lower().split()
        )


        for evidence in self.evidence_map.values():

            evidence_words = set(
                evidence.claim.lower().split()
            )


            overlap = (
                len(
                    claim_words &
                    evidence_words
                )
            )


            if overlap > 0:

                results.append(
                    evidence
                )


        return results