from __future__ import annotations

import re
from typing import Any, Dict, List

from app.research.models import ResearchQuery


class ResearchPlanner:
    """
    Creates a research execution plan.

    The planner is intentionally lightweight.

    Responsibilities:
        - determine which source types should be searched
        - determine research depth
        - determine which analysis tasks are required
        - detect whether the request requires comparison
    """

    def create_plan(
        self,
        research_query: ResearchQuery,
    ) -> Dict[str, Any]:
        """
        Generate a research execution strategy.

        This method is synchronous. ResearchPipeline supports both
        synchronous and asynchronous planner implementations.
        """

        if research_query is None:
            raise ValueError("ResearchQuery cannot be None.")

        # ------------------------------------------------------------------
        # Canonical ResearchQuery field
        # ------------------------------------------------------------------
        # ResearchQuery.question is the public API field and the canonical
        # representation of the user's research request.
        query = research_query.question.strip()

        if not query:
            raise ValueError("Research query cannot be empty.")

        # ------------------------------------------------------------------
        # Base plan
        # ------------------------------------------------------------------

        plan: Dict[str, Any] = {
            "query": query,
            "question": query,
            "depth": research_query.depth,
            "sources": [],
            "tasks": [],
            "requires_comparison": self.requires_comparison(query),
            "collection_id": research_query.collection_id,
        }

        # ==================================================================
        # Source Selection
        # ==================================================================

        if research_query.include_papers:
            plan["sources"].append(
                {
                    "type": "paper",
                    "purpose": (
                        "Find academic research and primary literature"
                    ),
                }
            )

        if research_query.include_github:
            plan["sources"].append(
                {
                    "type": "github",
                    "purpose": "Find open-source implementations",
                }
            )

        if research_query.include_docs:
            plan["sources"].append(
                {
                    "type": "documentation",
                    "purpose": (
                        "Find official documentation and technical references"
                    ),
                }
            )

        # ==================================================================
        # Core Research Tasks
        # ==================================================================

        plan["tasks"].extend(
            [
                "Collect relevant information",
                "Extract supporting evidence",
                "Synthesize findings",
            ]
        )

        # ==================================================================
        # Comparison
        # ==================================================================

        if plan["requires_comparison"]:
            plan["tasks"].extend(
                [
                    "Identify comparison criteria",
                    "Compare approaches",
                ]
            )

        # ==================================================================
        # Research Depth
        # ==================================================================

        if research_query.depth == "basic":
            plan["tasks"].append(
                "Generate concise summary"
            )

        elif research_query.depth == "medium":
            plan["tasks"].extend(
                [
                    "Analyze strengths and weaknesses",
                    "Generate structured summary",
                ]
            )

        elif research_query.depth == "deep":
            plan["tasks"].extend(
                [
                    "Analyze strengths and weaknesses",
                    "Analyze limitations",
                    "Identify research gaps",
                    "Identify open questions",
                    "Generate detailed synthesis",
                ]
            )

        return plan

    # ======================================================================
    # Comparison Detection
    # ======================================================================

    @staticmethod
    def requires_comparison(
        query: str,
    ) -> bool:
        """
        Determine whether the user is requesting a comparison.
        """

        if not query:
            return False

        normalized_query = query.lower().strip()

        comparison_patterns: List[str] = [
            r"\bcompare\b",
            r"\bcomparison\b",
            r"\bcomparative\b",
            r"\bdifference\b",
            r"\bdifferences\b",
            r"\bvs\b",
            r"\bversus\b",
            r"\bbetter\b",
            r"\bpros and cons\b",
            r"\badvantages\b",
            r"\bdisadvantages\b",
        ]

        return any(
            re.search(
                pattern,
                normalized_query,
            )
            for pattern in comparison_patterns
        )