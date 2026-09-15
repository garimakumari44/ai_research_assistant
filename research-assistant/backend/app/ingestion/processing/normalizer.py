from __future__ import annotations

import re
from typing import Any


class PaperNormalizer:
    """
    Normalizes raw provider paper records into a consistent structure.

    The normalizer does not validate whether the paper is acceptable.
    It only cleans and standardizes values.
    """

    def normalize(self, paper: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(paper, dict):
            raise TypeError("Paper must be a dictionary")

        normalized = dict(paper)

        normalized["title"] = self._normalize_title(
            normalized.get("title")
        )

        normalized["abstract"] = self._normalize_text(
            normalized.get("abstract")
        )

        normalized["doi"] = self._normalize_doi(
            normalized.get("doi")
        )

        normalized["arxiv_id"] = self._normalize_identifier(
            normalized.get("arxiv_id")
        )

        normalized["pmid"] = self._normalize_identifier(
            normalized.get("pmid")
        )

        normalized["url"] = self._normalize_url(
            normalized.get("url")
        )

        normalized["venue"] = self._normalize_text(
            normalized.get("venue")
        )

        normalized["publisher"] = self._normalize_text(
            normalized.get("publisher")
        )

        normalized["authors"] = self._normalize_authors(
            normalized.get("authors")
        )

        normalized["keywords"] = self._normalize_list(
            normalized.get("keywords")
        )

        normalized["topics"] = self._normalize_list(
            normalized.get("topics")
        )

        return normalized

    @staticmethod
    def _normalize_title(value: Any) -> str | None:
        if value is None:
            return None

        value = str(value)
        value = re.sub(r"\s+", " ", value)
        value = value.strip()

        return value or None

    @staticmethod
    def _normalize_text(value: Any) -> str | None:
        if value is None:
            return None

        value = str(value)
        value = re.sub(r"\s+", " ", value)
        value = value.strip()

        return value or None

    @staticmethod
    def _normalize_doi(value: Any) -> str | None:
        if value is None:
            return None

        doi = str(value).strip()

        doi = re.sub(
            r"^(https?://)?(dx\.)?doi\.org/",
            "",
            doi,
            flags=re.IGNORECASE,
        )

        doi = doi.strip().rstrip(".")
        doi = doi.lower()

        return doi or None

    @staticmethod
    def _normalize_identifier(value: Any) -> str | None:
        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @staticmethod
    def _normalize_url(value: Any) -> str | None:
        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @staticmethod
    def _normalize_authors(value: Any) -> list[dict[str, Any]]:
        if not value:
            return []

        if not isinstance(value, list):
            return []

        normalized_authors: list[dict[str, Any]] = []

        for author in value:
            if isinstance(author, str):
                name = re.sub(r"\s+", " ", author).strip()

                if name:
                    normalized_authors.append(
                        {
                            "name": name,
                        }
                    )

                continue

            if not isinstance(author, dict):
                continue

            normalized_author = dict(author)

            if normalized_author.get("name"):
                normalized_author["name"] = re.sub(
                    r"\s+",
                    " ",
                    str(normalized_author["name"]),
                ).strip()

            normalized_authors.append(normalized_author)

        return normalized_authors

    @staticmethod
    def _normalize_list(value: Any) -> list[str]:
        if not value:
            return []

        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            return []

        result: list[str] = []

        for item in value:
            if item is None:
                continue

            item = re.sub(r"\s+", " ", str(item)).strip()

            if item and item not in result:
                result.append(item)

        return result