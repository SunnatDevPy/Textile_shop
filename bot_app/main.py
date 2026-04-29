import asyncio
import logging

from bot_app.core import build_bot, build_dispatcher
from config import conf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("textile-bot")


async def run_bot() -> None:
    if not conf.TG_BOT_TOKEN:
        logger.error("TG_BOT_TOKEN sozlanmagan. Bot ishga tushmadi.")
        return
    bot = build_bot()
    dp = build_dispatcher()
    logger.info("Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
