import json
import logging

from redis.exceptions import RedisError

from app.config import settings
from app.models.task import Task
from app.redis_client import get_redis, get_sync_redis
from app.schemas.task import TaskRead

log = logging.getLogger(__name__)

TASK_CREATED = "task.created"
TASK_UPDATED = "task.updated"
TASK_DELETED = "task.deleted"


def build_event(event_type: str, task: Task) -> str:
    payload = {"type": event_type, "task": TaskRead.model_validate(task).model_dump(mode="json")}
    return json.dumps(payload)


class EventPublisher:

    async def publish(self, event_type: str, task: Task) -> None:
        try:
            await get_redis().publish(settings.events_channel, build_event(event_type, task))
        except RedisError:
            log.exception("Failed to publish %s for task %s", event_type, task.id)


def publish_sync(event_type: str, task: Task) -> None:
    try:
        get_sync_redis().publish(settings.events_channel, build_event(event_type, task))
    except RedisError:
        log.exception("Failed to publish %s for task %s", event_type, task.id)