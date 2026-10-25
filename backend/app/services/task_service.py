from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskSource, TaskStatus, TranscriptionStatus
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.events import TASK_CREATED, TASK_DELETED, TASK_UPDATED, EventPublisher
from app.utils.errors import NotFoundError

MAX_TITLE = 500
VOICE_PLACEHOLDER = "🎙 Transcribing voice message…"


class TaskService:
    def __init__(self, session: AsyncSession, publisher: EventPublisher | None = None):
        self.session = session
        self.tasks = TaskRepository(session)
        self.users = UserRepository(session)
        self.publisher = publisher or EventPublisher()

    async def list_tasks(self, **filters) -> Sequence[Task]:
        return await self.tasks.list(**filters)

    async def get_task(self, task_id: int) -> Task:
        task = await self.tasks.get(task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    async def create_task(self, data: TaskCreate) -> Task:
        task = await self.tasks.create(
            title=data.title, description=data.description, source=TaskSource.WEB
        )
        await self._commit_and_publish(TASK_CREATED, task)
        return task

    async def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        task = await self.get_task(task_id)
        task = await self.tasks.update(task, **data.model_dump(exclude_unset=True))
        await self._commit_and_publish(TASK_UPDATED, task)
        return task

    async def set_status(self, task_id: int, status: TaskStatus) -> Task:
        task = await self.get_task(task_id)
        if task.status != status:
            task = await self.tasks.update(task, status=status)
            await self._commit_and_publish(TASK_UPDATED, task)
        return task

    async def delete_task(self, task_id: int) -> None:
        task = await self.get_task(task_id)
        snapshot = task  
        await self.tasks.delete(task)
        await self.session.commit()
        await self.publisher.publish(TASK_DELETED, snapshot)
    
    async def delete_last_task(self, telegram_user_id: int) -> Task:
        tasks = await self.list_for_telegram_user(telegram_user_id)
        
        if not tasks:
            raise NotFoundError("No tasks found to delete")

        user_id = tasks[0].user_id 
        
        task = await self.tasks.get_latest_for_user(user_id)
        if not task:
            raise NotFoundError("No tasks found to delete")
            
        snapshot = task
        await self.tasks.delete(task)
        await self.session.commit()
        await self.publisher.publish(TASK_DELETED, snapshot)
        return snapshot

    async def delete_all_tasks(self, telegram_user_id: int) -> int:
        user_tasks = await self.list_for_telegram_user(telegram_user_id)
        
        if not user_tasks:
            return 0

        deleted_count = 0
        
        for task in user_tasks:
            await self.tasks.delete(task)
            deleted_count += 1

        await self.session.commit()
        
        return deleted_count

    async def create_from_telegram_text(
        self, *, telegram_id: int, username: str | None, first_name: str | None, chat_id: int, text: str
    ) -> Task:
        user = await self.users.get_or_create(telegram_id, username, first_name)
        parts = text.split("|", 1)
        title = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else None
        title = title[:MAX_TITLE]

        text = text.strip()
        task = await self.tasks.create(
            user_id=user.id,
            title=title,
            description=description,
            source=TaskSource.TEXT,
            telegram_chat_id=chat_id,
        )
        await self._commit_and_publish(TASK_CREATED, task)
        return task

    async def create_voice_placeholder(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        chat_id: int,
        status_message_id: int,
    ) -> Task:
        user = await self.users.get_or_create(telegram_id, username, first_name)
        task = await self.tasks.create(
            user_id=user.id,
            title=VOICE_PLACEHOLDER,
            source=TaskSource.VOICE,
            transcription_status=TranscriptionStatus.PROCESSING,
            telegram_chat_id=chat_id,
            telegram_message_id=status_message_id,
        )
        await self._commit_and_publish(TASK_CREATED, task)
        return task

    async def mark_transcription_failed(self, task: Task, error: str) -> Task:
        task = await self.tasks.update(
            task, transcription_status=TranscriptionStatus.FAILED, transcription_error=error
        )
        await self._commit_and_publish(TASK_UPDATED, task)
        return task

    async def list_for_telegram_user(self, telegram_id: int, limit: int = 10) -> Sequence[Task]:
        user = await self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return []
        return await self.tasks.list(user_id=user.id, limit=limit)

    async def set_status_as_telegram_user(self, task_id: int, telegram_id: int, status: TaskStatus) -> Task:
        task = await self.get_task(task_id)
        user = await self.users.get_by_telegram_id(telegram_id)
        if user is None or task.user_id != user.id:
            raise NotFoundError(f"Task {task_id} not found")  
        return await self.set_status(task_id, status)

    async def _commit_and_publish(self, event_type: str, task: Task) -> None:
        await self.session.commit()  
        await self.publisher.publish(event_type, task)