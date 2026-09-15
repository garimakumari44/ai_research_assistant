from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)


# ============================================================
# SESSION FACTORY
# ============================================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async SQLAlchemy session to FastAPI routes.

    Successful requests are committed automatically.

    If an exception occurs during the request:
        - the transaction is rolled back
        - the exception is re-raised

    The session is always closed after the request.
    """

    async with AsyncSessionLocal() as session:
        try:
            # ------------------------------------------------
            # Give the session to the FastAPI route/service.
            # Repository methods can use flush() as needed.
            # ------------------------------------------------
            yield session

            # ------------------------------------------------
            # IMPORTANT:
            # Persist all successful database changes.
            # ------------------------------------------------
            await session.commit()

        except Exception:
            # ------------------------------------------------
            # Roll back all changes if anything fails.
            # ------------------------------------------------
            await session.rollback()
            raise

        finally:
            # ------------------------------------------------
            # Always close the session.
            # ------------------------------------------------
            await session.close()


# ============================================================
# OPTIONAL SHUTDOWN
# ============================================================

async def close_database() -> None:
    """
    Dispose of the SQLAlchemy connection pool.

    Call this during application shutdown if desired.
    """

    await engine.dispose()