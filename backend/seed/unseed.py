import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base

from app.models.task import Task
from app.models.user import User


async def unseed_data():
    print("Starting database cleanup process...")

    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        print("Connected to the database. Dropping application tables...")

        await conn.run_sync(Base.metadata.drop_all)
        print("Application tables (users, tasks) dropped successfully.")

        print("Dropping Alembic version table if exists...")
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
        print("Alembic history cleared successfully.")

    print("Database is completely empty and ready for a fresh start!")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(unseed_data())
    except Exception as e:
        print(f"CRITICAL ERROR during unseeding: {e}", file=sys.stderr)