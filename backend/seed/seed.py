import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskSource, TranscriptionStatus
from app.config import settings 

async def seed_data():
    print("Starting database seeding process...")
    
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        async with session.begin():
            print("Connected to the database. Checking for existing data...")
            
           
            test_user = User(
                telegram_id=123456789,
                username="interview_candidate",
                first_name="John Doe"
            )
            
            session.add(test_user)
            await session.flush()
            print(f"Generated fake user successfully (ID: {test_user.id}, Telegram ID: {test_user.telegram_id})")
            
            tasks = [
                Task(
                    user_id=test_user.id,
                    title="Prepare for the technical interview",
                    description="Review system design patterns, FastAPI dependency injection, and advanced SQLAlchemy architecture.",
                    status=TaskStatus.IN_PROGRESS,
                    source=TaskSource.WEB,
                    transcription_status=TranscriptionStatus.NOT_REQUIRED
                ),
                Task(
                    user_id=test_user.id,
                    title="Voice memo: Refactor telegram bot polling",
                    description="Audio transcription result placeholder.",
                    status=TaskStatus.PENDING,
                    source=TaskSource.VOICE,
                    transcription_status=TranscriptionStatus.DONE,
                    telegram_chat_id=123456789,
                    telegram_message_id=555
                ),
                Task(
                    user_id=test_user.id,
                    title="Deploy bot to production VPS",
                    description="Set up Docker compose, configure GitHub Actions, and bind SSL certificates via Nginx.",
                    status=TaskStatus.COMPLETED,
                    source=TaskSource.TEXT,
                    transcription_status=TranscriptionStatus.NOT_REQUIRED
                )
            ]
            
            session.add_all(tasks)
            print(f"Successfully staged {len(tasks)} tasks for the user.")
            
        print("Database transaction committed successfully!")
        
    print("Seeding process finished without errors. Ready for testing.")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    except Exception as e:
        print(f"CRITICAL ERROR during seeding: {e}", file=sys.stderr)
