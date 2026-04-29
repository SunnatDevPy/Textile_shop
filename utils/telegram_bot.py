from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import conf


def _group_ids() -> list[int]:
    raw = [x.strip() for x in str(conf.TG_GROUP_IDS or "").split(",") if x.strip()]
    ids: list[int] = []
    for item in raw:
        try:
            ids.append(int(item))
        except ValueError:
            continue
    return ids


def _enabled() -> bool:
    return bool(conf.TG_BOT_TOKEN and _group_ids())


def _build_bot() -> Optional[Bot]:
    if not conf.TG_BOT_TOKEN:
        return None
    return Bot(token=conf.TG_BOT_TOKEN)


async def send_new_order_notification(order_id: int, contact: str, total_sum: int, items_count: int) -> None:
    if not _enabled():
        return
    text = (
        f"Yangi buyurtma keldi!\n"
        f"Order ID: {order_id}\n"
        f"Kontakt: {contact}\n"
        f"Pozitsiyalar: {items_count}\n"
        f"Jami summa: {total_sum} UZS"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Qabul qildim", callback_data=f"accept:{order_id}")]]
    )
    bot = _build_bot()
    if bot is None:
        return
    try:
        for chat_id in _group_ids():
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    finally:
        await bot.session.close()


async def send_order_status_notification(order_id: int, old_status: Optional[str], new_status: str) -> None:
    if not _enabled():
        return
    text = (
        f"Buyurtma statusi yangilandi\n"
        f"Order ID: {order_id}\n"
        f"Old status: {old_status or '-'}\n"
        f"Yangi status: {new_status}"
    )
    bot = _build_bot()
    if bot is None:
        return
    try:
        for chat_id in _group_ids():
            await bot.send_message(chat_id=chat_id, text=text)
    finally:
        await bot.session.close()


async def answer_callback_query(callback_query_id: str, text: str) -> None:
    bot = _build_bot()
    if bot is None:
        return
    try:
        await bot.answer_callback_query(callback_query_id=callback_query_id, text=text, show_alert=False)
    finally:
        await bot.session.close()


async def clear_callback_markup(chat_id: int, message_id: int) -> None:
    bot = _build_bot()
    if bot is None:
        return
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    finally:
        await bot.session.close()


async def set_webhook() -> dict:
    if not conf.TG_BOT_TOKEN or not conf.TG_WEBHOOK_URL:
        return {"ok": False, "detail": "TG_BOT_TOKEN yoki TG_WEBHOOK_URL sozlanmagan"}
    bot = _build_bot()
    if bot is None:
        return {"ok": False, "detail": "Bot sozlanmagan"}
    try:
        result = await bot.set_webhook(
            url=conf.TG_WEBHOOK_URL,
            secret_token=conf.TG_WEBHOOK_SECRET or None,
        )
        return {"ok": bool(result)}
    finally:
        await bot.session.close()
