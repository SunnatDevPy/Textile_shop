from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import update

from config import conf
from fast_routers.admin_auth import verify_admin_credentials
from models import AdminUser, Order, OrderItem, ProductItems
from models.database import db
from utils.audit import write_audit_log
from utils.notifications import send_order_status_email
from utils.response import ok_response
from utils.telegram_bot import (
    answer_callback_query,
    clear_callback_markup,
    send_order_status_notification,
    set_webhook,
)

telegram_router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])


def _status_value(s: Any) -> Optional[str]:
    if s is None:
        return None
    if hasattr(s, "value"):
        return str(s.value)
    return str(s)


async def _deduct_stock_for_order(order_id: int) -> None:
    lines = await OrderItem.get_order_items(order_id)
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Buyurtmada mahsulot qatorlari yo'q",
        )
    for oi in lines:
        res = await db.execute(
            update(ProductItems)
            .where(
                ProductItems.id == oi.product_item_id,
                ProductItems.total_count >= oi.count,
            )
            .values(total_count=ProductItems.total_count - oi.count)
        )
        if res.rowcount != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Omborda yetarli mahsulot yo'q (product_item_id={oi.product_item_id})",
            )


@telegram_router.post("/set-webhook", summary="Telegram webhook ni o'rnatish (admin)")
async def telegram_set_webhook(_: AdminUser = Depends(verify_admin_credentials)):
    result = await set_webhook()
    return ok_response(result)


@telegram_router.post("/webhook", summary="Telegram webhook update handler")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
):
    if conf.TG_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != conf.TG_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid telegram secret token")

    payload = await request.json()
    callback = payload.get("callback_query")
    if not callback:
        return {"ok": True}

    data = str(callback.get("data") or "")
    cb_id = str(callback.get("id") or "")
    message = callback.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    message_id = message.get("message_id")

    if not data.startswith("accept:"):
        if cb_id:
            await answer_callback_query(cb_id, "Noma'lum amal")
        return {"ok": True}

    try:
        order_id = int(data.split(":", 1)[1])
    except ValueError:
        if cb_id:
            await answer_callback_query(cb_id, "Noto'g'ri order_id")
        return {"ok": True}

    order = await Order.get_or_none(order_id)
    if not order:
        if cb_id:
            await answer_callback_query(cb_id, "Buyurtma topilmadi")
        return {"ok": True}

    current = _status_value(order.status)
    if current != Order.StatusOrder.NEW.value:
        if cb_id:
            await answer_callback_query(cb_id, f"Status allaqachon o'zgargan: {current}")
        if chat_id and message_id:
            await clear_callback_markup(int(chat_id), int(message_id))
        return {"ok": True}

    new_status = Order.StatusOrder.IS_PROCESS.value
    try:
        await _deduct_stock_for_order(order_id)
        await db.execute(update(Order).where(Order.id == order_id).values(status=new_status))
        await db.commit()
        await write_audit_log(
            entity="order",
            entity_id=order_id,
            action="telegram_accept",
            actor="telegram_bot",
            details=f"old={current}, new={new_status}",
        )
        await send_order_status_email(
            to_email=order.email_address,
            order_id=order_id,
            old_status=current,
            new_status=new_status,
        )
        await send_order_status_notification(order_id=order_id, old_status=current, new_status=new_status)
        if cb_id:
            await answer_callback_query(cb_id, "Qabul qilindi: status jarayonda")
        if chat_id and message_id:
            await clear_callback_markup(int(chat_id), int(message_id))
    except HTTPException as exc:
        await db.rollback()
        if cb_id:
            await answer_callback_query(cb_id, f"Xatolik: {exc.detail}")
    except Exception:
        await db.rollback()
        if cb_id:
            await answer_callback_query(cb_id, "Ichki xatolik")
    return {"ok": True}
