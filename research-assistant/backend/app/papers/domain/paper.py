from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(slots=True)
class PaperAuthor:
    """
    Canonical author representation attached to a paper.
    """

    name: str
    author_id: str | None = None
    orcid: str | None = None
    email: str | None = None
    affiliation: str | None = None
    position: int = 0

    def __post_init__(self) -> None:
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Author name cannot be empty")

        if self.position < 0:
            raise ValueError("Author position cannot be negative")


@dataclass(slots=True)
class PaperCitation:
    """
    Represents a citation relationship between papers.

    source_paper_id -> target_paper_id
    """

    source_paper_id: str
    target_paper_id: str
    citation_type: str = "references"

    def __post_init__(self) -> None:
        self.source_paper_id = self.source_paper_id.strip()
        self.target_paper_id = self.target_paper_id.strip()
        self.citation_type = self.citation_type.strip() or "references"


@dataclass(slots=True)
class Paper:
    """
    Canonical paper domain entity.

    This is the normalized representation used internally by the
    application regardless of which provider supplied the paper.

    Provider-specific identifiers are retained in external_ids.
    """

    id: str | None = None

    title: str = ""
    abstract: str | None = None

    authors: list[PaperAuthor] = field(default_factory=list)

    publication_date: date | None = None

    venue: str | None = None
    journal: str | None = None
    conference: str | None = None

    doi: str | None = None

    url: str | None = None
    pdf_url: str | None = None

    language: str | None = None

    keywords: list[str] = field(default_factory=list)

    categories: list[str] = field(default_factory=list)

    external_ids: dict[str, str] = field(default_factory=dict)

    citation_count: int = 0
    reference_count: int = 0

    source: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.title = self.title.strip()

        if not self.title:
            raise ValueError("Paper title cannot be empty")

        if self.citation_count < 0:
            self.citation_count = 0

        if self.reference_count < 0:
            self.reference_count = 0

        self.doi = self._normalize_doi(self.doi)

        self.keywords = self._normalize_list(self.keywords)
        self.categories = self._normalize_list(self.categories)

        self.external_ids = {
            str(key).strip().lower(): str(value).strip()
            for key, value in self.external_ids.items()
            if key and value
        }

    @staticmethod
    def _normalize_doi(doi: str | None) -> str | None:
        if not doi:
            return None

        value = doi.strip()

        prefixes = (
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
            "DOI:",
        )

        for prefix in prefixes:
            if value.lower().startswith(prefix.lower()):
                value = value[len(prefix):]
                break

        return value.strip().lower() or None

    @staticmethod
    def _normalize_list(values: list[str]) -> list[str]:
        result: list[str] = []

        for value in values:
            if not value:
                continue

            normalized = value.strip()

            if normalized and normalized not in result:
                result.append(normalized)

        return result

    @property
    def first_author(self) -> PaperAuthor | None:
        if not self.authors:
            return None

        return self.authors[0]

    @property
    def author_count(self) -> int:
        return len(self.authors)

    @property
    def canonical_doi(self) -> str | None:
        return self.doi

    @property
    def canonical_key(self) -> str:
        """
        Primary deterministic identity key.

        DOI has highest priority, followed by known external IDs,
        then a normalized title fallback.
        """

        if self.doi:
            return f"doi:{self.doi}"

        for provider in (
            "openalex",
            "semantic_scholar",
            "arxiv",
            "pmid",
            "crossref",
        ):
            external_id = self.external_ids.get(provider)

            if external_id:
                return f"{provider}:{external_id.lower()}"

        normalized_title = " ".join(self.title.lower().split())

        return f"title:{normalized_title}"

    def add_author(self, author: PaperAuthor) -> None:
        self.authors.append(author)

    def add_keyword(self, keyword: str) -> None:
        keyword = keyword.strip()

        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)

    def add_category(self, category: str) -> None:
        category = category.strip()

        if category and category not in self.categories:
            self.categories.append(category)

    def set_external_id(self, provider: str, value: str) -> None:
        provider = provider.strip().lower()
        value = value.strip()

        if not provider or not value:
            return

        self.external_ids[provider] = value

    def merge(self, other: Paper) -> Paper:
        """
        Merge another normalized paper into this paper.

        Existing canonical values are preserved unless missing.
        Collections are unioned.
        """

        if other.doi and not self.doi:
            self.doi = other.doi

        if other.abstract and not self.abstract:
            self.abstract = other.abstract

        if other.url and not self.url:
            self.url = other.url

        if other.pdf_url and not self.pdf_url:
            self.pdf_url = other.pdf_url

        if other.publication_date and not self.publication_date:
            self.publication_date = other.publication_date

        if other.venue and not self.venue:
            self.venue = other.venue

        if other.journal and not self.journal:
            self.journal = other.journal

        if other.conference and not self.conference:
            self.conference = other.conference

        if other.language and not self.language:
            self.language = other.language

        if other.source and not self.source:
            self.source = other.source

        for author in other.authors:
            existing = {
                (
                    item.name.lower(),
                    item.orcid,
                )
                for item in self.authors
            }

            key = (author.name.lower(), author.orcid)

            if key not in existing:
                self.authors.append(author)

        for keyword in other.keywords:
            self.add_keyword(keyword)

        for category in other.categories:
            self.add_category(category)

        for provider, external_id in other.external_ids.items():
            self.external_ids.setdefault(provider, external_id)

        self.citation_count = max(
            self.citation_count,
            other.citation_count,
        )

        self.reference_count = max(
            self.reference_count,
            other.reference_count,
        )

        self.metadata.update(
            {
                key: value
                for key, value in other.metadata.items()
                if key not in self.metadata
            }
        )

        return self