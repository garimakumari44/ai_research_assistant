import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN (
                'research_projects',
                'research_executions',
                'research_results'
            )
            ORDER BY tablename
        """))

        for row in result:
            print(row[0])

asyncio.run(main())
