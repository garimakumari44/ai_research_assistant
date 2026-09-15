from sqlalchemy import text

from app.db.session import SessionLocal
from app.core.redis import redis_client


class HealthService:

    @staticmethod
    async def check_database() -> bool:
        try:
            db = SessionLocal()

            db.execute(
                text("SELECT 1")
            )

            db.close()

            return True

        except Exception:
            return False


    @staticmethod
    async def check_redis() -> bool:
        try:

            await redis_client.ping()

            return True

        except Exception:
            return False