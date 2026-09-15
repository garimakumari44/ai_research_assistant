from typing import Dict, List

from app.retrieval.advanced.models import QueryIntent


class IntentClassifier:
    """
    Classifies user queries into retrieval intents.

    The output controls:

    - retrieval sources
    - ranking strategy
    - query expansion
    - execution pipeline
    """



    def __init__(self):

        self.intent_keywords = {

            QueryIntent.CODING: [
                "code",
                "implementation",
                "github",
                "repository",
                "python",
                "pytorch",
                "tensorflow",
                "example",
                "build"
            ],


            QueryIntent.RESEARCH: [
                "paper",
                "arxiv",
                "research",
                "study",
                "publication",
                "experiment"
            ],


            QueryIntent.COMPARISON: [
                "compare",
                "comparison",
                "difference",
                "vs",
                "versus",
                "better than"
            ],


            QueryIntent.SUMMARY: [
                "summarize",
                "summary",
                "overview",
                "brief"
            ],


            QueryIntent.TROUBLESHOOTING: [
                "error",
                "bug",
                "issue",
                "problem",
                "fix",
                "debug"
            ],


            QueryIntent.EXPLANATION: [
                "explain",
                "how does",
                "why",
                "what is",
                "describe"
            ]

        }



    def classify(
        self,
        query: str
    ) -> QueryIntent:
        """
        Main classification method.

        Uses keyword matching now.

        Later this can be replaced
        with an LLM classifier.
        """


        query = query.lower()


        scores = self._calculate_scores(
            query
        )


        best_intent = max(
            scores,
            key=scores.get
        )


        # If nothing matches,
        # default to factual/explanation

        if scores[best_intent] == 0:

            return QueryIntent.FACTUAL


        return best_intent



    def _calculate_scores(
        self,
        query: str
    ) -> Dict[QueryIntent, int]:
        """
        Calculates confidence score
        for every intent.
        """


        scores = {}


        for intent, keywords in self.intent_keywords.items():

            score = 0


            for keyword in keywords:

                if keyword in query:

                    score += 1


            scores[intent] = score


        return scores



    def classify_with_confidence(
        self,
        query: str
    ) -> Dict:
        """
        Returns intent with confidence score.

        Useful for production systems
        where routing decisions need
        explainability.
        """


        scores = self._calculate_scores(
            query.lower()
        )


        intent = max(
            scores,
            key=scores.get
        )


        total_score = sum(
            scores.values()
        )


        confidence = 0


        if total_score > 0:

            confidence = (
                scores[intent]
                /
                total_score
            )


        return {

            "intent": intent,

            "confidence": round(
                confidence,
                2
            ),

            "scores": scores

        }



    def get_retrieval_strategy(
        self,
        intent: QueryIntent
    ) -> List[str]:
        """
        Maps intent to retrieval strategy.
        """


        strategies = {


            QueryIntent.CODING:
            [
                "github_search",
                "documentation_search",
                "vector_search"
            ],


            QueryIntent.RESEARCH:
            [
                "arxiv_search",
                "paper_search",
                "vector_search"
            ],


            QueryIntent.COMPARISON:
            [
                "multi_document_search",
                "paper_search",
                "documentation_search"
            ],


            QueryIntent.SUMMARY:
            [
                "document_search",
                "vector_search"
            ],


            QueryIntent.TROUBLESHOOTING:
            [
                "github_search",
                "documentation_search",
                "error_search"
            ],


            QueryIntent.EXPLANATION:
            [
                "vector_search",
                "documentation_search"
            ],


            QueryIntent.FACTUAL:
            [
                "vector_search"
            ]

        }


        return strategies.get(
            intent,
            ["vector_search"]
        )