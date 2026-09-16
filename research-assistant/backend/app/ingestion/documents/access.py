from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass(slots=True)
class DocumentAccess:
    """
    Result of checking whether a document URL is accessible.
    """

    accessible: bool
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    final_url: Optional[str] = None
    reason: Optional[str] = None


class DocumentAccessChecker:
    """
    Check whether a document URL is reachable.

    HEAD is attempted first.

    Some academic repositories incorrectly reject HEAD requests,
    so a lightweight GET request is used as a fallback.
    """

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        user_agent: str = "AI-Research-Assistant/1.0",
    ) -> None:
        self.timeout = timeout
        self.user_agent = user_agent

    def check(self, url: str) -> DocumentAccess:
        """
        Check document accessibility.

        Returns:
            DocumentAccess
        """

        if not url or not url.strip():
            return DocumentAccess(
                accessible=False,
                reason="Document URL is empty.",
            )

        url = url.strip()

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/pdf,text/html,*/*",
        }

        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers=headers,
            ) as client:

                # First attempt HEAD.
                response = client.head(url)

                if response.status_code < 400:
                    return self._build_result(response)

                # Fallback to a small GET request.
                response = client.get(
                    url,
                    headers={
                        **headers,
                        "Range": "bytes=0-1023",
                    },
                )

                return self._build_result(response)

        except httpx.TimeoutException:
            return DocumentAccess(
                accessible=False,
                reason="Document request timed out.",
            )

        except httpx.TooManyRedirects:
            return DocumentAccess(
                accessible=False,
                reason="Too many redirects while accessing document.",
            )

        except httpx.RequestError as exc:
            return DocumentAccess(
                accessible=False,
                reason=f"Document request failed: {exc}",
            )

        except Exception as exc:
            return DocumentAccess(
                accessible=False,
                reason=f"Unexpected access error: {exc}",
            )

    @staticmethod
    def _build_result(
        response: httpx.Response,
    ) -> DocumentAccess:
        content_type = response.headers.get("content-type")

        final_url = str(response.url)

        if response.status_code >= 400:
            return DocumentAccess(
                accessible=False,
                status_code=response.status_code,
                content_type=content_type,
                final_url=final_url,
                reason=f"HTTP {response.status_code}",
            )

        return DocumentAccess(
            accessible=True,
            status_code=response.status_code,
            content_type=content_type,
            final_url=final_url,
        )