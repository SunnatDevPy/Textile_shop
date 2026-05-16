"""To'lov URL'larini yaratish va foydalanuvchini to'lov sahifasiga yo'naltirish"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from config import conf
from models import Order
from utils.payment_links import (
    build_payme_checkout_url,
    get_order_amount_sum,
    get_order_amount_tiyin,
)

payment_url_router = APIRouter(prefix='/payment-url', tags=['Payment URLs'])

CLICK_MERCHANT_ID = conf.CLICK_MERCHANT_ID
CLICK_SERVICE_ID = conf.CLICK_SERVICE_ID
CLICK_MERCHANT_USER_ID = conf.CLICK_MERCHANT_USER_ID


class PaymentUrlResponse(BaseModel):
    payment_url: str
    order_id: int
    amount: int
    payment_system: str


def _click_return_url(order_id: int) -> str:
    base = (conf.PUBLIC_BASE_URL or "").strip().rstrip("/")
    if not base:
        raise ValueError("PUBLIC_BASE_URL sozlanmagan - to'lov natijasiga qaytish uchun kerak")
    return f"{base}/order/{order_id}/success"


@payment_url_router.get('/{order_id}/payme', name='Get Payme payment URL')
async def get_payme_url(order_id: int) -> PaymentUrlResponse:
    """Payme to'lov URL'ini yaratish."""

    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Buyurtma topilmadi'
        )

    if order.status != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Buyurtma allaqachon to\'langan yoki bekor qilingan: {order.status}'
        )

    amount_in_tiyin = await get_order_amount_tiyin(order_id)
    if amount_in_tiyin < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Buyurtma summasi juda kichik'
        )

    try:
        payment_url = build_payme_checkout_url(order_id, amount_in_tiyin)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return PaymentUrlResponse(
        payment_url=payment_url,
        order_id=order_id,
        amount=amount_in_tiyin,
        payment_system='payme'
    )


@payment_url_router.get('/{order_id}/click', name='Get Click payment URL')
async def get_click_url(order_id: int) -> PaymentUrlResponse:
    """Click to'lov URL'ini yaratish."""

    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Buyurtma topilmadi'
        )

    if order.status != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Buyurtma allaqachon to\'langan yoki bekor qilingan: {order.status}'
        )

    amount_in_sum = await get_order_amount_sum(order_id)
    if amount_in_sum < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Buyurtma summasi juda kichik'
        )
    
    if not CLICK_SERVICE_ID or not CLICK_MERCHANT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Click sozlamalari (.env) to\'ldirilmagan'
        )

    try:
        return_url = _click_return_url(order_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    payment_url = (
        f"https://my.click.uz/services/pay"
        f"?service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount_in_sum}"
        f"&transaction_param={order_id}"
        f"&return_url={return_url}"
        f"&merchant_user_id={CLICK_MERCHANT_USER_ID}"
    )

    return PaymentUrlResponse(
        payment_url=payment_url,
        order_id=order_id,
        amount=amount_in_sum,
        payment_system='click'
    )


@payment_url_router.get('/{order_id}/payment-info', name='Get payment info')
async def get_payment_info(order_id: int):
    """Buyurtma to'lov ma'lumotlarini olish."""
    from models import OrderItem
    from models.database import db
    from sqlalchemy import select

    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Buyurtma topilmadi'
        )

    order_items_query = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    order_items = order_items_query.scalars().all()

    items_list = []
    for item in order_items:
        items_list.append({
            'product_id': item.product_id,
            'product_name': item.product.name_uz if item.product else 'N/A',
            'quantity': item.count,
            'price': item.price,
            'total': item.total
        })

    total_amount = sum(item.total for item in order_items)
    payment_url = None
    if str(getattr(order.payment, "value", order.payment)) == Order.Payment.PAYME.value:
        amount_tiyin = total_amount * 100
        try:
            payment_url = build_payme_checkout_url(order_id, amount_tiyin)
        except ValueError:
            payment_url = None

    return {
        'order_id': order_id,
        'status': order.status,
        'payment_method': order.payment,
        'total_amount': total_amount,
        'amount_tiyin': total_amount * 100,
        'payment_url': payment_url,
        'items': items_list,
        'customer': {
            'first_name': order.first_name,
            'last_name': order.last_name,
            'contact': order.contact,
            'email': order.email_address
        }
    }
