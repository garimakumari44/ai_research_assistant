from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(
    prefix="/graph",
    tags=["Graph"],
)


GRAPH_NODE_TYPES = {
    "paper",
    "topic",
    "method",
    "author",
    "dataset",
}


@router.get("")
async def get_graph(
    depth: int = Query(
        default=2,
        ge=1,
        le=10,
    ),
    node_type: str | None = Query(
        default=None,
    ),
    edge_type: str | None = Query(
        default=None,
    ),
    search: str | None = Query(
        default=None,
    ),
) -> dict[str, Any]:
    """
    Return the research graph.

    This endpoint currently provides the graph API contract expected
    by the frontend. Database-backed graph construction can be added
    as the graph domain/service layer is implemented.
    """

    if node_type and node_type not in GRAPH_NODE_TYPES:
        return {
            "nodes": [],
            "edges": [],
            "total_nodes": 0,
            "total_edges": 0,
            "metadata": {
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "depth": depth,
                "node_type": node_type,
                "edge_type": edge_type,
                "search": search,
            },
        }

    return {
        "nodes": [],
        "edges": [],
        "total_nodes": 0,
        "total_edges": 0,
        "metadata": {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "depth": depth,
            "node_type": node_type,
            "edge_type": edge_type,
            "search": search,
        },
    }