from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **fields: Any) -> Task:
        task = Task(**fields)
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get(self, task_id: int) -> Task | None:
        return await self.session.get(Task, task_id)

    async def list(
        self,
        *,
        status: TaskStatus | None = None,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Task]:
        stmt = select(Task).order_by(Task.created_at.desc(), Task.id.desc()).limit(limit).offset(offset)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return (await self.session.scalars(stmt)).all()

    async def update(self, task: Task, **fields: Any) -> Task:
        for key, value in fields.items():
            setattr(task, key, value)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()
    
    async def get_latest_for_user(self, user_id: int) -> Task | None:
        stmt = select(Task).where(Task.user_id == user_id).order_by(desc(Task.id)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_all_for_user(self, user_id: int) -> int:
        stmt = delete(Task).where(Task.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount 