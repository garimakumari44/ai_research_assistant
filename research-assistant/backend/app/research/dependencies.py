from __future__ import annotations

import logging

from fastapi import Request

from app.llm.pipeline import get_llm_pipeline
from app.retrieval.service import RetrievalService
from app.research.pipeline import ResearchPipeline


logger = logging.getLogger(__name__)


def get_research_pipeline(
    request: Request,
) -> ResearchPipeline:
    """
    Build a request-scoped ResearchPipeline using the application's
    shared retrieval indexes and canonical LLM pipeline.

    IMPORTANT:
    Never create a new IndexRegistry here.

    The shared IndexRegistry is created and restored during application
    startup and stored on:

        request.app.state.index_registry
    """

    index_registry = getattr(
        request.app.state,
        "index_registry",
        None,
    )

    if index_registry is None:
        logger.error(
            "Research pipeline requested but app.state.index_registry "
            "is not initialized."
        )

        raise RuntimeError(
            "Shared retrieval IndexRegistry is not initialized."
        )

    retrieval_service = RetrievalService(
        registry=index_registry,
    )

    llm_pipeline = get_llm_pipeline()

    pipeline = ResearchPipeline(
        retrieval_service=retrieval_service,
        llm_pipeline=llm_pipeline,
    )

    logger.debug(
        "ResearchPipeline dependency created: "
        "shared_registry=%s llm_provider=%s",
        type(index_registry).__name__,
        llm_pipeline.provider_name,
    )

    return pipeline