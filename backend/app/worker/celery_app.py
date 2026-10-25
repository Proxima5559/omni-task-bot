from celery import Celery
import redis

from app.config import settings

_original_init = redis.connection.Connection.__init__
def _patched_connection_init(self, *args, **kwargs):
    kwargs['protocol'] = 2 
    
    if 'maint_notifications_config' in kwargs:
        kwargs['maint_notifications_config'] = None
        
    _original_init(self, *args, **kwargs)

redis.connection.Connection.__init__ = _patched_connection_init

if hasattr(redis.connection.Connection, 'maint_notifications_config'):
    redis.connection.Connection.maint_notifications_config = None

TRANSCRIPTION_QUEUE = "transcription"
NOTIFICATIONS_QUEUE = "notifications"
    

celery_app = Celery("tasks_worker", broker=settings.redis_url, include=["app.worker.tasks"])

celery_app.conf.update(
    task_ignore_result=True,
    task_acks_late=True, 
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1, 
    task_default_queue=TRANSCRIPTION_QUEUE,
    task_routes={
        "app.worker.tasks.transcribe_voice": {"queue": TRANSCRIPTION_QUEUE},
        "app.worker.tasks.notify_user": {"queue": NOTIFICATIONS_QUEUE},
    },
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=settings.transcription_timeout_sec * 3,
    task_time_limit=settings.transcription_timeout_sec * 3 + 30,
    timezone="UTC",
)