from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable, Optional


@dataclass(frozen=True, slots=True)
class Author:
    """Normalized document author."""

    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


@dataclass(slots=True)
class DocumentMetadata:
    """
    Normalized metadata describing a document.

    This model is provider-agnostic and can represent metadata
    originating from arXiv, Crossref, Semantic Scholar, PDFs,
    or other document providers.
    """

    document_id: str

    title: Optional[str] = None

    authors: list[Author] = field(default_factory=list)

    abstract: Optional[str] = None

    doi: Optional[str] = None
    arxiv_id: Optional[str] = None

    journal: Optional[str] = None
    conference: Optional[str] = None
    publisher: Optional[str] = None

    language: Optional[str] = None

    publication_date: Optional[date] = None

    keywords: list[str] = field(default_factory=list)

    categories: list[str] = field(default_factory=list)

    url: Optional[str] = None

    page_count: Optional[int] = None

    document_type: Optional[str] = None

    source: Optional[str] = None

    extra: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_author(self, author: Author) -> None:
        """Add an author if they are not already present."""

        if author not in self.authors:
            self.authors.append(author)

    def add_keyword(self, keyword: str) -> None:
        """Add a normalized keyword."""

        value = keyword.strip()

        if value and value.lower() not in {
            item.lower() for item in self.keywords
        }:
            self.keywords.append(value)

    def add_category(self, category: str) -> None:
        """Add a normalized category."""

        value = category.strip()

        if value and value.lower() not in {
            item.lower() for item in self.categories
        }:
            self.categories.append(value)

    @property
    def author_names(self) -> list[str]:
        """Return author names in document order."""

        return [author.name for author in self.authors]

    @property
    def author_count(self) -> int:
        """Return the number of authors."""

        return len(self.authors)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert metadata into a JSON-friendly dictionary.
        """

        return {
            "document_id": self.document_id,
            "title": self.title,
            "authors": [
                {
                    "name": author.name,
                    "given_name": author.given_name,
                    "family_name": author.family_name,
                    "affiliation": author.affiliation,
                    "orcid": author.orcid,
                }
                for author in self.authors
            ],
            "abstract": self.abstract,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "journal": self.journal,
            "conference": self.conference,
            "publisher": self.publisher,
            "language": self.language,
            "publication_date": (
                self.publication_date.isoformat()
                if self.publication_date
                else None
            ),
            "keywords": list(self.keywords),
            "categories": list(self.categories),
            "url": self.url,
            "page_count": self.page_count,
            "document_type": self.document_type,
            "source": self.source,
            "extra": dict(self.extra),
            "created_at": self.created_at.isoformat(),
        }


class MetadataNormalizer:
    """
    Normalizes raw metadata coming from external providers.
    """

    @staticmethod
    def normalize_title(title: Optional[str]) -> Optional[str]:
        if not title:
            return None

        value = " ".join(title.split())

        return value.strip()

    @staticmethod
    def normalize_abstract(
        abstract: Optional[str],
    ) -> Optional[str]:
        if not abstract:
            return None

        value = " ".join(abstract.split())

        return value.strip()

    @staticmethod
    def normalize_doi(doi: Optional[str]) -> Optional[str]:
        if not doi:
            return None

        value = doi.strip()

        prefixes = (
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
        )

        lowered = value.lower()

        for prefix in prefixes:
            if lowered.startswith(prefix):
                value = value[len(prefix):]
                break

        return value.strip().rstrip("/")

    @staticmethod
    def normalize_arxiv_id(
        arxiv_id: Optional[str],
    ) -> Optional[str]:
        if not arxiv_id:
            return None

        value = arxiv_id.strip()

        prefixes = (
            "https://arxiv.org/abs/",
            "http://arxiv.org/abs/",
            "https://arxiv.org/pdf/",
            "http://arxiv.org/pdf/",
            "arxiv:",
        )

        lowered = value.lower()

        for prefix in prefixes:
            if lowered.startswith(prefix):
                value = value[len(prefix):]
                break

        if value.lower().endswith(".pdf"):
            value = value[:-4]

        return value.strip()

    @staticmethod
    def normalize_keywords(
        keywords: Optional[Iterable[str]],
    ) -> list[str]:
        if not keywords:
            return []

        result: list[str] = []
        seen: set[str] = set()

        for keyword in keywords:
            value = " ".join(keyword.split()).strip()

            if not value:
                continue

            key = value.lower()

            if key not in seen:
                seen.add(key)
                result.append(value)

        return result

    @classmethod
    def normalize(
        cls,
        metadata: DocumentMetadata,
    ) -> DocumentMetadata:
        """
        Normalize fields in an existing metadata object.
        """

        metadata.title = cls.normalize_title(metadata.title)

        metadata.abstract = cls.normalize_abstract(
            metadata.abstract
        )

        metadata.doi = cls.normalize_doi(metadata.doi)

        metadata.arxiv_id = cls.normalize_arxiv_id(
            metadata.arxiv_id
        )

        metadata.keywords = cls.normalize_keywords(
            metadata.keywords
        )

        metadata.categories = cls.normalize_keywords(
            metadata.categories
        )

        return metadata