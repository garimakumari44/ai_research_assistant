from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse


@dataclass(slots=True)
class DocumentResolution:
    """
    Result of resolving a paper to an actual document.

    Attributes:
        document_url:
            URL that can be used to access/download the document.

        source:
            Provider/source that supplied the URL.

        external_id:
            Provider-specific identifier.

        is_pdf:
            Whether the resolved URL appears to point to a PDF.
    """

    document_url: str
    source: Optional[str] = None
    external_id: Optional[str] = None
    is_pdf: bool = False


class DocumentResolver:
    """
    Resolve a paper/provider-paper object into a document URL.

    The resolver accepts both dictionaries and arbitrary Python objects
    so it does not depend directly on a specific Paper implementation.
    """

    URL_FIELDS = (
        "pdf_url",
        "document_url",
        "download_url",
        "full_text_url",
        "open_access_url",
        "url",
    )

    NESTED_FIELDS = (
        "pdf",
        "document",
        "links",
        "open_access",
    )

    def resolve(self, paper: Any) -> DocumentResolution:
        """
        Resolve a document URL from a paper/provider-paper object.

        Raises:
            ValueError:
                If no usable document URL can be found.
        """

        if paper is None:
            raise ValueError("Paper is required for document resolution.")

        url = self._find_url(paper)

        if not url:
            raise ValueError(
                "Unable to resolve a document URL for the supplied paper."
            )

        external_id = self._get_value(
            paper,
            "external_id",
            "provider_paper_id",
            "paper_id",
            "arxiv_id",
            "doi",
        )

        source = self._get_value(
            paper,
            "provider",
            "source",
            "provider_name",
        )

        return DocumentResolution(
            document_url=url,
            source=source,
            external_id=external_id,
            is_pdf=self._looks_like_pdf(url),
        )

    def _find_url(self, obj: Any) -> Optional[str]:
        if obj is None:
            return None

        # Dictionary/object mapping
        if isinstance(obj, dict):
            for field in self.URL_FIELDS:
                value = obj.get(field)

                if isinstance(value, str) and value.strip():
                    return value.strip()

            for field in self.NESTED_FIELDS:
                nested = obj.get(field)

                if nested is not None:
                    result = self._find_url(nested)

                    if result:
                        return result

            return None

        # Regular object
        for field in self.URL_FIELDS:
            value = getattr(obj, field, None)

            if isinstance(value, str) and value.strip():
                return value.strip()

        # Nested objects
        for field in self.NESTED_FIELDS:
            nested = getattr(obj, field, None)

            if nested is not None:
                result = self._find_url(nested)

                if result:
                    return result

        return None

    @staticmethod
    def _get_value(
        obj: Any,
        *fields: str,
    ) -> Optional[str]:
        for field in fields:
            if isinstance(obj, dict):
                value = obj.get(field)
            else:
                value = getattr(obj, field, None)

            if value is not None:
                value_string = str(value).strip()

                if value_string:
                    return value_string

        return None

    @staticmethod
    def _looks_like_pdf(url: str) -> bool:
        """
        Determine whether a URL appears to reference a PDF.

        This is only a heuristic. The actual Content-Type returned by
        the remote server should be treated as authoritative.
        """

        parsed = urlparse(url)

        path = parsed.path.lower()

        return (
            path.endswith(".pdf")
            or ".pdf/" in path
            or "pdf" in path
        )