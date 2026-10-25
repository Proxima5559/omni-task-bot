from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.config import settings
from app.utils.errors import AppError


def create_bot() -> Bot:
    if not settings.telegram_bot_token:
        raise AppError("TELEGRAM_BOT_TOKEN is not set")
    return Bot(token=settings.telegram_bot_token)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp