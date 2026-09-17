from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.papers import router as papers_router
from app.api.routes.retrieval import router as retrieval_router
from app.api.routes.graph import router as graph_router
from app.api.routes.research import router as research_router
from app.api.routes.collections import router as collections_router
from app.api.routes.reports import router as reports_router
from app.api.routes.assistant import router as assistant_router


api_router = APIRouter(
    prefix="/api/v1",
)


# ============================================================
# AUTHENTICATION
# ============================================================

api_router.include_router(
    auth_router,
)


# ============================================================
# PAPERS
# ============================================================

api_router.include_router(
    papers_router,
)


# ============================================================
# DOCUMENTS
# ============================================================

api_router.include_router(
    documents_router,
)


# ============================================================
# RETRIEVAL
# ============================================================

api_router.include_router(
    retrieval_router,
)


# ============================================================
# GRAPH
# ============================================================

api_router.include_router(
    graph_router,
)


# ============================================================
# RESEARCH
# ============================================================

api_router.include_router(
    research_router,
)


# ============================================================
# COLLECTIONS
# ============================================================

api_router.include_router(
    collections_router,
)


# ============================================================
# ASSISTANT
# ============================================================

api_router.include_router(
    assistant_router,
)


# ============================================================
# RESEARCH REPORTS
# ============================================================

api_router.include_router(
    reports_router,
)