"""To'lov URL'larini yaratish va foydalanuvchini to'lov sahifasiga yo'naltirish"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from models import Order
from utils.order_payment import start_order_payment
from utils.order_status import payment_status_value
from utils.payment_links import build_payme_checkout_url


payment_url_router = APIRouter(prefix='/payment-url', tags=['Payment URLs'])


class PaymentUrlResponse(BaseModel):
    payment_url: str
    order_id: int
    amount: int
    payment_system: str


@payment_url_router.get('/{order_id}/payme', name='Get Payme payment URL')
async def get_payme_url(order_id: int) -> PaymentUrlResponse:
    """Payme to'lov URL'ini yaratish (order.payment=payme ga yangilanadi)."""
    data = await start_order_payment(order_id, "payme")
    return PaymentUrlResponse(
        payment_url=data["payment_url"],
        order_id=order_id,
        amount=data["amount_tiyin"],
        payment_system='payme',
    )


@payment_url_router.get('/{order_id}/click', name='Get Click payment URL')
async def get_click_url(order_id: int) -> PaymentUrlResponse:
    """Click to'lov URL'ini yaratish (order.payment=click ga yangilanadi)."""
    data = await start_order_payment(order_id, "click")
    return PaymentUrlResponse(
        payment_url=data["payment_url"],
        order_id=order_id,
        amount=data["amount"],
        payment_system='click',
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
    payment_method = str(getattr(order.payment, "value", order.payment))
    payment_url = None
    if payment_method == Order.Payment.PAYME.value:
        try:
            payment_url = build_payme_checkout_url(order_id, total_amount * 100)
        except ValueError:
            payment_url = None

    return {
        'order_id': order_id,
        'status': order.status,
        'payment_status': payment_status_value(order),
        'payment_method': payment_method,
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
