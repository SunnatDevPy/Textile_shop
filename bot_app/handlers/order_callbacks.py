import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot_app.services.order_flow import accept_order_from_telegram

logger = logging.getLogger("textile-bot")
order_callbacks_router = Router(name="order_callbacks")


@order_callbacks_router.callback_query(F.data.startswith("accept:"))
async def on_accept_order(callback: CallbackQuery):
    data = callback.data or ""
    try:
        order_id = int(data.split(":", 1)[1])
    except Exception:
        await callback.answer("Noto'g'ri order_id", show_alert=False)
        return

    try:
        ok, message = await accept_order_from_telegram(order_id)
        await callback.answer(message, show_alert=False)
        if callback.message and ok:
            await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as exc:
        logger.exception("accept callback failed: %s", exc)
        await callback.answer("Xatolik yuz berdi", show_alert=False)
