from __future__ import annotations

import inspect
import logging
from typing import Any

from app.adaptive_rag.planner import AdaptiveRAGPlanner
from app.knowledge.indexing.registry import IndexRegistry

from app.retrieval.dense.vector_search import (
    DenseRetriever,
    DenseSearchResult,
)
from app.retrieval.sparse.bm25 import (
    BM25Retriever,
    SparseSearchResult,
)
from app.retrieval.hybrid.fusion import HybridFusion
from app.retrieval.ranking.rrf import ReciprocalRankFusion
from app.retrieval.ranking.cross_encoder import CrossEncoderReranker
from app.retrieval.filters.metadata_filter import MetadataFilter
from app.retrieval.query.processor import QueryProcessor
from app.retrieval.query.router import QueryRouter

from app.retrieval.models import (
    RetrievalMode,
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    RetrievedDocument,
)

logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """
    Canonical end-to-end retrieval pipeline.

    Architecture
    ------------

        RetrievalQuery
              |
              v
        QueryProcessor
              |
              v
        Processed RetrievalQuery
              |
              v
        QueryRouter
              |
              v
        Adaptive Planner
              |
              +-------------------+
              |                   |
              v                   v
        Dense Retrieval      Sparse Retrieval
              |                   |
              +---------+---------+
                        |
                        v
                 Hybrid Fusion
                        |
                        v
                       RRF
                        |
                        v
              Document Resolution
                        |
                        v
               Metadata Filtering
                        |
                        v
              RetrievedChunk adapter
                        |
                        v
                CrossEncoder
                        |
                        v
                  RankingResult
                        |
                        v
                RankedChunk list
                        |
                        v
                 Final Results
                        |
                        v
                RetrievalResponse

    Contract principles
    -------------------
    1. RetrievalQuery is the canonical request.
    2. QueryProcessor receives RetrievalQuery and returns RetrievalQuery.
    3. RRF receives ranked ID lists only.
    4. RRF results are resolved explicitly into documents.
    5. Reranking receives RetrievedChunk objects.
    6. Reranking returns RankingResult.
    7. RankingResult.chunks are explicitly converted back to documents.
    8. RetrievalResult is the canonical final result object.
    9. Index getters may be synchronous OR asynchronous.
    10. QueryRouter is optional; explicit request.mode always wins.

    Important design note
    ---------------------
    This shared pipeline intentionally does NOT apply a hard-coded
    semantic relevance threshold. Different consumers such as Explore,
    Assistant, Adaptive RAG, and Research may require different
    relevance policies.

    Research-specific relevance gating belongs in ResearchPipeline.
    """


    def __init__(
        self,
        *,
        documents: list[Any] | None = None,
        index_registry: IndexRegistry | None = None,
    ) -> None:
        if index_registry is None:
            raise ValueError(
                "RetrievalPipeline requires a shared IndexRegistry."
            )

        self.index_registry = index_registry
        self.documents = list(documents or [])

        # --------------------------------------------------------------
        # Retrieval engines
        # --------------------------------------------------------------

        self.dense_retriever = DenseRetriever(
            vector_index=self.index_registry.vector,
        )

        self.sparse_retriever = BM25Retriever(
            keyword_index=self.index_registry.keyword,
        )

        # --------------------------------------------------------------
        # Fusion / ranking
        # --------------------------------------------------------------

        self.hybrid_fusion = HybridFusion()
        self.rrf = ReciprocalRankFusion()
        self.metadata_filter = MetadataFilter()
        self.reranker = CrossEncoderReranker()

        # --------------------------------------------------------------
        # Query intelligence
        # --------------------------------------------------------------

        self.planner = AdaptiveRAGPlanner()
        self.query_processor = QueryProcessor()
        self.query_router = QueryRouter()

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    async def retrieve(
        self,
        request: RetrievalQuery,
    ) -> RetrievalResponse:
        """
        Execute the complete retrieval pipeline.
        """

        if not isinstance(request, RetrievalQuery):
            raise TypeError(
                "request must be an instance of RetrievalQuery."
            )

        original_query = request.query.strip()

        if not original_query:
            raise ValueError(
                "Retrieval query must not be empty."
            )

        requested_top_k = max(
            1,
            min(
                int(request.top_k),
                100,
            ),
        )

        # ============================================================== 
        # 1. QUERY PROCESSING
        # ==============================================================

        processed_request = self.query_processor.process(
            request
        )

        if inspect.isawaitable(processed_request):
            processed_request = await processed_request

        if not isinstance(
            processed_request,
            RetrievalQuery,
        ):
            raise TypeError(
                "QueryProcessor.process() must return RetrievalQuery."
            )

        processed_query = processed_request.query.strip()

        if not processed_query:
            processed_query = original_query

            processed_request = self._copy_request(
                processed_request,
                query=processed_query,
            )

        logger.info(
            "Retrieval query processed. original=%r processed=%r",
            original_query,
            processed_query,
        )

        # ============================================================== 
        # 2. QUERY ROUTING
        # ==============================================================

        routed_mode = await self._route_query(
            request=processed_request,
        )

        logger.info(
            "Retrieval query routed. mode=%r",
            routed_mode,
        )

        # ============================================================== 
        # 3. RETRIEVAL MODE
        # ==============================================================

        mode = self._resolve_mode(
            request=processed_request,
            routed_mode=routed_mode,
        )

        logger.info(
            "Retrieval mode resolved. mode=%s",
            mode,
        )

        # ============================================================== 
        # 4. ADAPTIVE PLANNING
        # ==============================================================

        plan = await self._create_plan(
            query=processed_query,
            request=processed_request,
            mode=mode,
            top_k=requested_top_k,
        )

        self._set_plan_attribute(
            plan,
            "mode",
            mode,
        )

        self._set_plan_attribute(
            plan,
            "top_k",
            requested_top_k,
        )

        self._set_plan_attribute(
            plan,
            "filters",
            dict(
                processed_request.filters or {}
            ),
        )

        logger.info(
            "Adaptive retrieval plan created: %r",
            plan,
        )

        # ============================================================== 
        # 5. DENSE RETRIEVAL
        # ==============================================================

        dense_results: list[DenseSearchResult] = []

        if mode in {
            "dense",
            "vector",
            "hybrid",
        }:
            dense_results = await self._retrieve_dense(
                query=processed_query,
                top_k=requested_top_k,
            )

        logger.info(
            "Dense retrieval candidates=%d",
            len(dense_results),
        )

        # ============================================================== 
        # 6. SPARSE RETRIEVAL
        # ==============================================================

        sparse_results: list[SparseSearchResult] = []

        if mode in {
            "sparse",
            "keyword",
            "bm25",
            "hybrid",
        }:
            sparse_results = await self._retrieve_sparse(
                query=processed_query,
                top_k=requested_top_k,
                filters=processed_request.filters,
            )

        logger.info(
            "Sparse retrieval candidates=%d",
            len(sparse_results),
        )

        # ============================================================== 
        # 7. HYBRID FUSION
        # ==============================================================

        fused_results = self._fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            mode=mode,
        )

        logger.info(
            "Hybrid fusion candidates=%d",
            len(fused_results),
        )

        # ============================================================== 
        # 8. RECIPROCAL RANK FUSION
        # ==============================================================

        ranked_results = self._apply_rrf(
            dense_results=dense_results,
            sparse_results=sparse_results,
            fused_results=fused_results,
            mode=mode,
            top_k=requested_top_k,
        )

        logger.info(
            "RRF candidates=%d",
            len(ranked_results),
        )

        # ============================================================== 
        # 9. DOCUMENT RESOLUTION
        # ==============================================================

        retrieved_documents = await self._convert_documents(
            ranked_results
        )

        logger.info(
            "Resolved documents=%d",
            len(retrieved_documents),
        )

        # ============================================================== 
        # 10. METADATA FILTERING
        # ==============================================================

        filtered_documents = self._apply_metadata_filter(
            retrieved_documents,
            filters=processed_request.filters,
        )

        logger.info(
            "Documents after metadata filtering=%d",
            len(filtered_documents),
        )

        # ============================================================== 
        # 11. CROSS-ENCODER RERANKING
        # ==============================================================

        reranking_enabled = bool(
            getattr(
                processed_request,
                "enable_reranking",
                False,
            )
        )

        reranked_documents = await self._apply_reranker(
            query=processed_query,
            documents=filtered_documents,
            top_k=requested_top_k,
            enabled=reranking_enabled,
        )

        logger.info(
            "Documents after reranking=%d",
            len(reranked_documents),
        )

        # ============================================================== 
        # 12. FINAL TOP-K
        # ==============================================================

        final_documents = reranked_documents[
            :requested_top_k
        ]

        # ============================================================== 
        # 13. CANONICAL RESULT CONSTRUCTION
        # ==============================================================

        results = self._build_results(
            documents=final_documents,
            query=original_query,
            mode=mode,
        )

        logger.info(
            "Canonical retrieval results=%d",
            len(results),
        )

        # ============================================================== 
        # 14. RESPONSE
        # ==============================================================

        return RetrievalResponse(
            query=original_query,
            results=results,
            retrieval_mode=self._coerce_retrieval_mode(
                mode
            ),
            metadata={
                "original_query": original_query,
                "processed_query": processed_query,
                "dense_candidates": len(
                    dense_results
                ),
                "sparse_candidates": len(
                    sparse_results
                ),
                "fused_candidates": len(
                    fused_results
                ),
                "ranked_candidates": len(
                    ranked_results
                ),
                "resolved_documents": len(
                    retrieved_documents
                ),
                "filtered_documents": len(
                    filtered_documents
                ),
                "final_results": len(
                    results
                ),
                "reranker_enabled": reranking_enabled,
                "reranker_name": getattr(
                    self.reranker,
                    "model_name",
                    self.reranker.__class__.__name__,
                ),
                "query_metadata": dict(
                    processed_request.metadata or {}
                ),
                "plan": self._serialize_plan(
                    plan
                ),
            },
        )

    # ==================================================================
    # QUERY ROUTING
    # ==================================================================

    async def _route_query(
        self,
        *,
        request: RetrievalQuery,
    ) -> str | None:
        """
        Route the processed RetrievalQuery.
        """

        router = self.query_router

        method_names = (
            "route",
            "resolve",
            "classify",
            "select",
            "determine",
        )

        method = None
        method_name = None

        for candidate_name in method_names:
            candidate = getattr(
                router,
                candidate_name,
                None,
            )

            if callable(candidate):
                method = candidate
                method_name = candidate_name
                break

        if method is None:
            logger.debug(
                "QueryRouter has no compatible routing method. "
                "Using request mode/default mode."
            )
            return None

        try:
            try:
                result = method(
                    request=request
                )
            except TypeError:
                try:
                    result = method(
                        query=request.query
                    )
                except TypeError:
                    result = method(
                        request.query
                    )

            if inspect.isawaitable(result):
                result = await result

        except Exception:
            logger.exception(
                "Query routing failed using %s(). "
                "Falling back to request mode.",
                method_name,
            )
            return None

        if result is None:
            return None

        if isinstance(
            result,
            RetrievalMode,
        ):
            return result.value

        if isinstance(
            result,
            str,
        ):
            return result.lower().strip()

        result_mode = getattr(
            result,
            "mode",
            None,
        )

        if isinstance(
            result_mode,
            RetrievalMode,
        ):
            return result_mode.value

        if isinstance(
            result_mode,
            str,
        ):
            return result_mode.lower().strip()

        if isinstance(
            result,
            dict,
        ):
            result_mode = result.get(
                "mode"
            )

            if isinstance(
                result_mode,
                RetrievalMode,
            ):
                return result_mode.value

            if isinstance(
                result_mode,
                str,
            ):
                return result_mode.lower().strip()

        return None

    # ==================================================================
    # MODE RESOLUTION
    # ==================================================================

    def _resolve_mode(
        self,
        *,
        request: RetrievalQuery,
        routed_mode: str | None,
    ) -> str:
        """
        Resolve retrieval mode.

        Explicit RetrievalQuery.mode has priority over the router.
        """

        request_mode = request.mode

        if isinstance(
            request_mode,
            RetrievalMode,
        ):
            return request_mode.value

        if isinstance(
            request_mode,
            str,
        ):
            normalized = request_mode.lower().strip()

            if normalized:
                return normalized

        if hasattr(
            request_mode,
            "value",
        ):
            normalized = str(
                request_mode.value
            ).lower().strip()

            if normalized:
                return normalized

        if routed_mode:
            normalized = routed_mode.lower().strip()

            if normalized:
                return normalized

        return "hybrid"

    # ==================================================================
    # ADAPTIVE PLANNING
    # ==================================================================

    async def _create_plan(
        self,
        *,
        query: str,
        request: RetrievalQuery,
        mode: str,
        top_k: int,
    ) -> Any:
        """
        Create an adaptive retrieval plan.
        """

        method = getattr(
            self.planner,
            "plan",
            None,
        )

        if method is None:
            logger.warning(
                "AdaptiveRAGPlanner does not expose plan()."
            )

            return self._fallback_plan(
                mode=mode,
                top_k=top_k,
                filters=request.filters,
            )

        try:
            try:
                result = method(
                    query=query,
                    top_k=top_k,
                    filters=dict(
                        request.filters or {}
                    ),
                )

            except TypeError:
                result = method(
                    query
                )

            if inspect.isawaitable(result):
                result = await result

        except Exception:
            logger.exception(
                "Adaptive planning failed. "
                "Using fallback plan."
            )

            return self._fallback_plan(
                mode=mode,
                top_k=top_k,
                filters=request.filters,
            )

        if result is None:
            return self._fallback_plan(
                mode=mode,
                top_k=top_k,
                filters=request.filters,
            )

        return result

    # ==================================================================
    # DENSE RETRIEVAL
    # ==================================================================

    async def _retrieve_dense(
        self,
        *,
        query: str,
        top_k: int,
    ) -> list[DenseSearchResult]:
        """
        Execute dense vector retrieval.
        """

        try:
            result = self.dense_retriever.search(
                query=query,
                top_k=top_k,
            )

            if inspect.isawaitable(result):
                result = await result

            if result is None:
                return []

            return list(result)

        except Exception:
            logger.exception(
                "Dense retrieval failed. "
                "query=%r top_k=%d",
                query,
                top_k,
            )
            return []

    # ==================================================================
    # SPARSE RETRIEVAL
    # ==================================================================

    async def _retrieve_sparse(
        self,
        *,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> list[SparseSearchResult]:
        """
        Execute BM25 retrieval.
        """

        try:
            result = self.sparse_retriever.search(
                query=query,
                top_k=top_k,
                filters=filters,
            )

            if inspect.isawaitable(result):
                result = await result

            if result is None:
                return []

            return list(result)

        except Exception:
            logger.exception(
                "Sparse retrieval failed. "
                "query=%r top_k=%d",
                query,
                top_k,
            )
            return []

    # ==================================================================
    # HYBRID FUSION
    # ==================================================================

    def _fuse(
        self,
        *,
        dense_results: list[DenseSearchResult],
        sparse_results: list[SparseSearchResult],
        mode: str,
    ) -> list[Any]:
        """
        Perform hybrid fusion.

        RRF remains a separate ranking stage.
        """

        if mode in {
            "dense",
            "vector",
        }:
            return list(
                dense_results
            )

        if mode in {
            "sparse",
            "keyword",
            "bm25",
        }:
            return list(
                sparse_results
            )

        if not dense_results:
            return list(
                sparse_results
            )

        if not sparse_results:
            return list(
                dense_results
            )

        try:
            result = self.hybrid_fusion.fuse(
                dense_results=dense_results,
                sparse_results=sparse_results,
            )

        except TypeError:
            try:
                result = self.hybrid_fusion.fuse(
                    dense_results,
                    sparse_results,
                )

            except Exception:
                logger.exception(
                    "Hybrid fusion failed. "
                    "Using unique merged candidates."
                )

                return self._merge_unique_results(
                    dense_results,
                    sparse_results,
                )

        except Exception:
            logger.exception(
                "Hybrid fusion failed. "
                "Using unique merged candidates."
            )

            return self._merge_unique_results(
                dense_results,
                sparse_results,
            )

        if result is None:
            return self._merge_unique_results(
                dense_results,
                sparse_results,
            )

        return list(result)

    # ==================================================================
    # RECIPROCAL RANK FUSION
    # ==================================================================

    def _apply_rrf(
        self,
        *,
        dense_results: list[DenseSearchResult],
        sparse_results: list[SparseSearchResult],
        fused_results: list[Any],
        mode: str,
        top_k: int,
    ) -> list[Any]:
        """
        Apply Reciprocal Rank Fusion.

        ReciprocalRankFusion.fuse() receives ranked ID lists.
        """

        if not fused_results:
            return []

        if mode in {
            "dense",
            "vector",
            "sparse",
            "keyword",
            "bm25",
        }:
            return list(
                fused_results[:top_k]
            )

        dense_ids = self._extract_result_ids(
            dense_results
        )

        sparse_ids = self._extract_result_ids(
            sparse_results
        )

        rankings: list[list[str]] = []

        if dense_ids:
            rankings.append(
                dense_ids
            )

        if sparse_ids:
            rankings.append(
                sparse_ids
            )

        if not rankings:
            return list(
                fused_results[:top_k]
            )

        try:
            rrf_results = self.rrf.fuse(
                rankings
            )

        except Exception:
            logger.exception(
                "RRF failed. Falling back to fused candidates."
            )

            return list(
                fused_results[:top_k]
            )

        if not rrf_results:
            logger.warning(
                "RRF returned zero candidates. "
                "Falling back to fused candidates."
            )

            return list(
                fused_results[:top_k]
            )

        return list(
            rrf_results[:top_k]
        )

    # ==================================================================
    # DOCUMENT RESOLUTION
    # ==================================================================

    async def _convert_documents(
        self,
        results: list[Any],
    ) -> list[Any]:
        """
        Resolve retrieval result IDs into actual documents.
        """

        if not results:
            return []

        resolved: list[Any] = []

        for result in results:
            result_id = self._result_id(
                result
            )

            if result_id is None:
                logger.warning(
                    "Skipping retrieval result without ID: %r",
                    result,
                )
                continue

            document = await self._resolve_document(
                result_id
            )

            if document is None:
                logger.warning(
                    "Unable to resolve retrieval ID=%s",
                    result_id,
                )
                continue

            resolved.append(
                self._attach_score(
                    document,
                    result,
                )
            )

        return resolved

    # ==================================================================
    # DOCUMENT LOOKUP
    # ==================================================================

    async def _resolve_document(
        self,
        result_id: Any,
    ) -> Any | None:
        """
        Resolve a retrieval ID against known documents and indexes.
        """

        key = str(
            result_id
        )

        # --------------------------------------------------------------
        # Explicit document snapshot
        # --------------------------------------------------------------

        for document in self.documents:
            if isinstance(
                document,
                dict,
            ):
                document_id = document.get(
                    "id"
                )

                if document_id is None:
                    document_id = document.get(
                        "chunk_id"
                    )

            else:
                document_id = getattr(
                    document,
                    "id",
                    None,
                )

                if document_id is None:
                    document_id = getattr(
                        document,
                        "chunk_id",
                        None,
                    )

            if (
                document_id is not None
                and str(document_id) == key
            ):
                return document

        # --------------------------------------------------------------
        # Keyword index
        # --------------------------------------------------------------

        keyword_item = await self._get_keyword_item(
            result_id
        )

        if keyword_item is not None:
            document = self._item_to_document(
                keyword_item
            )

            if document is not None:
                return document

        # --------------------------------------------------------------
        # Vector index
        # --------------------------------------------------------------

        vector_item = await self._get_vector_item(
            result_id
        )

        if vector_item is not None:
            document = self._item_to_document(
                vector_item
            )

            if document is not None:
                return document

        return None

    # ==================================================================
    # KEYWORD INDEX
    # ==================================================================

    async def _get_keyword_item(
        self,
        chunk_id: Any,
    ) -> Any | None:
        """
        Retrieve an item from the keyword index.
        """

        index = self.index_registry.keyword

        getter = getattr(
            index,
            "get",
            None,
        )

        if callable(getter):
            try:
                result = getter(
                    chunk_id
                )

                if inspect.isawaitable(result):
                    result = await result

                if result is not None:
                    return result

            except Exception:
                logger.debug(
                    "Keyword index get() failed "
                    "for chunk_id=%s",
                    chunk_id,
                    exc_info=True,
                )

        items = getattr(
            index,
            "_items",
            None,
        )

        if isinstance(
            items,
            dict,
        ):
            return (
                items.get(
                    str(chunk_id)
                )
                or items.get(
                    chunk_id
                )
            )

        return None

    # ==================================================================
    # VECTOR INDEX
    # ==================================================================

    async def _get_vector_item(
        self,
        chunk_id: Any,
    ) -> Any | None:
        """
        Retrieve an item from the vector index.
        """

        index = self.index_registry.vector

        getter = getattr(
            index,
            "get",
            None,
        )

        if callable(getter):
            try:
                result = getter(
                    chunk_id
                )

                if inspect.isawaitable(result):
                    result = await result

                if result is not None:
                    return result

            except Exception:
                logger.debug(
                    "Vector index get() failed "
                    "for chunk_id=%s",
                    chunk_id,
                    exc_info=True,
                )

        items = getattr(
            index,
            "_items",
            None,
        )

        if isinstance(
            items,
            dict,
        ):
            return (
                items.get(
                    str(chunk_id)
                )
                or items.get(
                    chunk_id
                )
            )

        return None

    # ==================================================================
    # ITEM -> DOCUMENT
    # ==================================================================

    def _item_to_document(
        self,
        item: Any,
    ) -> dict[str, Any] | None:
        """
        Normalize an index item into a retrieval document.
        """

        if item is None:
            return None

        if isinstance(
            item,
            dict,
        ):
            text = item.get(
                "text"
            )

            if text is None:
                text = item.get(
                    "content"
                )

            chunk_id = item.get(
                "chunk_id"
            )

            if chunk_id is None:
                chunk_id = item.get(
                    "id"
                )

            metadata = item.get(
                "metadata"
            ) or {}

            document_id = item.get(
                "document_id"
            )

            paper_id = item.get(
                "paper_id"
            )

        else:
            text = getattr(
                item,
                "text",
                None,
            )

            if text is None:
                text = getattr(
                    item,
                    "content",
                    None,
                )

            chunk_id = getattr(
                item,
                "chunk_id",
                None,
            )

            if chunk_id is None:
                chunk_id = getattr(
                    item,
                    "id",
                    None,
                )

            metadata = getattr(
                item,
                "metadata",
                None,
            ) or {}

            document_id = getattr(
                item,
                "document_id",
                None,
            )

            paper_id = getattr(
                item,
                "paper_id",
                None,
            )

        if not isinstance(
            text,
            str,
        ):
            return None

        text = text.strip()

        if not text:
            return None

        if chunk_id is None:
            return None

        metadata = (
            dict(metadata)
            if isinstance(
                metadata,
                dict,
            )
            else {}
        )

        if document_id is None:
            document_id = metadata.get(
                "document_id"
            )

        if paper_id is None:
            paper_id = metadata.get(
                "paper_id"
            )

        return {
            "id": str(
                chunk_id
            ),
            "chunk_id": str(
                chunk_id
            ),
            "document_id": self._string_or_none(
                document_id
            ),
            "paper_id": self._string_or_none(
                paper_id
            ),
            "content": text,
            "text": text,
            "metadata": metadata,
        }

    # ==================================================================
    # SCORE ATTACHMENT
    # ==================================================================

    def _attach_score(
        self,
        document: Any,
        result: Any,
    ) -> Any:
        """
        Attach retrieval/ranking scores to a document.
        """

        score = self._get_result_attribute(
            result,
            "score",
        )

        vector_score = self._get_result_attribute(
            result,
            "vector_score",
        )

        keyword_score = self._get_result_attribute(
            result,
            "keyword_score",
        )

        rerank_score = self._get_result_attribute(
            result,
            "rerank_score",
        )

        if isinstance(
            document,
            dict,
        ):
            output = dict(
                document
            )

            metadata = output.get(
                "metadata"
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}
            else:
                metadata = dict(
                    metadata
                )

            if score is not None:
                output["score"] = self._safe_float(
                    score
                )

            if vector_score is not None:
                output["vector_score"] = self._safe_float(
                    vector_score
                )

            if keyword_score is not None:
                output["keyword_score"] = self._safe_float(
                    keyword_score
                )

            if rerank_score is not None:
                output["rerank_score"] = self._safe_float(
                    rerank_score
                )

            if score is not None:
                metadata["original_retrieval_score"] = (
                    self._safe_float(score)
                )

            if vector_score is not None:
                metadata["vector_score"] = self._safe_float(
                    vector_score
                )

            if keyword_score is not None:
                metadata["keyword_score"] = self._safe_float(
                    keyword_score
                )

            if rerank_score is not None:
                metadata["rerank_score"] = self._safe_float(
                    rerank_score
                )

            output["metadata"] = metadata

            return output

        return document

    # ==================================================================
    # RESULT ID
    # ==================================================================

    @staticmethod
    def _result_id(
        result: Any,
    ) -> Any | None:
        """
        Extract an ID from strings, dictionaries, or result objects.
        """

        if result is None:
            return None

        if isinstance(
            result,
            str,
        ):
            return result

        if isinstance(
            result,
            dict,
        ):
            result_id = result.get(
                "id"
            )

            if result_id is None:
                result_id = result.get(
                    "chunk_id"
                )

            return result_id

        result_id = getattr(
            result,
            "id",
            None,
        )

        if result_id is None:
            result_id = getattr(
                result,
                "chunk_id",
                None,
            )

        return result_id

    # ==================================================================
    # METADATA FILTER
    # ==================================================================

    def _apply_metadata_filter(
        self,
        documents: list[Any],
        *,
        filters: dict[str, Any] | None,
    ) -> list[Any]:
        """
        Apply metadata filters.
        """

        if not documents:
            return []

        if not filters:
            return list(
                documents
            )

        try:
            result = self.metadata_filter.apply(
                documents,
                filters=filters,
            )

        except TypeError:
            try:
                result = self.metadata_filter.apply(
                    documents,
                    filters,
                )

            except Exception:
                logger.exception(
                    "Metadata filtering failed. "
                    "Returning unfiltered documents."
                )

                return list(
                    documents
                )

        except Exception:
            logger.exception(
                "Metadata filtering failed. "
                "Returning unfiltered documents."
            )

            return list(
                documents
            )

        if result is None:
            return list(
                documents
            )

        return list(
            result
        )

    # ==================================================================
    # RERANKING
    # ==================================================================

    async def _apply_reranker(
        self,
        *,
        query: str,
        documents: list[Any],
        top_k: int,
        enabled: bool,
    ) -> list[Any]:
        """
        Apply the CrossEncoder reranker.
        """

        if not documents:
            return []

        if not enabled:
            logger.info(
                "CrossEncoder reranking disabled."
            )

            return list(
                documents
            )

        method = getattr(
            self.reranker,
            "rerank",
            None,
        )

        if method is None:
            logger.error(
                "CrossEncoderReranker does not expose rerank()."
            )

            return list(
                documents
            )

        chunks = self._documents_to_reranker_chunks(
            documents
        )

        if not chunks:
            logger.warning(
                "No valid RetrievedChunk objects available "
                "for reranking."
            )

            return list(
                documents
            )

        try:
            ranking_result = method(
                query=query,
                chunks=chunks,
                top_k=top_k,
            )

            if inspect.isawaitable(
                ranking_result
            ):
                ranking_result = await ranking_result

        except Exception:
            logger.exception(
                "CrossEncoder reranking failed. "
                "Returning pre-reranked documents."
            )

            return list(
                documents
            )

        if ranking_result is None:
            logger.warning(
                "CrossEncoder returned None. "
                "Returning pre-reranked documents."
            )

            return list(
                documents
            )

        return self._apply_ranking_result(
            result=ranking_result,
            original_documents=documents,
        )

    # ==================================================================
    # DOCUMENT -> RERANKER CHUNK
    # ==================================================================

    def _documents_to_reranker_chunks(
        self,
        documents: list[Any],
    ) -> list[Any]:
        """
        Convert pipeline documents into RetrievedChunk objects.
        """

        from app.retrieval.ranking.models import (
            RetrievedChunk,
        )

        chunks: list[RetrievedChunk] = []

        for document in documents:
            normalized = self._normalize_document(
                document
            )

            if normalized is None:
                continue

            chunk = self._build_retrieved_chunk(
                RetrievedChunk,
                normalized,
            )

            if chunk is not None:
                chunks.append(
                    chunk
                )

        return chunks

    def _build_retrieved_chunk(
        self,
        chunk_model: Any,
        document: RetrievedDocument,
    ) -> Any | None:
        """
        Build the canonical ranking-layer RetrievedChunk.
        """

        data = {
            "id": document.id,
            "text": document.text,
            "score": document.score,
            "source_id": document.source_id,
            "document_id": document.document_id,
            "chunk_id": document.chunk_id,
            "paper_id": document.paper_id,
            "source": document.source,
            "title": document.title,
            "author": document.author,
            "metadata": dict(
                document.metadata
            ),
        }

        if hasattr(
            chunk_model,
            "model_fields",
        ):
            allowed_fields = set(
                chunk_model.model_fields.keys()
            )

            filtered_data = {
                key: value
                for key, value in data.items()
                if key in allowed_fields
            }

            try:
                return chunk_model(
                    **filtered_data
                )

            except Exception:
                logger.debug(
                    "Unable to construct RetrievedChunk "
                    "with canonical fields.",
                    exc_info=True,
                )

        try:
            return chunk_model(
                **data
            )

        except Exception:
            logger.debug(
                "Unable to construct RetrievedChunk.",
                exc_info=True,
            )

        return None

    # ==================================================================
    # RANKING RESULT -> DOCUMENTS
    # ==================================================================

    def _apply_ranking_result(
        self,
        *,
        result: Any,
        original_documents: list[Any],
    ) -> list[Any]:
        """
        Convert RankingResult into pipeline documents.

        IMPORTANT:
            The original retrieval score is captured BEFORE the
            CrossEncoder score replaces document["score"].

        Final score semantics:

            score
                Final reranker score when available.

            rerank_score
                Raw CrossEncoder score.

            metadata.original_retrieval_score
                Score produced before CrossEncoder reranking.

            vector_score
                Dense retrieval score.

            keyword_score
                Sparse/BM25 retrieval score.
        """

        ranked_chunks = getattr(
            result,
            "chunks",
            None,
        )

        if ranked_chunks is None:
            logger.error(
                "CrossEncoder returned a result without "
                "RankingResult.chunks. type=%s",
                type(result).__name__,
            )

            return list(
                original_documents
            )

        ranked_chunks = list(
            ranked_chunks
        )

        if not ranked_chunks:
            return []

        # --------------------------------------------------------------
        # Map original documents by chunk/document ID.
        # --------------------------------------------------------------

        original_by_id: dict[str, Any] = {}

        for document in original_documents:
            document_id = self._result_id(
                document
            )

            if document_id is None:
                continue

            original_by_id[
                str(document_id)
            ] = document

        # --------------------------------------------------------------
        # Apply reranking order.
        # --------------------------------------------------------------

        output: list[Any] = []

        for rank, ranked_chunk in enumerate(
            ranked_chunks,
            start=1,
        ):
            chunk_id = self._result_id(
                ranked_chunk
            )

            if chunk_id is None:
                continue

            key = str(
                chunk_id
            )

            original = original_by_id.get(
                key
            )

            if original is None:
                logger.debug(
                    "Reranked chunk %s was not found "
                    "in original documents.",
                    key,
                )
                continue

            # ----------------------------------------------------------
            # Copy original document.
            # ----------------------------------------------------------

            if isinstance(
                original,
                dict,
            ):
                document = dict(
                    original
                )
            else:
                document = self._document_to_dict(
                    original
                )

            # ----------------------------------------------------------
            # IMPORTANT FIX:
            #
            # Capture original retrieval score BEFORE replacing
            # document["score"] with rerank_score.
            # ----------------------------------------------------------

            original_retrieval_score = (
                self._get_result_attribute(
                    original,
                    "score",
                )
            )

            if original_retrieval_score is None:
                original_retrieval_score = document.get(
                    "score"
                )

            original_retrieval_score = (
                self._optional_float(
                    original_retrieval_score
                )
            )

            # ----------------------------------------------------------
            # Preserve vector score.
            # ----------------------------------------------------------

            vector_score = self._get_result_attribute(
                original,
                "vector_score",
            )

            if vector_score is None:
                vector_score = document.get(
                    "vector_score"
                )

            if vector_score is not None:
                vector_score = self._safe_float(
                    vector_score
                )

                document["vector_score"] = (
                    vector_score
                )

            # ----------------------------------------------------------
            # Preserve keyword score.
            # ----------------------------------------------------------

            keyword_score = self._get_result_attribute(
                original,
                "keyword_score",
            )

            if keyword_score is None:
                keyword_score = document.get(
                    "keyword_score"
                )

            if keyword_score is not None:
                keyword_score = self._safe_float(
                    keyword_score
                )

                document["keyword_score"] = (
                    keyword_score
                )

            # ----------------------------------------------------------
            # Extract CrossEncoder score.
            # ----------------------------------------------------------

            rerank_score = self._get_result_attribute(
                ranked_chunk,
                "rerank_score",
            )

            if rerank_score is None:
                rerank_score = self._get_result_attribute(
                    ranked_chunk,
                    "score",
                )

            rerank_score = self._optional_float(
                rerank_score
            )

            # ----------------------------------------------------------
            # Ranking metadata.
            # ----------------------------------------------------------

            document["rank"] = rank

            metadata = document.get(
                "metadata"
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}
            else:
                metadata = dict(
                    metadata
                )

            metadata["rank"] = rank

            # ----------------------------------------------------------
            # Preserve original retrieval score.
            # ----------------------------------------------------------

            if original_retrieval_score is not None:
                metadata[
                    "original_retrieval_score"
                ] = original_retrieval_score

            # ----------------------------------------------------------
            # Store CrossEncoder score separately.
            # ----------------------------------------------------------

            if rerank_score is not None:
                document["rerank_score"] = (
                    rerank_score
                )

                document["score"] = (
                    rerank_score
                )

                metadata[
                    "rerank_score"
                ] = rerank_score

            # ----------------------------------------------------------
            # Preserve vector score in metadata.
            # ----------------------------------------------------------

            if vector_score is not None:
                metadata[
                    "vector_score"
                ] = vector_score

            # ----------------------------------------------------------
            # Preserve keyword score in metadata.
            # ----------------------------------------------------------

            if keyword_score is not None:
                metadata[
                    "keyword_score"
                ] = keyword_score

            document["metadata"] = metadata

            output.append(
                document
            )

        return output

    # ==================================================================
    # RESULT BUILDING
    # ==================================================================

    def _build_results(
        self,
        *,
        documents: list[Any],
        query: str,
        mode: str,
    ) -> list[RetrievalResult]:
        """
        Convert normalized documents into RetrievalResult objects.
        """

        if not documents:
            return []

        retrieval_mode = self._coerce_retrieval_mode(
            mode
        )

        results: list[RetrievalResult] = []

        for rank, document in enumerate(
            documents,
            start=1,
        ):
            normalized = self._normalize_document(
                document
            )

            if normalized is None:
                continue

            score = self._safe_float(
                self._get_result_attribute(
                    document,
                    "score",
                ),
                default=0.0,
            )

            vector_score = self._optional_float(
                self._get_result_attribute(
                    document,
                    "vector_score",
                )
            )

            keyword_score = self._optional_float(
                self._get_result_attribute(
                    document,
                    "keyword_score",
                )
            )

            rerank_score = self._optional_float(
                self._get_result_attribute(
                    document,
                    "rerank_score",
                )
            )

            metadata = dict(
                normalized.metadata
            )

            results.append(
                RetrievalResult(
                    document=normalized,
                    rank=rank,
                    score=score,
                    vector_score=vector_score,
                    keyword_score=keyword_score,
                    rerank_score=rerank_score,
                    retrieval_method=retrieval_mode,
                    metadata=metadata,
                )
            )

        return results

    # ==================================================================
    # DOCUMENT NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_document(
        document: Any,
    ) -> RetrievedDocument | None:
        """
        Normalize a document-like object into RetrievedDocument.
        """

        if isinstance(
            document,
            RetrievedDocument,
        ):
            return document

        if not isinstance(
            document,
            dict,
        ):
            try:
                document = {
                    "id": getattr(
                        document,
                        "id",
                        None,
                    ),
                    "chunk_id": getattr(
                        document,
                        "chunk_id",
                        None,
                    ),
                    "document_id": getattr(
                        document,
                        "document_id",
                        None,
                    ),
                    "paper_id": getattr(
                        document,
                        "paper_id",
                        None,
                    ),
                    "text": getattr(
                        document,
                        "text",
                        "",
                    ),
                    "metadata": getattr(
                        document,
                        "metadata",
                        {},
                    ),
                    "score": getattr(
                        document,
                        "score",
                        0.0,
                    ),
                    "vector_score": getattr(
                        document,
                        "vector_score",
                        None,
                    ),
                    "keyword_score": getattr(
                        document,
                        "keyword_score",
                        None,
                    ),
                    "rerank_score": getattr(
                        document,
                        "rerank_score",
                        None,
                    ),
                }

            except Exception:
                return None

        document_id = document.get(
            "id"
        )

        chunk_id = document.get(
            "chunk_id"
        )

        if document_id is None:
            document_id = chunk_id

        if document_id is None:
            return None

        text = document.get(
            "text"
        )

        if text is None:
            text = document.get(
                "content",
                "",
            )

        if not isinstance(
            text,
            str,
        ):
            return None

        text = text.strip()

        if not text:
            return None

        metadata = document.get(
            "metadata"
        ) or {}

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        source_id = (
            document.get(
                "source_id"
            )
            or metadata.get(
                "source_id"
            )
        )

        resolved_document_id = (
            document.get(
                "document_id"
            )
            or metadata.get(
                "document_id"
            )
        )

        paper_id = (
            document.get(
                "paper_id"
            )
            or metadata.get(
                "paper_id"
            )
        )

        source = (
            document.get(
                "source"
            )
            or metadata.get(
                "source"
            )
        )

        title = (
            document.get(
                "title"
            )
            or metadata.get(
                "title"
            )
        )

        author = (
            document.get(
                "author"
            )
            or metadata.get(
                "author"
            )
        )

        return RetrievedDocument(
            id=str(
                document_id
            ),
            text=text,
            score=RetrievalPipeline._safe_float(
                document.get(
                    "score"
                ),
                default=0.0,
            ),
            source_id=RetrievalPipeline._string_or_none(
                source_id
            ),
            document_id=RetrievalPipeline._string_or_none(
                resolved_document_id
            ),
            chunk_id=RetrievalPipeline._string_or_none(
                chunk_id
            ),
            paper_id=RetrievalPipeline._string_or_none(
                paper_id
            ),
            source=RetrievalPipeline._string_or_none(
                source
            ),
            title=RetrievalPipeline._string_or_none(
                title
            ),
            author=RetrievalPipeline._string_or_none(
                author
            ),
            metadata=dict(
                metadata
            ),
        )

    # ==================================================================
    # REQUEST COPY
    # ==================================================================

    @staticmethod
    def _copy_request(
        request: RetrievalQuery,
        **updates: Any,
    ) -> RetrievalQuery:
        """
        Copy RetrievalQuery without dropping future fields.
        """

        if hasattr(
            request,
            "model_copy",
        ):
            return request.model_copy(
                update=updates
            )

        if hasattr(
            request,
            "model_dump",
        ):
            data = request.model_dump()

        else:
            data = {
                field_name: getattr(
                    request,
                    field_name,
                )
                for field_name in (
                    "query",
                    "top_k",
                    "filters",
                    "mode",
                    "vector_weight",
                    "keyword_weight",
                    "metadata",
                    "enable_reranking",
                )
                if hasattr(
                    request,
                    field_name,
                )
            }

        data.update(
            updates
        )

        return RetrievalQuery(
            **data
        )

    # ==================================================================
    # RESULT IDS
    # ==================================================================

    @staticmethod
    def _extract_result_ids(
        results: list[Any],
    ) -> list[str]:
        """
        Extract ranked IDs from search results.
        """

        ids: list[str] = []
        seen: set[str] = set()

        for result in results:
            result_id = RetrievalPipeline._result_id(
                result
            )

            if result_id is None:
                continue

            key = str(
                result_id
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            ids.append(
                key
            )

        return ids

    # ==================================================================
    # UNIQUE MERGE
    # ==================================================================

    @staticmethod
    def _merge_unique_results(
        *result_lists: list[Any],
    ) -> list[Any]:
        """
        Merge result lists while preserving first occurrence.
        """

        output: list[Any] = []
        seen: set[str] = set()

        for results in result_lists:
            for result in results:
                result_id = RetrievalPipeline._result_id(
                    result
                )

                if result_id is None:
                    continue

                key = str(
                    result_id
                )

                if key in seen:
                    continue

                seen.add(
                    key
                )

                output.append(
                    result
                )

        return output

    # ==================================================================
    # RESULT ATTRIBUTE
    # ==================================================================

    @staticmethod
    def _get_result_attribute(
        result: Any,
        name: str,
    ) -> Any:
        if isinstance(
            result,
            dict,
        ):
            return result.get(
                name
            )

        return getattr(
            result,
            name,
            None,
        )

    # ==================================================================
    # DOCUMENT -> DICT
    # ==================================================================

    @staticmethod
    def _document_to_dict(
        document: Any,
    ) -> dict[str, Any]:
        if isinstance(
            document,
            dict,
        ):
            return dict(
                document
            )

        if hasattr(
            document,
            "model_dump",
        ):
            try:
                return document.model_dump()

            except Exception:
                pass

        return {
            "id": getattr(
                document,
                "id",
                None,
            ),
            "chunk_id": getattr(
                document,
                "chunk_id",
                None,
            ),
            "document_id": getattr(
                document,
                "document_id",
                None,
            ),
            "paper_id": getattr(
                document,
                "paper_id",
                None,
            ),
            "text": getattr(
                document,
                "text",
                "",
            ),
            "metadata": getattr(
                document,
                "metadata",
                {},
            ),
            "score": getattr(
                document,
                "score",
                0.0,
            ),
            "vector_score": getattr(
                document,
                "vector_score",
                None,
            ),
            "keyword_score": getattr(
                document,
                "keyword_score",
                None,
            ),
            "rerank_score": getattr(
                document,
                "rerank_score",
                None,
            ),
        }

    # ==================================================================
    # FLOAT HELPERS
    # ==================================================================

    @staticmethod
    def _safe_float(
        value: Any,
        *,
        default: float = 0.0,
    ) -> float:
        try:
            number = float(
                value
            )

            if number != number:
                return default

            if abs(number) == float(
                "inf"
            ):
                return default

            return number

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return default

    @staticmethod
    def _optional_float(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        return RetrievalPipeline._safe_float(
            value,
            default=0.0,
        )

    # ==================================================================
    # STRING HELPER
    # ==================================================================

    @staticmethod
    def _string_or_none(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        value = str(
            value
        ).strip()

        return value or None

    # ==================================================================
    # RETRIEVAL MODE
    # ==================================================================

    @staticmethod
    def _coerce_retrieval_mode(
        mode: str | RetrievalMode,
    ) -> RetrievalMode:
        if isinstance(
            mode,
            RetrievalMode,
        ):
            return mode

        normalized = str(
            mode
        ).lower().strip()

        aliases = {
            "vector": RetrievalMode.DENSE,
            "dense": RetrievalMode.DENSE,
            "keyword": RetrievalMode.BM25,
            "sparse": RetrievalMode.BM25,
            "bm25": RetrievalMode.BM25,
            "hybrid": RetrievalMode.HYBRID,
        }

        return aliases.get(
            normalized,
            RetrievalMode.HYBRID,
        )

    # ==================================================================
    # PLAN HELPERS
    # ==================================================================

    @staticmethod
    def _set_plan_attribute(
        plan: Any,
        name: str,
        value: Any,
    ) -> None:
        try:
            setattr(
                plan,
                name,
                value,
            )

        except Exception:
            logger.debug(
                "Unable to set plan.%s",
                name,
                exc_info=True,
            )

    @staticmethod
    def _serialize_plan(
        plan: Any,
    ) -> Any:
        if plan is None:
            return None

        if hasattr(
            plan,
            "model_dump",
        ):
            try:
                return plan.model_dump(
                    mode="json"
                )

            except Exception:
                pass

        if isinstance(
            plan,
            dict,
        ):
            return dict(
                plan
            )

        try:
            return vars(
                plan
            )

        except TypeError:
            return str(
                plan
            )

    @staticmethod
    def _fallback_plan(
        *,
        mode: str,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> Any:
        return type(
            "RetrievalPlanFallback",
            (),
            {
                "mode": mode,
                "top_k": top_k,
                "filters": dict(
                    filters or {}
                ),
            },
        )()


__all__ = [
    "RetrievalPipeline",
]