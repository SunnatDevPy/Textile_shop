"""Payme Merchant API integration"""

import base64
import hashlib
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy import select
from starlette import status

from config import conf
from models import Order, PaymentReceipt
from models.database import db
from utils.response import ok_response

payme_router = APIRouter(prefix='/payme', tags=['Payme'])

# Payme sozlamalari - config'dan olinadi
PAYME_MERCHANT_ID = conf.PAYME_MERCHANT_ID
PAYME_SECRET_KEY = conf.PAYME_SECRET_KEY
PAYME_MIN_AMOUNT = 100  # Minimal summa (tiyin)
PAYME_MAX_AMOUNT = 100000000  # Maksimal summa (tiyin)


class PaymeError:
    """Payme xatolik kodlari"""
    INTERNAL_ERROR = -32400
    INSUFFICIENT_PRIVILEGE = -32504
    INVALID_JSON_RPC = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_AMOUNT = -31001
    TRANSACTION_NOT_FOUND = -31003
    INVALID_ACCOUNT = -31050
    COULD_NOT_PERFORM = -31008
    COULD_NOT_CANCEL = -31007


def verify_payme_auth(authorization: Optional[str]) -> bool:
    """Payme autentifikatsiyasini tekshirish"""
    if not authorization:
        return False

    try:
        auth_type, credentials = authorization.split(' ')
        if auth_type.lower() != 'basic':
            return False

        decoded = base64.b64decode(credentials).decode('utf-8')
        username, password = decoded.split(':')

        # Username Payme tomonidan berilgan merchant_id bo'lishi kerak
        # Password esa secret_key
        return username == PAYME_MERCHANT_ID and password == PAYME_SECRET_KEY
    except Exception:
        return False


def create_payme_error(code: int, message: str, data: Optional[str] = None):
    """Payme xatolik javobini yaratish"""
    error = {
        "code": code,
        "message": message
    }
    if data:
        error["data"] = data
    return {"error": error}


@payme_router.post('', name='Payme Merchant API')
async def payme_webhook(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Payme Merchant API endpoint
    Payme JSON-RPC 2.0 protokolidan foydalanadi
    """

    # Autentifikatsiyani tekshirish
    if not verify_payme_auth(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    try:
        body = await request.json()
    except Exception:
        return create_payme_error(
            PaymeError.INVALID_JSON_RPC,
            "Invalid JSON-RPC request"
        )

    method = body.get('method')
    params = body.get('params', {})
    request_id = body.get('id')

    # Method'ga qarab handler'ni chaqirish
    handlers = {
        'CheckPerformTransaction': check_perform_transaction,
        'CreateTransaction': create_transaction,
        'PerformTransaction': perform_transaction,
        'CancelTransaction': cancel_transaction,
        'CheckTransaction': check_transaction,
        'GetStatement': get_statement,
    }

    handler = handlers.get(method)
    if not handler:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            **create_payme_error(PaymeError.METHOD_NOT_FOUND, f"Method not found: {method}")
        }

    try:
        result = await handler(params)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    except HTTPException as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            **create_payme_error(e.status_code, str(e.detail))
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            **create_payme_error(PaymeError.INTERNAL_ERROR, f"Internal error: {str(e)}")
        }


async def check_perform_transaction(params: dict):
    """
    To'lovni amalga oshirish mumkinligini tekshirish
    """
    amount = params.get('amount')
    account = params.get('account', {})
    order_id = account.get('order_id')

    if not order_id:
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail="order_id not provided"
        )

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail=f"Order not found: {order_id}"
        )

    # Buyurtma statusini tekshirish
    if order.status != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=PaymeError.COULD_NOT_PERFORM,
            detail=f"Order status is not NEW: {order.status}"
        )

    # Summani tekshirish (order_items orqali hisoblash kerak)
    order_items = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    # Bu yerda order_items yig'indisini hisoblash kerak

    if amount < PAYME_MIN_AMOUNT:
        raise HTTPException(
            status_code=PaymeError.INVALID_AMOUNT,
            detail=f"Amount is too small: {amount}"
        )

    return {"allow": True}


async def create_transaction(params: dict):
    """
    Tranzaksiya yaratish
    """
    transaction_id = params.get('id')
    time = params.get('time')
    amount = params.get('amount')
    account = params.get('account', {})
    order_id = account.get('order_id')

    # Mavjud tranzaksiyani tekshirish
    existing = await db.execute(
        select(PaymentReceipt).where(PaymentReceipt.transaction_id == transaction_id)
    )
    existing_receipt = existing.scalar()

    if existing_receipt:
        # Agar tranzaksiya allaqachon mavjud bo'lsa
        if existing_receipt.state == 1:
            raise HTTPException(
                status_code=PaymeError.COULD_NOT_PERFORM,
                detail="Transaction already performed"
            )
        return {
            "create_time": existing_receipt.create_time,
            "transaction": str(existing_receipt.id),
            "state": existing_receipt.state
        }

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail=f"Order not found: {order_id}"
        )

    # Yangi tranzaksiya yaratish
    receipt = await PaymentReceipt.create(
        order_id=order_id,
        payment_system='payme',
        transaction_id=transaction_id,
        amount=amount,
        state=0,  # Yaratildi
        create_time=time,
        receipt_data=json.dumps(params)
    )

    return {
        "create_time": receipt.create_time,
        "transaction": str(receipt.id),
        "state": receipt.state
    }


async def perform_transaction(params: dict):
    """
    Tranzaksiyani amalga oshirish
    """
    transaction_id = params.get('id')

    receipt_query = await db.execute(
        select(PaymentReceipt).where(PaymentReceipt.transaction_id == transaction_id)
    )
    receipt = receipt_query.scalar()

    if not receipt:
        raise HTTPException(
            status_code=PaymeError.TRANSACTION_NOT_FOUND,
            detail="Transaction not found"
        )

    if receipt.state == 1:
        # Allaqachon amalga oshirilgan
        return {
            "transaction": str(receipt.id),
            "perform_time": receipt.perform_time,
            "state": receipt.state
        }

    if receipt.state != 0:
        raise HTTPException(
            status_code=PaymeError.COULD_NOT_PERFORM,
            detail=f"Invalid state: {receipt.state}"
        )

    # Tranzaksiyani amalga oshirish
    perform_time = int(datetime.utcnow().timestamp() * 1000)
    await PaymentReceipt.update(
        receipt.id,
        state=1,
        perform_time=perform_time
    )

    # Buyurtma statusini yangilash va stock kamaytirish
    from fast_routers.orders import _deduct_stock_for_order
    from utils.telegram_bot import send_payment_notification

    try:
        await _deduct_stock_for_order(receipt.order_id)
        await Order.update(receipt.order_id, status=Order.StatusOrder.PAID.value)

        # Payment notification yuborish
        await send_payment_notification(
            order_id=receipt.order_id,
            amount=receipt.amount // 100,  # Tiyin -> So'm
            payment_system='payme'
        )
    except Exception as e:
        # Agar stock kamaytirish xato bo'lsa, tranzaksiyani bekor qilish
        await PaymentReceipt.update(receipt.id, state=-1, cancel_time=perform_time, reason=1)
        raise

    return {
        "transaction": str(receipt.id),
        "perform_time": perform_time,
        "state": 1
    }


async def cancel_transaction(params: dict):
    """
    Tranzaksiyani bekor qilish
    """
    transaction_id = params.get('id')
    reason = params.get('reason')

    receipt_query = await db.execute(
        select(PaymentReceipt).where(PaymentReceipt.transaction_id == transaction_id)
    )
    receipt = receipt_query.scalar()

    if not receipt:
        raise HTTPException(
            status_code=PaymeError.TRANSACTION_NOT_FOUND,
            detail="Transaction not found"
        )

    if receipt.state == 1:
        # Amalga oshirilgan tranzaksiyani bekor qilish
        cancel_time = int(datetime.utcnow().timestamp() * 1000)
        await PaymentReceipt.update(
            receipt.id,
            state=-1,
            cancel_time=cancel_time,
            reason=reason
        )

        return {
            "transaction": str(receipt.id),
            "cancel_time": cancel_time,
            "state": -1
        }

    if receipt.state == 0:
        # Yaratilgan tranzaksiyani bekor qilish
        cancel_time = int(datetime.utcnow().timestamp() * 1000)
        await PaymentReceipt.update(
            receipt.id,
            state=-2,
            cancel_time=cancel_time,
            reason=reason
        )

        return {
            "transaction": str(receipt.id),
            "cancel_time": cancel_time,
            "state": -2
        }

    # Allaqachon bekor qilingan
    return {
        "transaction": str(receipt.id),
        "cancel_time": receipt.cancel_time,
        "state": receipt.state
    }


async def check_transaction(params: dict):
    """
    Tranzaksiya holatini tekshirish
    """
    transaction_id = params.get('id')

    receipt_query = await db.execute(
        select(PaymentReceipt).where(PaymentReceipt.transaction_id == transaction_id)
    )
    receipt = receipt_query.scalar()

    if not receipt:
        raise HTTPException(
            status_code=PaymeError.TRANSACTION_NOT_FOUND,
            detail="Transaction not found"
        )

    result = {
        "create_time": receipt.create_time,
        "perform_time": receipt.perform_time,
        "cancel_time": receipt.cancel_time,
        "transaction": str(receipt.id),
        "state": receipt.state,
        "reason": receipt.reason
    }

    return result


async def get_statement(params: dict):
    """
    Belgilangan vaqt oralig'idagi tranzaksiyalar ro'yxati
    """
    from_time = params.get('from')
    to_time = params.get('to')

    query = select(PaymentReceipt).where(
        PaymentReceipt.payment_system == 'payme',
        PaymentReceipt.create_time >= from_time,
        PaymentReceipt.create_time <= to_time
    )

    result = await db.execute(query)
    receipts = result.scalars().all()

    transactions = []
    for receipt in receipts:
        transactions.append({
            "id": receipt.transaction_id,
            "time": receipt.create_time,
            "amount": receipt.amount,
            "account": {
                "order_id": receipt.order_id
            },
            "create_time": receipt.create_time,
            "perform_time": receipt.perform_time,
            "cancel_time": receipt.cancel_time,
            "transaction": str(receipt.id),
            "state": receipt.state,
            "reason": receipt.reason
        })

    return {"transactions": transactions}
