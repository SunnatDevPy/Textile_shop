from aiogram import Bot, Dispatcher

from bot_app.handlers.order_callbacks import order_callbacks_router
from config import conf


def build_bot() -> Bot:
    return Bot(token=conf.TG_BOT_TOKEN)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(order_callbacks_router)
    return dp
