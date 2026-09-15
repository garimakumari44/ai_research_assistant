from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
)


# ============================================================
# REGISTER REQUEST
# ============================================================


class UserCreate(BaseModel):
    full_name: str | None = None

    email: EmailStr

    password: str


# ============================================================
# LOGIN REQUEST
# ============================================================


class UserLogin(BaseModel):
    email: EmailStr

    password: str


# ============================================================
# USER RESPONSE
# ============================================================


class UserResponse(BaseModel):
    id: int

    email: EmailStr

    full_name: str | None

    is_active: bool

    created_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# REFRESH TOKEN REQUEST
# ============================================================


class RefreshTokenRequest(BaseModel):
    """
    Request body used to exchange a refresh token
    for a new access/refresh token pair.
    """

    refresh_token: str


# ============================================================
# TOKEN RESPONSE
# ============================================================


class TokenResponse(BaseModel):
    access_token: str

    refresh_token: str

    token_type: str = "bearer"