from __future__ import annotations

from typing import Any


class PaperValidationError(ValueError):
    """Raised when a paper fails validation."""


class PaperValidator:
    """
    Validates normalized paper records.

    Validation is intentionally conservative:
    a paper needs enough identity information to be persisted and
    deduplicated, but optional metadata is allowed to be missing.
    """

    def validate(self, paper: dict[str, Any]) -> None:
        if not isinstance(paper, dict):
            raise PaperValidationError(
                "Paper must be a dictionary"
            )

        title = paper.get("title")

        if not title:
            raise PaperValidationError(
                "Paper title is required"
            )

        if not isinstance(title, str):
            raise PaperValidationError(
                "Paper title must be a string"
            )

        if len(title.strip()) < 2:
            raise PaperValidationError(
                "Paper title is too short"
            )

        self._validate_authors(paper.get("authors"))
        self._validate_identifiers(paper)

    def _validate_authors(self, authors: Any) -> None:
        if authors is None:
            return

        if not isinstance(authors, list):
            raise PaperValidationError(
                "Authors must be a list"
            )

        for author in authors:
            if not isinstance(author, dict):
                raise PaperValidationError(
                    "Each author must be an object"
                )

            name = author.get("name")

            if name is not None and not isinstance(name, str):
                raise PaperValidationError(
                    "Author name must be a string"
                )

    def _validate_identifiers(
        self,
        paper: dict[str, Any],
    ) -> None:
        doi = paper.get("doi")

        if doi is not None and not isinstance(doi, str):
            raise PaperValidationError(
                "DOI must be a string"
            )

        arxiv_id = paper.get("arxiv_id")

        if arxiv_id is not None and not isinstance(arxiv_id, str):
            raise PaperValidationError(
                "arxiv_id must be a string"
            )

        pmid = paper.get("pmid")

        if pmid is not None and not isinstance(pmid, str):
            raise PaperValidationError(
                "pmid must be a string"
            )