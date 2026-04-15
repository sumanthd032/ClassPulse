import asyncio
from sqlalchemy import text
from app.database import engine

async def fix_alembic():
    print("⏳ Synchronizing Alembic and PostgreSQL...")
    async with engine.begin() as conn:
        # 1. Remove the forced table so Alembic can build it properly
        await conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE;"))
        
        # 2. Tell Alembic to forget the deleted files and go back to the last good one
        await conn.execute(text("UPDATE alembic_version SET version_num = '5a84815621ef';"))
        
    print("✅ Clean slate achieved!")

if __name__ == "__main__":
    asyncio.run(fix_alembic())