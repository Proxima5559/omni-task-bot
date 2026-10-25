import asyncio
import logging

from app.bot.instance import create_bot, create_dispatcher
from app.utils.logging import setup_logging

log = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    bot, dp = create_bot(), create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=False)  
    log.info("Bot started (polling)")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())