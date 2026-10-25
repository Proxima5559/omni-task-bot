import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import task_keyboard
from app.database import async_session_maker
from app.models.task import TaskStatus
from app.services.task_service import TaskService
from app.services.voice_service import VoiceService
from app.utils.errors import AppError, NotFoundError, QueueUnavailable, VoiceRejected
from app.utils.formatting import format_task

log = logging.getLogger(__name__)
router = Router()

WELCOME = (
    "Hi! Send me a text or a voice message and I'll turn it into a task.\n"
    "/tasks - your latest tasks"
)


def _who(message: Message) -> dict:
    u = message.from_user
    return {"telegram_id": u.id, "username": u.username, "first_name": u.first_name}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME)


@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    async with async_session_maker() as session:
        tasks = await TaskService(session).list_for_telegram_user(message.from_user.id)
    if not tasks:
        await message.answer("No tasks yet. Send me one! Writing template: title | description. You can also send a voice message and I'll transcribe it into a task.")
        return
    for task in tasks:
        await message.answer(format_task(task), reply_markup=task_keyboard(task.id, task.status), parse_mode="HTML")


@router.message(F.voice)
async def on_voice(message: Message) -> None:
    voice = message.voice
    try:
        VoiceService.validate(voice.duration, voice.file_size)
    except VoiceRejected as exc:
        await message.reply(exc.message, parse_mode="HTML")
        return

    status_msg = await message.reply("🎙 Got it, transcribing…")
    try:
        async with async_session_maker() as session:
            await VoiceService(TaskService(session)).submit(
                **_who(message),
                chat_id=message.chat.id,
                status_message_id=status_msg.message_id,
                file_id=voice.file_id,
            )
    except QueueUnavailable as exc:
        await status_msg.edit_text(f"⚠️ {exc.message}", parse_mode="HTML")
    except Exception:
        log.exception("Voice intake failed")
        await status_msg.edit_text("⚠️ Something went wrong. Please try again.", parse_mode="HTML")


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(message: Message) -> None:
    async with async_session_maker() as session:
        task = await TaskService(session).create_from_telegram_text(
            **_who(message), chat_id=message.chat.id, text=message.text
        )
    await message.reply(f"📝 Task created:\n{format_task(task)}", reply_markup=task_keyboard(task.id, task.status), parse_mode="HTML")


@router.callback_query(F.data.startswith("status:"))
async def on_status_change(callback: CallbackQuery) -> None:
    try:
        _, raw_id, raw_status = callback.data.split(":")
        task_id, status = int(raw_id), TaskStatus(raw_status)
    except ValueError:
        await callback.answer("Invalid action", show_alert=True)
        return

    try:
        async with async_session_maker() as session:
            task = await TaskService(session).set_status_as_telegram_user(task_id, callback.from_user.id, status)
    except NotFoundError:
        await callback.answer("Task not found", show_alert=True)
        return
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    try:
        await callback.message.edit_text(format_task(task), reply_markup=task_keyboard(task.id, task.status), parse_mode="HTML")
    except TelegramBadRequest:  
        pass
    await callback.answer("Updated")


@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.reply(
            "❓ <b>How to use the /delete command:</b>\n\n"
            "• `/delete last` — Delete your most recently created task\n"
            "• `/delete all` — Delete <b>all</b> of your tasks permanently",
            parse_mode="HTML"
        )
        return

    action = args[1].strip().lower()
    tg_user_id = message.from_user.id

    if action not in ["last", "all"]:
        await message.reply(
            "⚠️ Invalid argument! Use only <b>last</b> or <b>all</b>.\n"
            "Example: `/delete last` or `/delete all`",
            parse_mode="HTML"
        )
        return

    async with async_session_maker() as session:
        service = TaskService(session)
        
        try:
            if action == "all":
                deleted_count = await service.delete_all_tasks(tg_user_id)
                if deleted_count == 0:
                    await message.reply("📭 You don't have any tasks to delete.")
                else:
                    await message.reply(f"💥 Done! <b>{deleted_count}</b> tasks have been deleted.", parse_mode="HTML")
            
            elif action == "last":
                deleted_task = await service.delete_last_task(tg_user_id)
                await message.reply(f"🗑 Deleted the latest task:\n<b>#{deleted_task.id} {deleted_task.title}</b>", parse_mode="HTML")
                
        except NotFoundError:
            await message.reply("❌ No tasks found or you don't have permission to delete them.")
        except AppError as exc:
            await message.reply(f"⚠️ Error: {exc.message}")
        except TelegramBadRequest as err:
            await message.reply(f"⚠️ Telegram parsing error: {err.message}")
        except Exception:
            await message.reply("⚠️ Something went wrong. Failed to execute delete operation.")