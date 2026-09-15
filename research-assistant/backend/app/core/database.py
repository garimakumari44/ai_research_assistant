from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ----------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)


# ----------------------------------------------------------------------
# Session factory
# ----------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ----------------------------------------------------------------------
# Declarative base
# ----------------------------------------------------------------------

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """

    pass


# ----------------------------------------------------------------------
# FastAPI dependency
# ----------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an AsyncSession to a FastAPI request.

    The session is automatically closed after the request.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# ----------------------------------------------------------------------
# Database lifecycle
# ----------------------------------------------------------------------

async def init_db() -> None:
    """
    Development-only database initialization.

    Production environments should use Alembic migrations instead
    of create_all().
    """

    from app.db import base  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Dispose the SQLAlchemy connection pool.
    """

    await engine.dispose()