"""Buyurtma uchun to'lov turini tanlash va to'lov havolasini yaratish."""

from typing import Any

from fastapi import HTTPException
from starlette import status

from config import conf
from models import Order
from utils.order_status import is_order_payable, payment_status_value
from utils.order_totals import sync_order_total_sum
from utils.payment_links import (
    build_click_checkout_url,
    build_payme_checkout_url,
    get_order_amount_sum,
    get_order_amount_tiyin,
)

PAYMENT_METHODS = frozenset({
    Order.Payment.CLICK.value,
    Order.Payment.PAYME.value,
    Order.Payment.CASH.value,
})


def parse_payment_method(raw: str) -> str:
    pay = (raw or "").strip().lower()
    if pay not in PAYMENT_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="To'lov turi faqat 'click', 'payme' yoki 'cash' bo'lishi mumkin",
        )
    return pay


async def start_order_payment(order_id: int, payment: str) -> dict[str, Any]:
    """Buyurtmaga to'lov turini biriktirish va (kerak bo'lsa) to'lov havolasini qaytarish."""
    pay = parse_payment_method(payment)

    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyurtma topilmadi",
        )

    if not is_order_payable(order):
        ps = payment_status_value(order)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Buyurtma to'lov uchun mavjud emas (payment_status={ps})",
        )

    await Order.update(order_id, payment=pay)

    if int(getattr(order, "total_sum", 0) or 0) < 1:
        await sync_order_total_sum(order_id)

    total_sum = await get_order_amount_sum(order_id)
    if total_sum < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Buyurtma summasi juda kichik",
        )

    response: dict[str, Any] = {
        "order_id": order_id,
        "payment": pay,
        "total_sum": total_sum,
        "status": str(getattr(order.status, "value", order.status)),
        "payment_status": payment_status_value(order),
        "payment_url": None,
        "amount_tiyin": None,
        "amount": None,
    }

    if pay == Order.Payment.PAYME.value:
        if not (conf.PAYME_MERCHANT_ID and conf.PAYME_SECRET_KEY):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payme sozlamalari (.env) to'ldirilmagan",
            )
        amount_tiyin = await get_order_amount_tiyin(order_id)
        if amount_tiyin < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Buyurtma summasi Payme uchun juda kichik (min 1 so'm)",
            )
        try:
            response["payment_url"] = build_payme_checkout_url(order_id, amount_tiyin)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        response["amount_tiyin"] = amount_tiyin
        response["amount"] = amount_tiyin
        return response

    if pay == Order.Payment.CLICK.value:
        if not (conf.CLICK_MERCHANT_ID and conf.CLICK_SERVICE_ID):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Click sozlamalari (.env) to'ldirilmagan",
            )
        try:
            response["payment_url"] = build_click_checkout_url(order_id, total_sum)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        response["amount"] = total_sum
        return response

    # cash
    response["message"] = "Naqd to'lov tanlandi. Operator tasdiqlashini kuting."
    return response
