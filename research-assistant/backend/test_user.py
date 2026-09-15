import asyncio
import selectors

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.user import User


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        print(f"TOTAL USERS: {len(users)}")

        for user in users:
            print(
                f"ID={user.id} | "
                f"EMAIL={user.email} | "
                f"FULL_NAME={user.full_name} | "
                f"ACTIVE={user.is_active}"
            )


if __name__ == "__main__":
    asyncio.run(
        main(),
        loop_factory=lambda: asyncio.SelectorEventLoop(
            selectors.SelectSelector()
        ),
    )