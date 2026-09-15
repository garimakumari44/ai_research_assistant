import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN (
                  'research_projects',
                  'research_executions',
                  'research_results'
              )
            ORDER BY table_name, ordinal_position
        """))

        current_table = None

        for row in result:
            if row.table_name != current_table:
                current_table = row.table_name
                print(f"\n=== {current_table} ===")

            print(
                f"{row.column_name:20} "
                f"{row.data_type:20} "
                f"nullable={row.is_nullable}"
            )

asyncio.run(main())
