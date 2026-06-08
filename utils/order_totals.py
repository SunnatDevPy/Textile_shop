"""Buyurtma jami summasini order_items dan hisoblash va sinxronlash."""

from sqlalchemy import func, select

from models import Order, OrderItem
from models.database import db


async def calc_order_items_total(order_id: int) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(OrderItem.total), 0)).where(
            OrderItem.order_id == order_id
        )
    )
    return int(result.scalar() or 0)


async def sync_order_total_sum(order_id: int) -> int:
    """order_items jami → orders.total_sum (0 qolib ketmasin)."""
    total = await calc_order_items_total(order_id)
    await Order.update(order_id, total_sum=total)
    return total
