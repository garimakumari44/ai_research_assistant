
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUserId
from app.core.exceptions import UnauthorizedException
from app.db.session import get_db
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# AUTH SERVICE DEPENDENCY
# ============================================================


def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """
    Create an AuthService using the current
    database session.
    """

    return AuthService(db)


# ============================================================
# REGISTER
# ============================================================


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    auth_service: AuthService = Depends(
        get_auth_service
    ),
):
    """
    Register a new user.
    """

    return await auth_service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )


# ============================================================
# LOGIN
# ============================================================


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: UserLogin,
    auth_service: AuthService = Depends(
        get_auth_service
    ),
):
    """
    Authenticate a user and return
    access and refresh tokens.
    """

    return await auth_service.login(
        email=payload.email,
        password=payload.password,
    )


# ============================================================
# REFRESH TOKEN
# ============================================================


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(
        get_auth_service
    ),
):
    """
    Exchange a valid refresh token for
    a new access and refresh token pair.

    This endpoint intentionally does NOT use
    CurrentUserId because the access token may
    already be expired.
    """

    return await auth_service.refresh(
        refresh_token=payload.refresh_token,
    )


# ============================================================
# CURRENT USER
# ============================================================


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_current_user(
    current_user_id: CurrentUserId,
    auth_service: AuthService = Depends(
        get_auth_service
    ),
):
    """
    Return the currently authenticated user.

    Requires:

        Authorization: Bearer <access_token>
    """

    try:
        user_id = int(current_user_id)

    except (TypeError, ValueError):
        raise UnauthorizedException(
            "Invalid user ID in authentication token."
        )

    user = await auth_service.get_user(
        user_id
    )

    if user is None:
        raise UnauthorizedException(
            "Authenticated user no longer exists."
        )

    if not user.is_active:
        raise UnauthorizedException(
            "User account is inactive."
        )

    return user

