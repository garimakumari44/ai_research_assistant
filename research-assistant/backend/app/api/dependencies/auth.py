from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db


# ============================================================================
# HTTP BEARER AUTHENTICATION
# ============================================================================

bearer_scheme = HTTPBearer(
    auto_error=False,
)


# ============================================================================
# CURRENT USER ID
# ============================================================================


async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    """
    Extract and validate the current user's ID from a JWT.
    """

    if credentials is None:
        raise UnauthorizedException(
            "Authentication credentials are required."
        )

    if credentials.scheme.lower() != "bearer":
        raise UnauthorizedException(
            "Invalid authentication scheme."
        )

    token = credentials.credentials

    if not token or not token.strip():
        raise UnauthorizedException(
            "Authentication token is empty."
        )

    try:
        payload = decode_access_token(token)

    except JWTError:
        raise UnauthorizedException(
            "Invalid or expired authentication token."
        )

    user_id = payload.get("sub")

    if user_id is None or str(user_id).strip() == "":
        raise UnauthorizedException(
            "Authentication token does not contain a user ID."
        )

    return str(user_id)


# ============================================================================
# CURRENT USER ID DEPENDENCY
# ============================================================================

CurrentUserId = Annotated[
    str,
    Depends(get_current_user_id),
]


# ============================================================================
# CURRENT USER
# ============================================================================


async def get_current_user(
    current_user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the authenticated JWT subject to an actual User.
    """

    try:
        user_id = int(current_user_id)

    except (TypeError, ValueError):
        raise UnauthorizedException(
            "Invalid user ID in authentication token."
        )

    result = await db.execute(
        select(User).where(
            User.id == user_id,
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException(
            "Authenticated user no longer exists."
        )

    if not user.is_active:
        raise UnauthorizedException(
            "User account is inactive."
        )

    return user


# ============================================================================
# CURRENT USER DEPENDENCY
# ============================================================================

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]