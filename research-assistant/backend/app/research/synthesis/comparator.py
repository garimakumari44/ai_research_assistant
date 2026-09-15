from __future__ import annotations

from typing import List, Dict

from app.research.models import (
    Evidence,
    ComparisonResult,
)


class ResearchComparator:
    """
    Compares research topics using evidence.

    Responsibilities:

    - Identify comparison criteria
    - Extract differences
    - Build comparison tables
    - Support paper/framework/model analysis

    """



    def compare(
        self,
        topic: str,
        evidence_items: List[Evidence],
    ) -> ComparisonResult:
        """
        Generate comparison result.
        """


        criteria = self.extract_criteria(
            evidence_items
        )


        comparison_table = (
            self.build_comparison_table(
                evidence_items,
                criteria
            )
        )


        return ComparisonResult(

            topic=topic,

            criteria=criteria,

            comparison_table=comparison_table

        )



    def extract_criteria(
        self,
        evidence_items: List[Evidence],
    ) -> List[str]:
        """
        Determine comparison dimensions.

        Later improvements:

        - LLM extraction
        - Ontology matching
        - Knowledge graph

        """

        return [

            "Architecture",

            "Advantages",

            "Limitations",

            "Performance",

            "Use Cases"

        ]



    def build_comparison_table(
        self,
        evidence_items: List[Evidence],
        criteria: List[str],
    ) -> List[Dict[str, str]]:
        """
        Create structured comparison.

        Future:

        LLM converts evidence
        into rows and columns.

        """

        table = []


        for evidence in evidence_items:

            row = {

                "source":
                evidence.source_id,


                "finding":
                evidence.claim,

            }


            table.append(
                row
            )


        return table