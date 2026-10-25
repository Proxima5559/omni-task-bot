import asyncio
import logging
from fastapi import FastAPI
from app.config import settings

log = logging.getLogger(__name__)

_polling_task = None

async def init_bot(app: FastAPI) -> None:
    if not settings.telegram_bot_token:
        log.warning("Telegram bot token is missing!")
        return

    from app.bot.instance import create_bot, create_dispatcher
    bot = create_bot()
    dp = create_dispatcher()
    
    app.state.bot = bot
    app.state.dp = dp

    if settings.telegram_mode == "webhook":
        await bot.set_webhook(
            settings.telegram_webhook_url,
            secret_token=settings.telegram_webhook_secret or None,
        )
        log.info("Telegram webhook set on production URL")
    else:
        global _polling_task
        await bot.delete_webhook(drop_pending_updates=True)

        _polling_task = asyncio.create_task(dp.start_polling(bot))
        log.info("Local development: Simulated Webhook via background Long-Polling started!")


async def close_bot(app: FastAPI) -> None:
    log.info("Closing bot sessions...")
    if hasattr(app.state, "bot"):
        await app.state.bot.session.close()
    
    global _polling_task
    if _polling_task and not _polling_task.done():
        _polling_task.cancel()
        log.info("Background polling task stopped")