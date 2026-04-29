from typing import Optional

from sqlalchemy import update

from models import Order, OrderItem, ProductItems
from models.database import db
from utils.audit import write_audit_log
from utils.notifications import send_order_status_email
from utils.telegram_bot import send_order_status_notification


def status_value(s) -> Optional[str]:
    if s is None:
        return None
    if hasattr(s, "value"):
        return str(s.value)
    return str(s)


async def deduct_stock_for_order(order_id: int) -> None:
    lines = await OrderItem.get_order_items(order_id)
    if not lines:
        raise ValueError("Buyurtmada mahsulot qatorlari yo'q")
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
            raise ValueError(f"Omborda yetarli mahsulot yo'q (product_item_id={oi.product_item_id})")


async def accept_order_from_telegram(order_id: int) -> tuple[bool, str]:
    order = await Order.get_or_none(order_id)
    if not order:
        return False, "Buyurtma topilmadi"

    current = status_value(order.status)
    if current != Order.StatusOrder.NEW.value:
        return False, f"Status allaqachon o'zgargan: {current}"

    new_status = Order.StatusOrder.IS_PROCESS.value
    try:
        await deduct_stock_for_order(order_id)
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
    except Exception:
        await db.rollback()
        raise

    return True, "Qabul qilindi: status jarayonda"
