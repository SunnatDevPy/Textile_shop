from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from config import conf


async def _get_bot_settings():
    """Database dan bot sozlamalarini olish"""
    try:
        from models import db, BotSettings
        query = select(BotSettings).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception:
        return None


def _group_ids() -> list[int]:
    """Env dan group IDs olish (fallback)"""
    raw = [x.strip() for x in str(conf.TG_GROUP_IDS or "").split(",") if x.strip()]
    ids: list[int] = []
    for item in raw:
        try:
            ids.append(int(item))
        except ValueError:
            continue
    return ids


async def _get_active_bot_token() -> Optional[str]:
    """Faol bot token olish (database > env)"""
    settings = await _get_bot_settings()
    if settings and settings.is_enabled and settings.bot_token:
        return settings.bot_token
    return conf.TG_BOT_TOKEN if conf.TG_BOT_TOKEN else None


async def _get_active_group_ids() -> list[int]:
    """Faol group IDs olish (database > env)"""
    settings = await _get_bot_settings()
    if settings and settings.is_enabled and settings.group_ids:
        raw = [x.strip() for x in settings.group_ids.split(",") if x.strip()]
        ids: list[int] = []
        for item in raw:
            try:
                ids.append(int(item))
            except ValueError:
                continue
        return ids
    return _group_ids()


async def _enabled() -> bool:
    """Bot yoqilganligini tekshirish"""
    settings = await _get_bot_settings()
    if settings:
        return settings.is_enabled and bool(settings.bot_token and settings.group_ids)
    return bool(conf.TG_BOT_TOKEN and _group_ids())


async def _build_bot() -> Optional[Bot]:
    """Bot instance yaratish"""
    token = await _get_active_bot_token()
    if not token:
        return None
    return Bot(token=token)


async def send_new_order_notification(order_id: int, contact: str, total_sum: int, items_count: int) -> None:
    if not await _enabled():
        return

    settings = await _get_bot_settings()
    if settings and not settings.notify_new_orders:
        return

    text = (
        f"🆕 Yangi buyurtma keldi!\n"
        f"📦 Order ID: {order_id}\n"
        f"📞 Kontakt: {contact}\n"
        f"📊 Pozitsiyalar: {items_count}\n"
        f"💰 Jami summa: {total_sum:,} UZS"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Qabul qildim", callback_data=f"accept:{order_id}")]]
    )
    bot = await _build_bot()
    if bot is None:
        return
    try:
        for chat_id in await _get_active_group_ids():
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    finally:
        await bot.session.close()


async def send_order_status_notification(order_id: int, old_status: Optional[str], new_status: str) -> None:
    if not await _enabled():
        return

    settings = await _get_bot_settings()
    if settings and not settings.notify_new_orders:
        return

    text = (
        f"🔄 Buyurtma statusi yangilandi\n"
        f"📦 Order ID: {order_id}\n"
        f"📋 Eski status: {old_status or '-'}\n"
        f"✅ Yangi status: {new_status}"
    )
    bot = await _build_bot()
    if bot is None:
        return
    try:
        for chat_id in await _get_active_group_ids():
            await bot.send_message(chat_id=chat_id, text=text)
    finally:
        await bot.session.close()


async def send_low_stock_notification(product_name: str, current_stock: int, min_stock: int) -> None:
    """Kam qolgan mahsulot haqida xabar yuborish"""
    if not await _enabled():
        return

    settings = await _get_bot_settings()
    if settings and not settings.notify_low_stock:
        return

    text = (
        f"⚠️ Omborda mahsulot kam qoldi!\n"
        f"📦 Mahsulot: {product_name}\n"
        f"📊 Hozirgi qoldiq: {current_stock}\n"
        f"⚡ Minimal daraja: {min_stock}\n"
        f"🔔 Yangi mahsulot buyurtma qiling!"
    )
    bot = await _build_bot()
    if bot is None:
        return
    try:
        for chat_id in await _get_active_group_ids():
            await bot.send_message(chat_id=chat_id, text=text)
    finally:
        await bot.session.close()


async def send_payment_notification(order_id: int, amount: int, payment_system: str) -> None:
    """To'lov haqida xabar yuborish"""
    if not await _enabled():
        return

    settings = await _get_bot_settings()
    if settings and not settings.notify_payment:
        return

    text = (
        f"💳 To'lov qabul qilindi!\n"
        f"📦 Order ID: {order_id}\n"
        f"💰 Summa: {amount:,} UZS\n"
        f"🏦 To'lov tizimi: {payment_system.upper()}"
    )
    bot = await _build_bot()
    if bot is None:
        return
    try:
        for chat_id in await _get_active_group_ids():
            await bot.send_message(chat_id=chat_id, text=text)
    finally:
        await bot.session.close()


async def answer_callback_query(callback_query_id: str, text: str) -> None:
    bot = await _build_bot()
    if bot is None:
        return
    try:
        await bot.answer_callback_query(callback_query_id=callback_query_id, text=text, show_alert=False)
    finally:
        await bot.session.close()


async def clear_callback_markup(chat_id: int, message_id: int) -> None:
    bot = await _build_bot()
    if bot is None:
        return
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    finally:
        await bot.session.close()


async def set_webhook() -> dict:
    if not conf.TG_WEBHOOK_URL:
        return {"ok": False, "detail": "TG_WEBHOOK_URL sozlanmagan"}

    token = await _get_active_bot_token()
    if not token:
        return {"ok": False, "detail": "Bot token sozlanmagan"}

    bot = await _build_bot()
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
