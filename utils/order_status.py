"""Buyurtma va to'lov holati yordamchilari."""

from models import Order


def status_value(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def payment_status_value(order: Order) -> str:
    return status_value(getattr(order, "payment_status", None))


def is_order_paid(order: Order) -> bool:
    return payment_status_value(order) == Order.PaymentStatus.PAID.value


def is_order_payable(order: Order) -> bool:
    """To'lov qabul qilish mumkinmi (bekor qilinmagan va to'lanmagan)."""
    st = status_value(order.status)
    if st == Order.StatusOrder.CANCELLED.value:
        return False
    return not is_order_paid(order)


async def mark_order_payment_paid(order_id: int) -> None:
    await Order.update(order_id, payment_status=Order.PaymentStatus.PAID.value)
