from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


# ======================================================================
# RESOLVED PAPER DATA
# ======================================================================


@dataclass(frozen=True)
class ResolvedPaperIdentity:
    """
    Canonical identity information for a paper.

    This object contains only identity-level information.
    It does not represent the complete Paper domain model.
    """

    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    openalex_id: str | None = None


@dataclass(frozen=True)
class ResolvedPaperMetadata:
    """
    Normalized metadata selected from a provider response.
    """

    title: str | None = None
    abstract: str | None = None
    publication_year: int | None = None
    venue: str | None = None
    publisher: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class ResolvedPaper:
    """
    Canonical result returned by PaperResolver.

    The resolver does not perform:
        - database access
        - persistence
        - deduplication
        - HTTP requests
        - provider API calls
    """

    identity: ResolvedPaperIdentity
    metadata: ResolvedPaperMetadata
    authors: tuple[str, ...] = ()
    source: str | None = None
    source_id: str | None = None


# ======================================================================
# PAPER RESOLVER
# ======================================================================


class PaperResolver:
    """
    Resolves and normalizes paper metadata coming from external providers.

    Responsibilities:
        - Normalize paper identifiers.
        - Extract canonical identifiers.
        - Select the best available metadata.
        - Normalize URLs.
        - Normalize authors.
        - Produce deterministic output.

    Non-responsibilities:
        - Database access.
        - Persistence.
        - Deduplication across database records.
        - HTTP requests.
        - Provider API calls.

    Provider-specific fetching belongs under:

        app/ingestion/providers/

    Cross-provider deduplication belongs under:

        app/ingestion/processing/
    """

    # ==================================================================
    # NORMALIZATION CONSTANTS
    # ==================================================================

    DOI_PREFIXES = (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
        "DOI:",
    )

    ARXIV_URL_PREFIXES = (
        "https://arxiv.org/abs/",
        "http://arxiv.org/abs/",
        "https://arxiv.org/pdf/",
        "http://arxiv.org/pdf/",
        "arxiv:",
        "ARXIV:",
    )

    PMID_URL_PREFIXES = (
        "https://pubmed.ncbi.nlm.nih.gov/",
        "http://pubmed.ncbi.nlm.nih.gov/",
        "pmid:",
        "PMID:",
    )

    OPENALEX_URL_PREFIXES = (
        "https://openalex.org/",
        "http://openalex.org/",
        "openalex:",
        "OPENALEX:",
    )

    # ==================================================================
    # RESOLVE
    # ==================================================================

    def resolve(
        self,
        record: Mapping[str, Any],
        *,
        source: str | None = None,
    ) -> ResolvedPaper:
        """
        Resolve a provider record into normalized paper information.

        Parameters
        ----------
        record:
            Provider-specific paper record.

        source:
            Optional explicit provider/source name.

        Returns
        -------
        ResolvedPaper
            Fully normalized paper information.
        """

        identity = self._resolve_identity(record)

        metadata = self._resolve_metadata(record)

        authors = self._resolve_authors(record)

        source_name = self._normalize_string(
            source
            or self._first_value(
                record,
                "source",
                "provider",
                "source_name",
            )
        )

        source_id = self._normalize_string(
            self._first_value(
                record,
                "source_id",
                "provider_id",
                "id",
            )
        )

        return ResolvedPaper(
            identity=identity,
            metadata=metadata,
            authors=tuple(authors),
            source=source_name,
            source_id=source_id,
        )

    # ==================================================================
    # PUBLIC NORMALIZATION API
    # ==================================================================

    def normalize_doi(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize a DOI.

        Examples:

            10.48550/arXiv.1706.03762
            https://doi.org/10.48550/arXiv.1706.03762
            doi:10.48550/arXiv.1706.03762
        """

        return self._normalize_doi(value)

    def normalize_arxiv_id(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize an arXiv identifier.
        """

        return self._normalize_arxiv_id(value)

    def normalize_pmid(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize a PubMed identifier.
        """

        return self._normalize_pmid(value)

    def normalize_openalex_id(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize an OpenAlex work identifier.
        """

        return self._normalize_openalex_id(value)

    def normalize_title(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize a paper title.
        """

        return self._normalize_title(value)

    def normalize_abstract(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize an abstract.
        """

        return self._normalize_abstract(value)

    def normalize_url(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize and validate a URL.
        """

        return self._normalize_url(value)

    def normalize_string(
        self,
        value: Any,
    ) -> str | None:
        """
        Generic string normalization.
        """

        return self._normalize_string(value)

    # ==================================================================
    # IDENTITY
    # ==================================================================

    def _resolve_identity(
        self,
        record: Mapping[str, Any],
    ) -> ResolvedPaperIdentity:
        """
        Resolve all supported canonical identifiers.

        All identifiers are normalized independently.
        """

        doi = self._resolve_doi(record)

        arxiv_id = self._resolve_arxiv_id(record)

        pmid = self._resolve_pmid(record)

        openalex_id = self._resolve_openalex_id(record)

        return ResolvedPaperIdentity(
            doi=doi,
            arxiv_id=arxiv_id,
            pmid=pmid,
            openalex_id=openalex_id,
        )

    # ==================================================================
    # DOI
    # ==================================================================

    def _resolve_doi(
        self,
        record: Mapping[str, Any],
    ) -> str | None:

        value = self._first_value(
            record,
            "doi",
            "DOI",
            "doi_url",
        )

        if not value:
            return None

        return self._normalize_doi(value)

    # ==================================================================
    # ARXIV
    # ==================================================================

    def _resolve_arxiv_id(
        self,
        record: Mapping[str, Any],
    ) -> str | None:

        value = self._first_value(
            record,
            "arxiv_id",
            "arxiv",
            "arxivId",
            "arxiv_url",
        )

        if not value:
            return None

        return self._normalize_arxiv_id(value)

    # ==================================================================
    # PMID
    # ==================================================================

    def _resolve_pmid(
        self,
        record: Mapping[str, Any],
    ) -> str | None:

        value = self._first_value(
            record,
            "pmid",
            "pubmed_id",
            "pubmedId",
            "pubmed_url",
        )

        if not value:
            return None

        return self._normalize_pmid(value)

    # ==================================================================
    # OPENALEX
    # ==================================================================

    def _resolve_openalex_id(
        self,
        record: Mapping[str, Any],
    ) -> str | None:

        value = self._first_value(
            record,
            "openalex_id",
            "openalex",
            "openalexId",
            "openalex_url",
        )

        if not value:
            return None

        return self._normalize_openalex_id(value)

    # ==================================================================
    # METADATA
    # ==================================================================

    def _resolve_metadata(
        self,
        record: Mapping[str, Any],
    ) -> ResolvedPaperMetadata:

        title = self._normalize_title(
            self._first_value(
                record,
                "title",
                "paper_title",
                "name",
            )
        )

        abstract = self._normalize_abstract(
            self._first_value(
                record,
                "abstract",
                "abstract_text",
                "summary",
                "description",
            )
        )

        publication_year = self._resolve_publication_year(
            record
        )

        venue = self._normalize_string(
            self._first_value(
                record,
                "venue",
                "journal",
                "journal_name",
                "container_title",
                "publication",
            )
        )

        publisher = self._normalize_string(
            self._first_value(
                record,
                "publisher",
                "publisher_name",
            )
        )

        url = self._resolve_url(record)

        return ResolvedPaperMetadata(
            title=title,
            abstract=abstract,
            publication_year=publication_year,
            venue=venue,
            publisher=publisher,
            url=url,
        )

    # ==================================================================
    # PUBLICATION YEAR
    # ==================================================================

    def _resolve_publication_year(
        self,
        record: Mapping[str, Any],
    ) -> int | None:

        value = self._first_value(
            record,
            "publication_year",
            "year",
            "published_year",
            "publicationYear",
            "published",
            "publication_date",
            "published_date",
        )

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value if 1000 <= value <= 2100 else None

        text = str(value).strip()

        if not text:
            return None

        match = re.search(
            r"\b(1[0-9]{3}|20[0-9]{2}|2100)\b",
            text,
        )

        if not match:
            return None

        year = int(match.group(1))

        if 1000 <= year <= 2100:
            return year

        return None

    # ==================================================================
    # URL
    # ==================================================================

    def _resolve_url(
        self,
        record: Mapping[str, Any],
    ) -> str | None:
        """
        Prefer a canonical DOI URL when DOI is available.

        Otherwise use the provider's paper URL.
        """

        doi = self._resolve_doi(record)

        if doi:
            return f"https://doi.org/{doi}"

        value = self._first_value(
            record,
            "url",
            "paper_url",
            "landing_page",
            "landing_page_url",
            "web_url",
            "link",
        )

        if not value:
            return None

        return self._normalize_url(value)

    # ==================================================================
    # AUTHORS
    # ==================================================================

    def _resolve_authors(
        self,
        record: Mapping[str, Any],
    ) -> list[str]:
        """
        Normalize author names from common provider formats.

        Supported examples:

            ["John Smith", "Jane Doe"]

            [
                {"name": "John Smith"},
                {"name": "Jane Doe"}
            ]

            [
                {"author": {"display_name": "John Smith"}}
            ]

            [
                {"display_name": "John Smith"}
            ]

            "John Smith, Jane Doe"
        """

        raw_authors = self._first_value(
            record,
            "authors",
            "author",
            "author_list",
            "author_names",
        )

        if not raw_authors:
            return []

        if isinstance(raw_authors, str):
            return self._normalize_author_string(
                raw_authors
            )

        if isinstance(raw_authors, Mapping):
            raw_authors = [raw_authors]

        if not isinstance(raw_authors, Sequence):
            return []

        authors: list[str] = []

        for raw_author in raw_authors:

            name = self._extract_author_name(
                raw_author
            )

            if not name:
                continue

            normalized = self._normalize_string(
                name
            )

            if (
                normalized
                and normalized not in authors
            ):
                authors.append(normalized)

        return authors

    # ==================================================================
    # AUTHOR NAME EXTRACTION
    # ==================================================================

    def _extract_author_name(
        self,
        author: Any,
    ) -> str | None:

        if isinstance(author, str):
            return author

        if not isinstance(author, Mapping):
            return None

        direct_name = self._first_value(
            author,
            "name",
            "display_name",
            "full_name",
            "author_name",
        )

        if direct_name:
            return str(direct_name)

        nested_author = author.get("author")

        if isinstance(
            nested_author,
            Mapping,
        ):

            nested_name = self._first_value(
                nested_author,
                "name",
                "display_name",
                "full_name",
            )

            if nested_name:
                return str(nested_name)

        # Common OpenAlex format:
        #
        # {
        #     "author": {
        #         "id": "...",
        #         "display_name": "..."
        #     }
        # }
        #
        # Already handled above.

        # Common Semantic Scholar-like format:
        #
        # {
        #     "authorId": "...",
        #     "name": "..."
        # }
        #
        # Already handled by direct_name.

        return None

    # ==================================================================
    # AUTHOR STRING
    # ==================================================================

    def _normalize_author_string(
        self,
        value: str,
    ) -> list[str]:
        """
        Handle simple comma/semicolon separated
        author strings.
        """

        parts = re.split(
            r"\s*[,;]\s*",
            value,
        )

        authors: list[str] = []

        for part in parts:

            normalized = self._normalize_string(
                part
            )

            if (
                normalized
                and normalized not in authors
            ):
                authors.append(normalized)

        return authors

    # ==================================================================
    # DOI NORMALIZATION
    # ==================================================================

    def _normalize_doi(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        doi = str(value).strip()

        if not doi:
            return None

        for prefix in self.DOI_PREFIXES:

            if doi.lower().startswith(
                prefix.lower()
            ):

                doi = doi[len(prefix):]

                break

        doi = doi.strip()

        doi = doi.rstrip(
            ".,; "
        )

        # Handle cases such as:
        #
        # doi.org/10.xxxx/xxxxx
        #
        if doi.lower().startswith(
            "doi.org/"
        ):
            doi = doi[8:]

        if doi.lower().startswith(
            "dx.doi.org/"
        ):
            doi = doi[11:]

        if not doi:
            return None

        # Basic DOI validation.
        #
        # DOI syntax begins with:
        #
        # 10.<registrant>/<suffix>
        #
        if not re.match(
            r"^10\.\d{4,9}/\S+$",
            doi,
            re.IGNORECASE,
        ):
            return None

        # DOI comparison is case-insensitive.
        return doi.lower()

    # ==================================================================
    # ARXIV NORMALIZATION
    # ==================================================================

    def _normalize_arxiv_id(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        arxiv_id = str(value).strip()

        if not arxiv_id:
            return None

        for prefix in self.ARXIV_URL_PREFIXES:

            if arxiv_id.lower().startswith(
                prefix.lower()
            ):

                arxiv_id = arxiv_id[
                    len(prefix):
                ]

                break

        arxiv_id = arxiv_id.strip()

        arxiv_id = arxiv_id.rstrip(
            ".,; "
        )

        # Remove query strings/fragments that may
        # accidentally be attached to an arXiv URL.
        arxiv_id = arxiv_id.split(
            "?",
            1,
        )[0]

        arxiv_id = arxiv_id.split(
            "#",
            1,
        )[0]

        # Remove version suffix.
        #
        # 1706.03762v7
        # becomes
        # 1706.03762
        arxiv_id = re.sub(
            r"v\d+$",
            "",
            arxiv_id,
            flags=re.IGNORECASE,
        )

        if not arxiv_id:
            return None

        # Modern arXiv IDs:
        #
        #     1234.56789
        #     1234.5678
        #
        # Old arXiv IDs:
        #
        #     hep-th/9901001
        #
        if not re.match(
            r"^(?:"
            r"\d{4}\.\d{4,5}"
            r"|"
            r"[a-zA-Z\-]+(?:\.[A-Za-z\-]+)?/\d{7}"
            r")$",
            arxiv_id,
        ):
            return None

        return arxiv_id

    # ==================================================================
    # PMID NORMALIZATION
    # ==================================================================

    def _normalize_pmid(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        pmid = str(value).strip()

        if not pmid:
            return None

        for prefix in self.PMID_URL_PREFIXES:

            if pmid.lower().startswith(
                prefix.lower()
            ):

                pmid = pmid[
                    len(prefix):
                ]

                break

        pmid = pmid.strip()

        pmid = pmid.rstrip(
            "/.,; "
        )

        if pmid.lower().startswith(
            "pubmed/"
        ):
            pmid = pmid[7:]

        if not pmid.isdigit():
            return None

        return pmid

    # ==================================================================
    # OPENALEX NORMALIZATION
    # ==================================================================

    def _normalize_openalex_id(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        openalex_id = str(value).strip()

        if not openalex_id:
            return None

        for prefix in self.OPENALEX_URL_PREFIXES:

            if openalex_id.lower().startswith(
                prefix.lower()
            ):

                openalex_id = openalex_id[
                    len(prefix):
                ]

                break

        openalex_id = (
            openalex_id
            .strip()
            .rstrip("/")
        )

        if not openalex_id:
            return None

        # OpenAlex work IDs:
        #
        # W123456789
        #
        if not re.match(
            r"^W\d+$",
            openalex_id,
            re.IGNORECASE,
        ):
            return None

        return openalex_id.upper()

    # ==================================================================
    # TITLE
    # ==================================================================

    def _normalize_title(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        title = self._normalize_string(
            value
        )

        if not title:
            return None

        return title

    # ==================================================================
    # ABSTRACT
    # ==================================================================

    def _normalize_abstract(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        abstract = self._normalize_string(
            value
        )

        if not abstract:
            return None

        return abstract

    # ==================================================================
    # URL
    # ==================================================================

    def _normalize_url(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        url = str(value).strip()

        if not url:
            return None

        parsed = urlparse(url)

        if parsed.scheme.lower() not in {
            "http",
            "https",
        }:
            return None

        if not parsed.netloc:
            return None

        return url.rstrip()

    # ==================================================================
    # STRING
    # ==================================================================

    def _normalize_string(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        text = str(value)

        # Normalize whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        text = text.strip()

        return text or None

    # ==================================================================
    # FIRST VALUE
    # ==================================================================

    @staticmethod
    def _first_value(
        record: Mapping[str, Any],
        *keys: str,
    ) -> Any:
        """
        Return the first non-empty value from a mapping.

        Empty strings are ignored.
        None values are ignored.
        """

        for key in keys:

            if key not in record:
                continue

            value = record[key]

            if value is None:
                continue

            if (
                isinstance(value, str)
                and not value.strip()
            ):
                continue

            return value

        return None