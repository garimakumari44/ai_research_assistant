from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

import httpx


@dataclass(slots=True)
class DocumentDownload:
    """
    Result of downloading a document.
    """

    path: Path
    content_type: Optional[str]
    size_bytes: int
    source_url: str
    final_url: str


class DocumentDownloader:
    """
    Stream a document from a remote URL to disk.

    The downloader does not know anything about the database.
    """

    def __init__(
        self,
        *,
        timeout: float = 120.0,
        chunk_size: int = 1024 * 1024,
        max_size_bytes: int = 100 * 1024 * 1024,
        user_agent: str = "AI-Research-Assistant/1.0",
    ) -> None:
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.max_size_bytes = max_size_bytes
        self.user_agent = user_agent

    def download(
        self,
        url: str,
        destination: str | Path,
        *,
        filename: Optional[str] = None,
    ) -> DocumentDownload:
        """
        Download a document.

        Args:
            url:
                Remote document URL.

            destination:
                Directory where the document should be stored.

            filename:
                Optional target filename.

        Returns:
            DocumentDownload

        Raises:
            ValueError:
                Invalid URL or document size.

            httpx.HTTPStatusError:
                Remote server returned an error.
        """

        if not url or not url.strip():
            raise ValueError("Document URL is required.")

        url = url.strip()

        destination_path = Path(destination)

        destination_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        target = self._build_target_path(
            destination_path,
            filename,
            url,
        )

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/pdf,*/*",
        }

        total_bytes = 0

        try:
            with httpx.stream(
                "GET",
                url,
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True,
            ) as response:

                response.raise_for_status()

                content_type = response.headers.get("content-type")

                content_length = response.headers.get(
                    "content-length"
                )

                if content_length:
                    try:
                        declared_size = int(content_length)
                    except ValueError:
                        declared_size = None

                    if (
                        declared_size is not None
                        and declared_size > self.max_size_bytes
                    ):
                        raise ValueError(
                            "Document exceeds maximum allowed size "
                            f"of {self.max_size_bytes} bytes."
                        )

                with target.open("wb") as file:
                    for chunk in response.iter_bytes(
                        chunk_size=self.chunk_size
                    ):
                        if not chunk:
                            continue

                        total_bytes += len(chunk)

                        if total_bytes > self.max_size_bytes:
                            raise ValueError(
                                "Downloaded document exceeds maximum "
                                "allowed size."
                            )

                        file.write(chunk)

                return DocumentDownload(
                    path=target,
                    content_type=content_type,
                    size_bytes=total_bytes,
                    source_url=url,
                    final_url=str(response.url),
                )

        except Exception:
            self._safe_delete(target)
            raise

    @staticmethod
    def _build_target_path(
        destination: Path,
        filename: Optional[str],
        url: str,
    ) -> Path:
        """
        Build a safe filename.

        If a filename is not supplied, attempt to derive one from
        the URL. If that fails, use document.pdf.
        """

        if filename:
            safe_filename = Path(filename).name

            if not safe_filename:
                safe_filename = "document.pdf"

        else:
            parsed = urlparse(url)

            url_filename = Path(
                unquote(parsed.path)
            ).name

            safe_filename = url_filename or "document.pdf"

        # Keep document downloads predictable.
        if "." not in safe_filename:
            safe_filename += ".pdf"

        return destination / safe_filename

    @staticmethod
    def _safe_delete(path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass