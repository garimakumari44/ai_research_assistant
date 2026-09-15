from typing import List

from app.retrieval.advanced.models import QueryAnalysis


class QueryRewriter:
    """
    Converts user queries into retrieval optimized queries.

    Responsibilities:

    - Expand missing context
    - Add technical keywords
    - Improve search recall
    - Generate alternative queries
    """


    def __init__(self):
        pass


    def rewrite(
        self,
        query: str
    ) -> str:
        """
        Rewrite a single query.

        Example:

        Input:
            Explain LoRA

        Output:
            LoRA Low Rank Adaptation
            parameter efficient fine tuning
            LLM adaptation method
        """


        query = query.strip()


        rewritten_query = (
            f"""
            {query}

            Important retrieval context:

            - definition
            - architecture
            - technical explanation
            - research papers
            - implementation examples
            - documentation
            """
        )


        return rewritten_query.strip()



    def generate_variations(
        self,
        query: str
    ) -> List[str]:
        """
        Generate multiple search variations.

        Useful for hybrid retrieval.

        Example:

        Query:

        "Explain LoRA"


        Returns:

        [
            "LoRA architecture explanation",
            "LoRA paper Low Rank Adaptation",
            "LoRA implementation examples"
        ]
        """


        base = query.strip()


        variations = [

            f"{base} architecture explanation",

            f"{base} research paper",

            f"{base} implementation example",

            f"{base} documentation"

        ]


        return variations



    def analyze(
        self,
        query: str
    ) -> QueryAnalysis:
        """
        Creates initial query analysis object.

        Used by the retrieval planner.
        """


        rewritten = self.rewrite(query)


        variations = self.generate_variations(query)


        return QueryAnalysis(

            original_query=query,

            rewritten_query=rewritten,

            sub_queries=variations

        )