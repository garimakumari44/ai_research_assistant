from __future__ import annotations

import logging
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4

from app.research.models import (
    ResearchQuery,
    RetrievedDocument,
    ResearchSource,
)

logger = logging.getLogger(__name__)


GitHubSearchFunction = Callable[
    [str, int],
    Iterable[Mapping[str, Any]],
]


class GitHubRetriever:
    """
    Retrieves GitHub repositories and implementation examples.

    The actual GitHub API/search implementation is injected through
    ``search_fn``.

    This keeps the research layer independent from HTTP clients and
    GitHub-specific infrastructure.
    """

    def __init__(
        self,
        top_k: int = 5,
        search_fn: GitHubSearchFunction | None = None,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        self.top_k = top_k
        self._search_fn = search_fn

    def retrieve(
        self,
        query: ResearchQuery,
    ) -> list[RetrievedDocument]:
        """
        Retrieve and normalize GitHub repositories.
        """

        if query is None:
            raise ValueError("query cannot be None")

        # ResearchQuery.question is the canonical public/API field.
        query_text = query.question.strip()

        if not query_text:
            raise ValueError("research query cannot be empty")

        repositories = self.search_github(
            query_text,
            top_k=self.top_k,
        )

        documents: list[RetrievedDocument] = []
        seen: set[str] = set()

        for repository in repositories:
            normalized = self._normalize_repository(
                repository
            )

            if normalized is None:
                continue

            dedup_key = self._deduplication_key(
                normalized
            )

            if dedup_key in seen:
                continue

            seen.add(dedup_key)

            try:
                source = ResearchSource(
                    id=str(uuid4()),
                    title=normalized["name"],
                    source_type="github",
                    url=normalized.get("url"),
                    authors=[
                        normalized["owner"]
                    ],
                    content=normalized["content"],
                    metadata={
                        "stars": normalized["stars"],
                        "language": normalized.get("language"),
                        "forks": normalized.get("forks"),
                        "description": normalized.get(
                            "description"
                        ),
                        "category": "implementation",
                        "retrieval_source": "github",
                        **normalized.get("metadata", {}),
                    },
                )

                document = RetrievedDocument(
                    id=str(uuid4()),
                    source=source,
                    text=normalized["content"],
                    score=normalized["score"],
                )

            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Skipping invalid GitHub result",
                    extra={
                        "error": str(exc),
                        "repository": normalized.get("name"),
                    },
                )
                continue

            documents.append(document)

            if len(documents) >= self.top_k:
                break

        logger.info(
            "GitHub retrieval completed: query=%r results=%d",
            query_text,
            len(documents),
        )

        return documents

    def search_github(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[Mapping[str, Any]]:
        """
        Search GitHub repositories.

        No fake repository is returned when a provider is absent.
        """

        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty")

        limit = top_k or self.top_k

        if limit <= 0:
            raise ValueError("top_k must be greater than zero")

        if self._search_fn is None:
            logger.warning(
                "No GitHub search provider configured",
                extra={"query": query},
            )
            return []

        try:
            results = self._search_fn(query, limit)

            if results is None:
                return []

            return list(results)[:limit]

        except Exception:
            logger.exception(
                "GitHub search provider failed",
                extra={"query": query},
            )
            return []

    @staticmethod
    def _normalize_repository(
        repository: Mapping[str, Any] | Any,
    ) -> dict[str, Any] | None:
        if not isinstance(repository, Mapping):
            return None

        name = str(
            repository.get("name")
            or repository.get("full_name")
            or ""
        ).strip()

        content = str(
            repository.get("content")
            or repository.get("readme")
            or repository.get("description")
            or ""
        ).strip()

        if not name or not content:
            return None

        owner_value = (
            repository.get("owner")
            or repository.get("owner_login")
            or "unknown"
        )

        owner = str(owner_value).strip() or "unknown"

        url = repository.get("url")

        if url is not None:
            url = str(url).strip() or None

        language = repository.get("language")

        if language is not None:
            language = str(language).strip() or None

        stars = GitHubRetriever._safe_non_negative_int(
            repository.get("stars", 0)
        )

        forks = GitHubRetriever._safe_non_negative_int(
            repository.get("forks", 0)
        )

        score = GitHubRetriever._safe_score(
            repository.get("score", 0.0)
        )

        metadata = repository.get("metadata", {})

        if not isinstance(metadata, Mapping):
            metadata = {}

        return {
            "name": name,
            "owner": owner,
            "url": url,
            "language": language,
            "stars": stars,
            "forks": forks,
            "description": repository.get(
                "description"
            ),
            "content": content,
            "score": score,
            "metadata": dict(metadata),
        }

    @staticmethod
    def _safe_score(value: Any) -> float:
        try:
            score = float(value)

            if score != score:
                return 0.0

            if score == float("inf") or score == float("-inf"):
                return 0.0

            return max(
                0.0,
                min(1.0, score),
            )

        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_non_negative_int(value: Any) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _deduplication_key(
        repository: Mapping[str, Any],
    ) -> str:
        url = repository.get("url")

        if url:
            return f"url:{str(url).strip().lower()}"

        name = str(
            repository.get("name") or ""
        ).strip().lower()

        return "repository:" + " ".join(
            name.split()
        )