"""Buyurtma va to'lov holati yordamchilari."""

from enum import Enum
from typing import Type

from models import Order


def status_value(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def enum_field_value(raw, enum_cls: Type[Enum]) -> str:
    """DB/SQLAlchemy enum nomi (PAID) yoki qiymati (to'landi) → enum `.value`."""
    val = status_value(raw)
    for member in enum_cls:
        if val == member.name or val == member.value:
            return str(member.value)
    return val


def payment_status_value(order: Order) -> str:
    return enum_field_value(getattr(order, "payment_status", None), Order.PaymentStatus)


def payment_method_value(order: Order) -> str:
    return enum_field_value(getattr(order, "payment", None), Order.Payment)


def order_workflow_status(order: Order) -> str:
    return enum_field_value(getattr(order, "status", None), Order.StatusOrder)


def is_order_paid(order: Order) -> bool:
    return payment_status_value(order) == Order.PaymentStatus.PAID.value


def is_order_account_blocked(order: Order) -> bool:
    """Payme sandbox «Заблокирован»: to'langan yoki bekor qilingan hisob."""
    st = order_workflow_status(order)
    if st in (
        Order.StatusOrder.CANCELLED.value,
        Order.StatusOrder.PAID.value,
    ):
        return True
    return is_order_paid(order)


def is_order_payable(order: Order) -> bool:
    """To'lov qabul qilish mumkinmi (bekor qilinmagan va to'lanmagan)."""
    return not is_order_account_blocked(order)


def is_payme_payment_method(order: Order) -> bool:
    """Payme checkout: payme yoki hali tanlanmagan (yangi oqim)."""
    return payment_method_value(order) in (
        Order.Payment.PAYME.value,
        Order.Payment.PENDING.value,
    )


async def mark_order_payment_paid(order_id: int) -> None:
    await Order.update(order_id, payment_status=Order.PaymentStatus.PAID.value)
