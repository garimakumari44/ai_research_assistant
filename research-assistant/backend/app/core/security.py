from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


# ============================================================================
# PASSWORD HASHING
# ============================================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plaintext password.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plaintext password against a stored password hash.
    """

    if not plain_password or not hashed_password:
        return False

    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        return False


# ============================================================================
# JWT CONFIGURATION
# ============================================================================


def _get_secret_key() -> str:
    """
    Return the configured JWT signing secret.

    The same SECRET_KEY must be used when:
        - creating access tokens
        - creating refresh tokens
        - decoding access tokens
        - decoding refresh tokens
    """

    secret_key = str(
        settings.SECRET_KEY
    ).strip()

    if not secret_key:
        raise RuntimeError(
            "JWT SECRET_KEY is not configured."
        )

    return secret_key


def _get_algorithm() -> str:
    """
    Return the configured JWT signing algorithm.
    """

    algorithm = str(
        settings.ALGORITHM
    ).strip()

    if not algorithm:
        raise RuntimeError(
            "JWT ALGORITHM is not configured."
        )

    return algorithm


# ============================================================================
# JWT CREATION
# ============================================================================


def _create_token(
    subject: str | int,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT.

    Standard claims:

        sub  -> user ID
        type -> access / refresh
        iat  -> issued-at timestamp
        exp  -> expiration timestamp
    """

    if (
        subject is None
        or str(subject).strip() == ""
    ):
        raise ValueError(
            "Token subject cannot be empty."
        )

    subject_string = str(subject).strip()

    if not token_type:
        raise ValueError(
            "Token type cannot be empty."
        )

    if expires_delta.total_seconds() <= 0:
        raise ValueError(
            "Token expiration must be greater than zero."
        )

    now = datetime.now(timezone.utc)

    expires_at = now + expires_delta

    payload: dict[str, Any] = {
        "sub": subject_string,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        _get_secret_key(),
        algorithm=_get_algorithm(),
    )


# ============================================================================
# ACCESS TOKEN
# ============================================================================


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a JWT access token.
    """

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=expires_delta,
        extra_claims=extra_claims,
    )


# ============================================================================
# REFRESH TOKEN
# ============================================================================


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a JWT refresh token.
    """

    if expires_delta is None:
        expires_delta = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=expires_delta,
        extra_claims=extra_claims,
    )


# ============================================================================
# JWT DECODING
# ============================================================================


def decode_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and cryptographically verify a JWT.

    Validation includes:

        - token format
        - signature
        - expiration
        - configured algorithm
    """

    if not isinstance(token, str):
        raise JWTError(
            "Authentication token must be a string."
        )

    token = token.strip()

    if not token:
        raise JWTError(
            "Authentication token is empty."
        )

    try:
        payload = jwt.decode(
            token,
            _get_secret_key(),
            algorithms=[
                _get_algorithm()
            ],
            options={
                "verify_signature": True,
                "verify_exp": True,
            },
        )

    except JWTError:
        raise

    except Exception as exc:
        raise JWTError(
            "Unable to decode authentication token."
        ) from exc

    if not isinstance(payload, dict):
        raise JWTError(
            "Invalid JWT payload."
        )

    return payload


# ============================================================================
# ACCESS TOKEN VALIDATION
# ============================================================================


def decode_access_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate an access token.

    The token must:

        1. have a valid signature
        2. not be expired
        3. contain type='access'
        4. contain a non-empty sub claim
    """

    payload = decode_token(
        token
    )

    token_type = payload.get(
        "type"
    )

    if token_type != "access":
        raise JWTError(
            "Invalid token type."
        )

    subject = payload.get(
        "sub"
    )

    if (
        subject is None
        or str(subject).strip() == ""
    ):
        raise JWTError(
            "Token does not contain a subject."
        )

    return payload


# ============================================================================
# REFRESH TOKEN VALIDATION
# ============================================================================


def decode_refresh_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a refresh token.

    The token must:

        1. have a valid signature
        2. not be expired
        3. contain type='refresh'
        4. contain a non-empty sub claim
    """

    payload = decode_token(
        token
    )

    token_type = payload.get(
        "type"
    )

    if token_type != "refresh":
        raise JWTError(
            "Invalid token type."
        )

    subject = payload.get(
        "sub"
    )

    if (
        subject is None
        or str(subject).strip() == ""
    ):
        raise JWTError(
            "Refresh token does not contain a subject."
        )

    return payload


# ============================================================================
# TOKEN SUBJECT
# ============================================================================


def get_token_subject(
    token: str,
) -> str:
    """
    Extract the user ID from an access token.
    """

    payload = decode_access_token(
        token
    )

    subject = payload.get(
        "sub"
    )

    if (
        subject is None
        or str(subject).strip() == ""
    ):
        raise JWTError(
            "Token does not contain a subject."
        )

    return str(subject)


def get_refresh_token_subject(
    token: str,
) -> str:
    """
    Extract the user ID from a refresh token.
    """

    payload = decode_refresh_token(
        token
    )

    subject = payload.get(
        "sub"
    )

    if (
        subject is None
        or str(subject).strip() == ""
    ):
        raise JWTError(
            "Refresh token does not contain a subject."
        )

    return str(subject)