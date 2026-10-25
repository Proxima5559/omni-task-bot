import logging

from celery import Task as CeleryTask

from app.config import settings
from app.database import sync_session_scope
from app.models.task import Task, TranscriptionStatus
from app.services.events import TASK_UPDATED, publish_sync
from app.services.telegram_api import TelegramAPI
from app.services.transcription import get_transcriber
from app.utils.errors import PermanentError, TransientError
from app.utils.formatting import format_task
from app.utils.logging import setup_logging
from app.worker.celery_app import NOTIFICATIONS_QUEUE, celery_app

setup_logging()
log = logging.getLogger(__name__)

MAX_TITLE = 500
NOTIFY_MAX_RETRIES = 5


def _backoff(retries: int) -> int:
    return min(2 ** (retries + 1), 60)  


def _save_result(task_id: int, *, text: str | None = None, error: str | None = None) -> None:
    with sync_session_scope() as s:
        task = s.get(Task, task_id)
        if task is None:
            return
        if text is not None:
            task.title = text[:MAX_TITLE]
            task.description = text if len(text) > MAX_TITLE else None
            task.transcription_status = TranscriptionStatus.DONE
            task.transcription_error = None
            s.flush()
            s.refresh(task)
            s.commit()
            publish_sync(TASK_UPDATED, task)
        else:

            chat_id = task.telegram_chat_id
            message_id = task.telegram_message_id
            
            s.delete(task)
            s.commit()
            
            if chat_id and message_id:
                try:
                    TelegramAPI().edit_message(
                        chat_id=chat_id, 
                        message_id=message_id, 
                        text=f"❌ Couldn't transcribe your voice message.\n{error or 'Unknown error'}",
                        parse_mode="HTML"
                    )
                except Exception:
                    log.exception("Failed to send error message to Telegram") 


def _finish(task_id: int, *, text: str | None = None, error: str | None = None) -> None:
    _save_result(task_id, text=text, error=error)
    notify_user.apply_async(args=[task_id], queue=NOTIFICATIONS_QUEUE)


@celery_app.task(bind=True, name="app.worker.tasks.transcribe_voice", max_retries=settings.transcription_max_retries)
def transcribe_voice(self: CeleryTask, task_id: int, file_id: str) -> None:
    with sync_session_scope() as s:
        task = s.get(Task, task_id)
        if task is None:
            log.warning("transcribe_voice: task %s no longer exists", task_id)
            return
        if task.transcription_status == TranscriptionStatus.DONE:
            return  

    try:
        tg = TelegramAPI()
        file_path = tg.get_file_path(file_id)
        audio = tg.download_file(file_path)
        text = get_transcriber().transcribe(audio, filename="voice.ogg")
    except TransientError as exc:
        if self.request.retries >= self.max_retries:
            log.error("Task %s: giving up after %s retries: %s", task_id, self.request.retries, exc)
            _finish(task_id, error="Transcription service is busy, please try again later.")
            return
        log.warning("Task %s: transient error (retry %s): %s", task_id, self.request.retries + 1, exc)
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))
    except PermanentError as exc:
        log.error("Task %s: permanent failure: %s", task_id, exc)
        _finish(task_id, error=str(exc))
        return
    except Exception:  
        log.exception("Task %s: unexpected error", task_id)
        _finish(task_id, error="Unexpected error while processing the voice message.")
        return

    _finish(task_id, text=text)


@celery_app.task(bind=True, name="app.worker.tasks.notify_user", max_retries=NOTIFY_MAX_RETRIES)
def notify_user(self: CeleryTask, task_id: int) -> None:
    from app.bot.keyboards import task_keyboard_data  

    with sync_session_scope() as s:
        task = s.get(Task, task_id)
        if task is None or not task.telegram_chat_id or not task.telegram_message_id:
            return
        chat_id, message_id = task.telegram_chat_id, task.telegram_message_id
        if task.transcription_status == TranscriptionStatus.FAILED:
            text, markup = f"❌ Couldn't transcribe your voice message.\n{task.transcription_error}", None
        else:
            text = f"🎙 Task created from voice:\n{format_task(task)}"
            markup = task_keyboard_data(task.id, task.status)

    try:
        TelegramAPI().edit_message(chat_id, message_id, text, markup)
    except TransientError as exc:
        if self.request.retries >= self.max_retries:
            log.error("notify_user %s: giving up: %s", task_id, exc)
            return
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))
    except PermanentError as exc:  
        log.warning("notify_user %s: permanent failure: %s", task_id, exc)