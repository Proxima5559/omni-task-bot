from typing import Annotated
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.task import TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskStatusUpdate, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_task_service(session: Annotated[AsyncSession, Depends(get_session)]) -> TaskService:
    return TaskService(session)


Service = Annotated[TaskService, Depends(get_task_service)]


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    service: Service,
    status: TaskStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await service.list_tasks(status=status, limit=limit, offset=offset)


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(data: TaskCreate, service: Service):
    return await service.create_task(data)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, service: Service):
    return await service.get_task(task_id)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, data: TaskUpdate, service: Service):
    return await service.update_task(task_id, data)


@router.patch("/{task_id}/status", response_model=TaskRead)
async def update_status(task_id: int, data: TaskStatusUpdate, service: Service):
    return await service.set_status(task_id, data.status)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, service: Service):
    await service.delete_task(task_id)
    return Response(status_code=204)