"""Click Merchant API integration"""

import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from starlette import status

from config import conf
from models import Order, PaymentReceipt
from models.database import db

click_router = APIRouter(prefix='/click', tags=['Click'])

# Click sozlamalari - config'dan olinadi
CLICK_MERCHANT_ID = conf.CLICK_MERCHANT_ID
CLICK_SERVICE_ID = conf.CLICK_SERVICE_ID
CLICK_SECRET_KEY = conf.CLICK_SECRET_KEY


class ClickPrepareRequest(BaseModel):
    click_trans_id: int
    service_id: int
    click_paydoc_id: int
    merchant_trans_id: str
    amount: float
    action: int
    error: int
    error_note: str
    sign_time: str
    sign_string: str
    merchant_prepare_id: Optional[int] = None


class ClickCompleteRequest(BaseModel):
    click_trans_id: int
    service_id: int
    click_paydoc_id: int
    merchant_trans_id: str
    merchant_prepare_id: int
    amount: float
    action: int
    error: int
    error_note: str
    sign_time: str
    sign_string: str


def verify_click_signature(
    click_trans_id: int,
    service_id: int,
    secret_key: str,
    merchant_trans_id: str,
    amount: float,
    action: int,
    sign_time: str,
    sign_string: str
) -> bool:
    """Click signatureni tekshirish"""
    # Click signature formula:
    # MD5(click_trans_id + service_id + secret_key + merchant_trans_id + amount + action + sign_time)

    data = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
    generated_sign = hashlib.md5(data.encode('utf-8')).hexdigest()

    return generated_sign == sign_string


@click_router.post('/prepare', name='Click Prepare')
async def click_prepare(request: ClickPrepareRequest):
    """
    Click prepare endpoint - to'lovni tayyorlash
    """

    # Signatureni tekshirish
    is_valid = verify_click_signature(
        click_trans_id=request.click_trans_id,
        service_id=request.service_id,
        secret_key=CLICK_SECRET_KEY,
        merchant_trans_id=request.merchant_trans_id,
        amount=request.amount,
        action=request.action,
        sign_time=request.sign_time,
        sign_string=request.sign_string
    )

    if not is_valid:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": 0,
            "error": -1,
            "error_note": "SIGN CHECK FAILED!"
        }

    # Service ID tekshirish
    if request.service_id != int(CLICK_SERVICE_ID):
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": 0,
            "error": -5,
            "error_note": "Service ID is incorrect"
        }

    # Action tekshirish (0 = prepare)
    if request.action != 0:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": 0,
            "error": -3,
            "error_note": "Action not found"
        }

    # Order ID ni merchant_trans_id dan olish
    try:
        order_id = int(request.merchant_trans_id)
    except ValueError:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": 0,
            "error": -5,
            "error_note": "Order ID is incorrect"
        }

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": 0,
            "error": -5,
            "error_note": "Order not found"
        }

    # Buyurtma statusini tekshirish
    if order.status != Order.StatusOrder.NEW.value:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": 0,
            "error": -4,
            "error_note": f"Order already paid or cancelled: {order.status}"
        }

    # Mavjud tranzaksiyani tekshirish
    existing = await db.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.transaction_id == str(request.click_trans_id),
            PaymentReceipt.payment_system == 'click'
        )
    )
    existing_receipt = existing.scalar()

    if existing_receipt:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": existing_receipt.id,
            "error": 0,
            "error_note": "Success"
        }

    # Yangi prepare receipt yaratish
    try:
        receipt = await PaymentReceipt.create(
            order_id=order_id,
            payment_system='click',
            transaction_id=str(request.click_trans_id),
            amount=int(request.amount * 100),  # So'mdan tiyin/kopeykalarga
            state=0,  # Prepare
            create_time=int(datetime.utcnow().timestamp() * 1000),
            receipt_data=request.model_dump_json()
        )

        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": receipt.id,
            "error": 0,
            "error_note": "Success"
        }
    except Exception as e:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_prepare_id": 0,
            "error": -9,
            "error_note": f"Internal error: {str(e)}"
        }


@click_router.post('/complete', name='Click Complete')
async def click_complete(request: ClickCompleteRequest):
    """
    Click complete endpoint - to'lovni yakunlash
    """

    # Signatureni tekshirish
    is_valid = verify_click_signature(
        click_trans_id=request.click_trans_id,
        service_id=request.service_id,
        secret_key=CLICK_SECRET_KEY,
        merchant_trans_id=request.merchant_trans_id,
        amount=request.amount,
        action=request.action,
        sign_time=request.sign_time,
        sign_string=request.sign_string
    )

    if not is_valid:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": 0,
            "error": -1,
            "error_note": "SIGN CHECK FAILED!"
        }

    # Service ID tekshirish
    if request.service_id != int(CLICK_SERVICE_ID):
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": 0,
            "error": -5,
            "error_note": "Service ID is incorrect"
        }

    # Action tekshirish (1 = complete)
    if request.action != 1:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": 0,
            "error": -3,
            "error_note": "Action not found"
        }

    # Prepare receipt'ni topish
    receipt_query = await db.execute(
        select(PaymentReceipt).where(PaymentReceipt.id == request.merchant_prepare_id)
    )
    receipt = receipt_query.scalar()

    if not receipt:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": 0,
            "error": -6,
            "error_note": "Transaction not found"
        }

    # Agar allaqachon complete bo'lgan bo'lsa
    if receipt.state == 1:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": receipt.id,
            "error": 0,
            "error_note": "Success"
        }

    # Agar bekor qilingan bo'lsa
    if receipt.state == -1:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": 0,
            "error": -9,
            "error_note": "Transaction cancelled"
        }

    # Click error tekshirish
    if request.error < 0:
        # Click tomonidan xatolik
        await PaymentReceipt.update(
            receipt.id,
            state=-1,
            cancel_time=int(datetime.utcnow().timestamp() * 1000),
            reason=request.error
        )

        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": 0,
            "error": -9,
            "error_note": f"Click error: {request.error_note}"
        }

    try:
        # Tranzaksiyani complete qilish
        perform_time = int(datetime.utcnow().timestamp() * 1000)
        await PaymentReceipt.update(
            receipt.id,
            state=1,
            perform_time=perform_time
        )

        # Buyurtma statusini yangilash
        await Order.update(receipt.order_id, status=Order.StatusOrder.PAID.value)

        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": receipt.id,
            "error": 0,
            "error_note": "Success"
        }
    except Exception as e:
        return {
            "click_trans_id": request.click_trans_id,
            "merchant_trans_id": request.merchant_trans_id,
            "merchant_confirm_id": 0,
            "error": -9,
            "error_note": f"Internal error: {str(e)}"
        }
