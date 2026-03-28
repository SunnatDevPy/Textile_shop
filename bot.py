import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot
from aiogram.types import BotCommand

from bot.handlers.start import start_router
from bot.language import language_router
from dispatcher import bot


async def on_start(bot: Bot):
    commands_admin = [
        BotCommand(command='start', description="Bo'tni ishga tushirish")
    ]
    await bot.set_my_commands(commands=commands_admin)


async def on_shutdown(bot: Bot):
    await bot.delete_my_commands()


async def main():
    dp = Dispatcher()
    dp.include_routers(start_router, language_router)
    dp.startup.register(on_start)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

# 1065  docker login
# 1068  docker build -t nickname/name .
# 1071  docker push nickname/name

# docker run --name db_mysql -e MYSQL_ROOT_PASSWORD=1 -d mysql
