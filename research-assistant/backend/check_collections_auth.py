import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.collection import Collection


async def main():
    async with AsyncSessionLocal() as db:

        print("\n" + "=" * 60)
        print("USERS")
        print("=" * 60)

        result = await db.execute(
            select(User).order_by(User.id)
        )

        users = result.scalars().all()

        for user in users:
            print(
                f"id={user.id} | "
                f"email={user.email} | "
                f"active={user.is_active}"
            )

        print("\n" + "=" * 60)
        print("COLLECTIONS")
        print("=" * 60)

        result = await db.execute(
            select(Collection).order_by(Collection.id)
        )

        collections = result.scalars().all()

        for collection in collections:
            print(
                f"id={collection.id} | "
                f"user_id={collection.user_id} | "
                f"name={collection.name!r}"
            )

        print("\n" + "=" * 60)
        print("CHECK COLLECTION 8")
        print("=" * 60)

        result = await db.execute(
            select(Collection).where(
                Collection.id == 8
            )
        )

        collection = result.scalar_one_or_none()

        if collection is None:
            print("Collection 8 DOES NOT EXIST.")
        else:
            print(
                f"Collection ID : {collection.id}"
            )
            print(
                f"Owner user ID : {collection.user_id}"
            )
            print(
                f"Name          : {collection.name!r}"
            )

        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())