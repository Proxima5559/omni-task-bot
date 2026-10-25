from aiogram.types import InlineKeyboardMarkup

from app.models.task import TaskStatus

_BUTTONS = [
    (TaskStatus.PENDING, "⏳ Pending"),
    (TaskStatus.IN_PROGRESS, "🚧 In progress"),
    (TaskStatus.COMPLETED, "✅ Done"),
]


def task_keyboard_data(task_id: int, current: TaskStatus) -> dict:
    """Plain dict so the Celery worker can use it with raw HTTP too."""
    row = [
        {"text": label, "callback_data": f"status:{task_id}:{status.value}"}
        for status, label in _BUTTONS
        if status != current
    ]
    return {"inline_keyboard": [row]}


def task_keyboard(task_id: int, current: TaskStatus) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.model_validate(task_keyboard_data(task_id, current))