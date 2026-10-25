import asyncio
import logging

from app.config import settings
from app.models.task import Task
from app.services.task_service import TaskService
from app.utils.errors import QueueUnavailable, VoiceRejected
from app.worker.celery_app import TRANSCRIPTION_QUEUE, celery_app

log = logging.getLogger(__name__)


class VoiceService:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    @staticmethod
    def validate(duration_sec: int | None, file_size: int | None) -> None:
        if duration_sec and duration_sec > settings.voice_max_duration_sec:
            raise VoiceRejected(
                f"Voice message is too long ({duration_sec}s). Max is {settings.voice_max_duration_sec}s."
            )
        if file_size and file_size > settings.voice_max_file_mb * 1024 * 1024:
            raise VoiceRejected(f"Voice file is too large. Max is {settings.voice_max_file_mb} MB.")

    async def submit(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        chat_id: int,
        status_message_id: int,
        file_id: str,
    ) -> Task:
        task = await self.task_service.create_voice_placeholder(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            chat_id=chat_id,
            status_message_id=status_message_id,
        )
        try:
            await asyncio.to_thread(
                celery_app.send_task,
                "app.worker.tasks.transcribe_voice",
                args=[task.id, file_id],
                queue=TRANSCRIPTION_QUEUE,
            )
        except Exception as exc:  
            log.exception("Could not enqueue transcription for task %s", task.id)
            await self.task_service.mark_transcription_failed(task, "Transcription queue unavailable")
            raise QueueUnavailable("Transcription queue is unavailable, please try again later.") from exc
        return task