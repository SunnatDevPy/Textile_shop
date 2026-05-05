"""To'lov URL'larini yaratish va foydalanuvchini to'lov sahifasiga yo'naltirish"""

import base64
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from config import conf
from models import Order, OrderItem
from models.database import db
from sqlalchemy import select

payment_url_router = APIRouter(prefix='/payment-url', tags=['Payment URLs'])

# Config'dan olinadi
PAYME_MERCHANT_ID = conf.PAYME_MERCHANT_ID
PAYME_ENDPOINT = conf.PAYME_ENDPOINT
CLICK_MERCHANT_ID = conf.CLICK_MERCHANT_ID
CLICK_SERVICE_ID = conf.CLICK_SERVICE_ID
CLICK_MERCHANT_USER_ID = conf.CLICK_MERCHANT_USER_ID


class PaymentUrlResponse(BaseModel):
    payment_url: str
    order_id: int
    amount: int
    payment_system: str


@payment_url_router.get('/{order_id}/payme', name='Get Payme payment URL')
async def get_payme_url(order_id: int) -> PaymentUrlResponse:
    """
    Payme to'lov URL'ini yaratish
    Foydalanuvchi bu URL orqali Payme sahifasiga o'tadi
    """

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Buyurtma topilmadi'
        )

    # Buyurtma statusini tekshirish
    if order.status != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Buyurtma allaqachon to\'langan yoki bekor qilingan: {order.status}'
        )

    # Buyurtma summasini hisoblash
    order_items_query = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    order_items = order_items_query.scalars().all()

    total_amount = sum(item.total for item in order_items)
    amount_in_tiyin = int(total_amount * 100)  # So'mdan tiyinga

    # Payme checkout URL yaratish
    # Format: m - merchant_id, ac.order_id - buyurtma ID, a - summa (tiyin), c - callback URL
    params = {
        "m": PAYME_MERCHANT_ID,
        "ac.order_id": str(order_id),
        "a": str(amount_in_tiyin),
        "c": f"https://yourdomain.com/order/{order_id}/success"  # Success callback URL
    }

    # Parametrlarni base64 encode qilish
    params_str = ";".join([f"{k}={v}" for k, v in params.items()])
    encoded_params = base64.b64encode(params_str.encode()).decode()

    payment_url = f"{PAYME_ENDPOINT}/{encoded_params}"

    return PaymentUrlResponse(
        payment_url=payment_url,
        order_id=order_id,
        amount=amount_in_tiyin,
        payment_system='payme'
    )


@payment_url_router.get('/{order_id}/click', name='Get Click payment URL')
async def get_click_url(order_id: int) -> PaymentUrlResponse:
    """
    Click to'lov URL'ini yaratish
    Foydalanuvchi bu URL orqali Click sahifasiga o'tadi
    """

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Buyurtma topilmadi'
        )

    # Buyurtma statusini tekshirish
    if order.status != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Buyurtma allaqachon to\'langan yoki bekor qilingan: {order.status}'
        )

    # Buyurtma summasini hisoblash
    order_items_query = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    order_items = order_items_query.scalars().all()

    total_amount = sum(item.total for item in order_items)
    amount_in_sum = int(total_amount)  # Click so'm bilan ishlaydi

    # Click checkout URL yaratish
    # Format: service_id, merchant_id, amount, transaction_param (order_id), return_url, merchant_user_id
    payment_url = (
        f"https://my.click.uz/services/pay"
        f"?service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount_in_sum}"
        f"&transaction_param={order_id}"
        f"&return_url=https://yourdomain.com/order/{order_id}/success"
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
    """
    Buyurtma to'lov ma'lumotlarini olish
    """
    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Buyurtma topilmadi'
        )

    # Buyurtma summasini hisoblash
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

    return {
        'order_id': order_id,
        'status': order.status,
        'payment_method': order.payment,
        'total_amount': total_amount,
        'items': items_list,
        'customer': {
            'first_name': order.first_name,
            'last_name': order.last_name,
            'contact': order.contact,
            'email': order.email_address
        }
    }
