import enum
from datetime import datetime
from typing import TYPE_CHECKING 
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskSource(str, enum.Enum):
    TEXT = "text"
    VOICE = "voice"
    WEB = "web"


class TranscriptionStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


def _enum(e: type[enum.Enum]) -> Enum:
    return Enum(e, native_enum=False, length=20, values_callable=lambda x: [m.value for m in x])


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(_enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    source: Mapped[TaskSource] = mapped_column(_enum(TaskSource), default=TaskSource.WEB)
    transcription_status: Mapped[TranscriptionStatus] = mapped_column(
        _enum(TranscriptionStatus), default=TranscriptionStatus.NOT_REQUIRED
    )
    transcription_error: Mapped[str | None] = mapped_column(Text)

    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User | None"] = relationship(back_populates="tasks")