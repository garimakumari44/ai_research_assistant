from __future__ import annotations

import hashlib
import re
from typing import Any


class PaperDeduplicator:
    """
    Generates deterministic identity keys for papers.

    Identifier-based identity is preferred over title-based identity.
    """

    def get_identity_key(self, paper: dict[str, Any]) -> str:
        doi = self._clean_identifier(paper.get("doi"))

        if doi:
            return f"doi:{doi}"

        arxiv_id = self._clean_identifier(
            paper.get("arxiv_id")
        )

        if arxiv_id:
            return f"arxiv:{arxiv_id}"

        pmid = self._clean_identifier(
            paper.get("pmid")
        )

        if pmid:
            return f"pmid:{pmid}"

        provider = paper.get("provider")
        provider_id = paper.get("provider_id")

        if provider and provider_id:
            return (
                f"provider:"
                f"{str(provider).lower().strip()}:"
                f"{str(provider_id).strip()}"
            )

        return self._title_identity(paper)

    def is_same_paper(
        self,
        first: dict[str, Any],
        second: dict[str, Any],
    ) -> bool:
        return (
            self.get_identity_key(first)
            == self.get_identity_key(second)
        )

    def _title_identity(
        self,
        paper: dict[str, Any],
    ) -> str:
        title = paper.get("title") or ""
        year = paper.get("publication_year")

        normalized_title = self._normalize_title(title)

        raw = f"{normalized_title}|{year or ''}"

        digest = hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

        return f"title:{digest}"

    @staticmethod
    def _normalize_title(value: Any) -> str:
        value = str(value).lower().strip()

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    @staticmethod
    def _clean_identifier(value: Any) -> str | None:
        if value is None:
            return None

        value = str(value).strip().lower()

        return value or None