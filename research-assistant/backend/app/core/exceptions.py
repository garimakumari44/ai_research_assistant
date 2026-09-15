
from __future__ import annotations

from typing import Any


class AppException(Exception):
    """
    Base application exception.

    Application exceptions are converted into HTTP responses
    by the global exception handler registered in app/main.py.
    """

    status_code: int = 500
    code: str = "APP_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: Any = None,
    ) -> None:
        self.message = message
        self.details = details

        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the exception into a consistent API error response.
        """

        response: dict[str, Any] = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }

        if self.details is not None:
            response["error"]["details"] = self.details

        return response


class NotFoundException(AppException):
    """
    Resource could not be found.
    """

    status_code = 404
    code = "NOT_FOUND"


class ValidationException(AppException):
    """
    Application-level validation failure.
    """

    status_code = 422
    code = "VALIDATION_ERROR"


class ConflictException(AppException):
    """
    Resource conflicts with existing state.
    """

    status_code = 409
    code = "CONFLICT"


class UnauthorizedException(AppException):
    """
    Authentication failed.
    """

    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenException(AppException):
    """
    Authenticated user lacks permission.
    """

    status_code = 403
    code = "FORBIDDEN"


class ProviderException(AppException):
    """
    External provider failed.
    """

    status_code = 502
    code = "PROVIDER_ERROR"


class ProviderTimeoutException(ProviderException):
    """
    External provider timed out.
    """

    code = "PROVIDER_TIMEOUT"


class DuplicatePaperException(ConflictException):
    """
    Paper already exists in the canonical database.
    """

    code = "DUPLICATE_PAPER"

