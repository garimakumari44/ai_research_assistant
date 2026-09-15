"""
RAG generation adapters.

This module connects the Adaptive RAG strategies to the existing
application LLM pipeline.

Architecture:

    Adaptive RAG Strategy
            ↓
      RAGAnswerGenerator
            ↓
         LLMPipeline
            ↓
         LLM provider
            ↓
          LLM answer

The generator deliberately does not know anything about retrieval
implementation details. It only converts retrieved documents into
grounded context for the LLM.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from app.llm.pipeline import (
    LLMPipeline,
    get_llm_pipeline,
)


class RAGAnswerGenerator:
    """
    Adapter between BaseRAGStrategy and the application's LLMPipeline.

    BaseRAGStrategy expects:

        generate(query=..., documents=...)

    while LLMPipeline expects:

        generate(prompt, ...)

    This class bridges those two interfaces.
    """

    def __init__(
        self,
        pipeline: LLMPipeline | None = None,
    ) -> None:
        self.pipeline = (
            pipeline
            or get_llm_pipeline()
        )

    # ==================================================================
    # DOCUMENT CONTENT EXTRACTION
    # ==================================================================

    @staticmethod
    def _extract_content(
        document: Any,
    ) -> str:
        """
        Extract textual content from different retrieval-result shapes.

        Supported forms include:

        - dict
        - dict with nested "document"
        - Pydantic/object result
        - object with nested "document"
        - LangChain-style "page_content"
        """

        if document is None:
            return ""

        # --------------------------------------------------------------
        # Dictionary result
        # --------------------------------------------------------------

        if isinstance(
            document,
            Mapping,
        ):
            nested = document.get(
                "document"
            )

            if isinstance(
                nested,
                Mapping,
            ):
                content = (
                    nested.get("content")
                    or nested.get("text")
                    or nested.get("page_content")
                    or ""
                )

                if content:
                    return str(content)

            content = (
                document.get("content")
                or document.get("text")
                or document.get("page_content")
                or ""
            )

            return str(content)

        # --------------------------------------------------------------
        # Object containing nested document
        # --------------------------------------------------------------

        nested_document = getattr(
            document,
            "document",
            None,
        )

        if nested_document is not None:
            content = getattr(
                nested_document,
                "content",
                None,
            )

            if content is None:
                content = getattr(
                    nested_document,
                    "text",
                    None,
                )

            if content is None:
                content = getattr(
                    nested_document,
                    "page_content",
                    None,
                )

            if content:
                return str(content)

        # --------------------------------------------------------------
        # Direct object
        # --------------------------------------------------------------

        content = getattr(
            document,
            "content",
            None,
        )

        if content is None:
            content = getattr(
                document,
                "text",
                None,
            )

        if content is None:
            content = getattr(
                document,
                "page_content",
                None,
            )

        return str(
            content or ""
        )

    # ==================================================================
    # METADATA EXTRACTION
    # ==================================================================

    @staticmethod
    def _extract_metadata(
        document: Any,
    ) -> dict[str, Any]:
        """
        Extract metadata safely from a retrieval result.
        """

        if document is None:
            return {}

        if isinstance(
            document,
            Mapping,
        ):
            metadata = document.get(
                "metadata"
            )

            if isinstance(
                metadata,
                Mapping,
            ):
                return dict(
                    metadata
                )

            nested = document.get(
                "document"
            )

            if isinstance(
                nested,
                Mapping,
            ):
                nested_metadata = nested.get(
                    "metadata"
                )

                if isinstance(
                    nested_metadata,
                    Mapping,
                ):
                    return dict(
                        nested_metadata
                    )

            return {}

        metadata = getattr(
            document,
            "metadata",
            None,
        )

        if isinstance(
            metadata,
            Mapping,
        ):
            return dict(
                metadata
            )

        nested_document = getattr(
            document,
            "document",
            None,
        )

        if nested_document is not None:
            nested_metadata = getattr(
                nested_document,
                "metadata",
                None,
            )

            if isinstance(
                nested_metadata,
                Mapping,
            ):
                return dict(
                    nested_metadata
                )

        return {}

    # ==================================================================
    # ID EXTRACTION
    # ==================================================================

    @staticmethod
    def _extract_id(
        document: Any,
    ) -> str | None:
        """
        Extract a stable identifier from a retrieval result.
        """

        if document is None:
            return None

        # --------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------

        if isinstance(
            document,
            Mapping,
        ):
            nested = document.get(
                "document"
            )

            if isinstance(
                nested,
                Mapping,
            ):
                nested_id = (
                    nested.get("id")
                    or nested.get("chunk_id")
                    or nested.get("document_id")
                )

                if nested_id is not None:
                    return str(
                        nested_id
                    )

            value = (
                document.get("id")
                or document.get("chunk_id")
                or document.get("document_id")
            )

            if value is not None:
                return str(
                    value
                )

            return None

        # --------------------------------------------------------------
        # Nested object
        # --------------------------------------------------------------

        nested_document = getattr(
            document,
            "document",
            None,
        )

        if nested_document is not None:
            nested_id = getattr(
                nested_document,
                "id",
                None,
            )

            if nested_id is None:
                nested_id = getattr(
                    nested_document,
                    "chunk_id",
                    None,
                )

            if nested_id is None:
                nested_id = getattr(
                    nested_document,
                    "document_id",
                    None,
                )

            if nested_id is not None:
                return str(
                    nested_id
                )

        # --------------------------------------------------------------
        # Direct object
        # --------------------------------------------------------------

        value = getattr(
            document,
            "id",
            None,
        )

        if value is None:
            value = getattr(
                document,
                "chunk_id",
                None,
            )

        if value is None:
            value = getattr(
                document,
                "document_id",
                None,
            )

        return (
            str(value)
            if value is not None
            else None
        )

    # ==================================================================
    # CONTEXT BUILDING
    # ==================================================================

    @classmethod
    def _build_context(
        cls,
        documents: Sequence[Any],
    ) -> str:
        """
        Convert retrieved chunks into bounded evidence context.

        Each source is explicitly labelled so the model can distinguish
        individual evidence chunks.
        """

        sections: list[str] = []

        for index, document in enumerate(
            documents,
            start=1,
        ):
            content = cls._extract_content(
                document
            )

            if not content.strip():
                continue

            source_id = cls._extract_id(
                document
            )

            metadata = cls._extract_metadata(
                document
            )

            header = (
                f"[Source {index}]"
            )

            if source_id:
                header += (
                    f" id={source_id}"
                )

            document_name = metadata.get(
                "document_name"
            )

            if document_name:
                header += (
                    f" document={document_name}"
                )

            page_number = metadata.get(
                "page_number"
            )

            if page_number is not None:
                header += (
                    f" page={page_number}"
                )

            sections.append(
                f"{header}\n{content.strip()}"
            )

        return "\n\n".join(
            sections
        )

    # ==================================================================
    # GENERATION OPTION HELPER
    # ==================================================================

    @staticmethod
    def _generation_option(
        kwargs: Mapping[str, Any],
        name: str,
        default: Any,
    ) -> Any:
        """
        Read generation options without accidentally forwarding
        retrieval/runtime parameters to the LLM provider.
        """

        value = kwargs.get(
            name
        )

        if value is None:
            return default

        return value

    # ==================================================================
    # GENERATION
    # ==================================================================

    async def generate(
        self,
        query: str,
        documents: Sequence[Any],
        **kwargs: Any,
    ) -> str:
        """
        Generate a grounded answer from retrieved evidence.

        The LLM receives only:

        - the user query
        - retrieved evidence
        - grounding instructions

        Retrieval/runtime parameters are never blindly forwarded.
        """

        context = self._build_context(
            documents
        )

        if not context.strip():
            return (
                "I could not generate a grounded answer because "
                "the retrieval results did not contain usable text."
            )

        # --------------------------------------------------------------
        # Grounding system prompt
        # --------------------------------------------------------------

        system_prompt = """
You are the answer-generation component of an Adaptive RAG system.

Answer the user's question using ONLY the supplied retrieved evidence.

Rules:

1. Ground factual claims in the supplied evidence.
2. Do not invent facts that are absent from the evidence.
3. If the evidence is insufficient, explicitly say so.
4. Be concise but informative.
5. Synthesize information across multiple sources when useful.
6. Do not mention internal retrieval, embeddings, FAISS, BM25,
   strategies, iterations, or implementation details unless the user
   explicitly asks about them.
7. Do not treat source labels such as [Source 1] as document content.
8. Do not cite information that is not present in the supplied evidence.
9. If sources disagree, clearly acknowledge the disagreement.
"""

        prompt = f"""
Question:
{query}

Retrieved evidence:
{context}

Task:
Answer the question based on the retrieved evidence.
"""

        # --------------------------------------------------------------
        # Generation parameters
        # --------------------------------------------------------------

        model = self._generation_option(
            kwargs,
            "model",
            None,
        )

        temperature = self._generation_option(
            kwargs,
            "temperature",
            0.2,
        )

        max_tokens = self._generation_option(
            kwargs,
            "max_tokens",
            1024,
        )

        top_p = self._generation_option(
            kwargs,
            "top_p",
            None,
        )

        stop = self._generation_option(
            kwargs,
            "stop",
            None,
        )

        pipeline_kwargs: dict[str, Any] = {}

        if model is not None:
            pipeline_kwargs["model"] = model

        if temperature is not None:
            pipeline_kwargs["temperature"] = temperature

        if max_tokens is not None:
            pipeline_kwargs["max_tokens"] = max_tokens

        if top_p is not None:
            pipeline_kwargs["top_p"] = top_p

        if stop is not None:
            pipeline_kwargs["stop"] = stop

        # --------------------------------------------------------------
        # LLM generation
        # --------------------------------------------------------------

        result = await self.pipeline.generate(
            prompt,
            system_prompt=system_prompt,
            **pipeline_kwargs,
        )

        answer = str(
            result.content or ""
        ).strip()

        if not answer:
            raise RuntimeError(
                "RAG answer generator received an empty "
                "LLM response."
            )

        return answer


class RAGAnswerEvaluator:
    """
    Lightweight deterministic evaluator for generated RAG answers.

    This evaluator is intentionally separate from the controller's
    AdaptiveRAGEvaluator.

    Controller evaluator:
        evaluates retrieval/evidence state.

    RAGAnswerEvaluator:
        evaluates whether the generated answer is grounded enough
        for an iterative strategy to decide whether it should stop.

    This is NOT intended to replace a semantic evaluator or
    LLM-as-a-judge system.

    The score is a deterministic heuristic rather than a semantic
    confidence measurement.
    """

    _TOKEN_PATTERN = re.compile(
        r"[A-Za-z0-9][A-Za-z0-9_-]*"
    )

    _STOPWORDS = {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "from",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "into",
        "than",
        "then",
        "they",
        "their",
        "there",
        "about",
        "which",
        "what",
        "when",
        "where",
        "how",
        "why",
        "does",
        "did",
        "can",
        "could",
        "would",
        "should",
        "using",
        "used",
        "use",
    }

    @classmethod
    def _tokens(
        cls,
        text: str,
    ) -> set[str]:
        """
        Tokenize text while removing short/common stopwords.

        Removing common words makes lexical grounding more meaningful
        than simply counting overlap on words such as "the", "and",
        or "using".
        """

        return {
            token.lower()
            for token in cls._TOKEN_PATTERN.findall(
                text
            )
            if len(token) > 2
            and token.lower() not in cls._STOPWORDS
        }

    # ==================================================================
    # EVALUATION
    # ==================================================================

    async def evaluate(
        self,
        query: str,
        answer: str,
        documents: Sequence[Any],
        **_: Any,
    ) -> float:
        """
        Calculate deterministic grounding confidence.

        Components:

        - answer/evidence lexical overlap
        - query/evidence coverage

        Weighting:

        - answer grounding: 70%
        - query coverage: 30%

        The score is bounded to [0, 1].

        Unlike the previous implementation, there is no artificial
        0.50 confidence floor.
        """

        # --------------------------------------------------------------
        # Basic validation
        # --------------------------------------------------------------

        if not answer.strip():
            return 0.0

        if not documents:
            return 0.0

        # --------------------------------------------------------------
        # Build evidence corpus
        # --------------------------------------------------------------

        evidence_parts: list[str] = []

        for document in documents:
            content = (
                RAGAnswerGenerator._extract_content(
                    document
                )
            )

            if content.strip():
                evidence_parts.append(
                    content
                )

        evidence = " ".join(
            evidence_parts
        )

        if not evidence.strip():
            return 0.0

        # --------------------------------------------------------------
        # Tokenization
        # --------------------------------------------------------------

        answer_tokens = self._tokens(
            answer
        )

        evidence_tokens = self._tokens(
            evidence
        )

        query_tokens = self._tokens(
            query
        )

        if not answer_tokens:
            return 0.0

        if not evidence_tokens:
            return 0.0

        # --------------------------------------------------------------
        # Answer grounding
        # --------------------------------------------------------------

        answer_evidence_overlap = (
            len(
                answer_tokens
                & evidence_tokens
            )
            / len(answer_tokens)
        )

        # --------------------------------------------------------------
        # Query coverage
        # --------------------------------------------------------------

        if query_tokens:
            query_evidence_overlap = (
                len(
                    query_tokens
                    & evidence_tokens
                )
                / len(query_tokens)
            )
        else:
            query_evidence_overlap = 1.0

        # --------------------------------------------------------------
        # Weighted confidence
        #
        # Answer grounding:
        #     70%
        #
        # Query coverage:
        #     30%
        # --------------------------------------------------------------

        confidence = (
            0.70
            * answer_evidence_overlap
            + 0.30
            * query_evidence_overlap
        )

        return max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )


__all__ = [
    "RAGAnswerGenerator",
    "RAGAnswerEvaluator",
]