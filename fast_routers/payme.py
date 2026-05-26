"""Payme Merchant API integration"""

import base64
import hashlib
import json
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy import select
from starlette import status
from starlette.responses import JSONResponse

from config import conf
from models import Order, PaymentReceipt
from models.database import db
from utils.payment_links import get_order_amount_tiyin, resolve_payme_amount_tiyin
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


def _parse_payme_order_id(raw) -> int:
    """Payme account.order_id ko'pincha JSON da string ('3') — DB bigint bilan moslash uchun."""
    if raw is None or raw == "":
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail="order_id not provided",
        )
    if isinstance(raw, bool):
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail="order_id invalid",
        )
    try:
        oid = int(str(raw).strip())
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail="order_id invalid",
        )
    if oid < 1:
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail="order_id invalid",
        )
    return oid


def _parse_payme_amount_tiyin(raw) -> int:
    """amount tiyinda int bo'lishi kerak (-31001 noto'g'ri miqdor uchun)."""
    if raw is None:
        raise HTTPException(
            status_code=PaymeError.INVALID_AMOUNT,
            detail="amount not provided",
        )
    try:
        if isinstance(raw, float):
            if not raw.is_integer():
                raise ValueError("fractional amount")
            raw = int(raw)
        amt = int(raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=PaymeError.INVALID_AMOUNT,
            detail="amount invalid",
        )
    return amt


def verify_payme_auth(authorization: Optional[str]) -> bool:
    """Payme (Paycom) Basic Auth.

    Rasmiy: login har doim "Paycom", parol — kassa kaliti (help.paycom.uz / Merchant API template).
    Eski boshqa integratsiyalar uchun: login = PAYME_MERCHANT_ID ham qabul qilinadi.
    """
    if not authorization:
        return False

    if not (PAYME_SECRET_KEY or "").strip():
        return False

    try:
        auth_type, credentials = authorization.split(' ', 1)
        if auth_type.lower() != 'basic':
            return False

        decoded = base64.b64decode(credentials.strip()).decode('utf-8')
        parts = [p.strip() for p in decoded.split(':')]
        if not parts or len(parts) < 2:
            return False

        username = parts[0].strip()

        merchant_id = (PAYME_MERCHANT_ID or '').strip()
        secret = PAYME_SECRET_KEY.strip()

        def _normalize_candidates(rest: str) -> list[str]:
            """Sandbox ba'zan Paycom:Uzcard:LICENCE_KEY kabili yuboradi — bir necha variant bilan solishtiramiz."""
            cand: list[str] = []
            r = rest.strip()
            if r:
                cand.append(r)
                if ':' in r:
                    segs = [s.strip() for s in r.split(':') if s.strip()]
                    if segs:
                        cand.append(segs[-1])
                    if len(segs) >= 2:
                        cand.append(':'.join(segs[1:]))
            out: list[str] = []
            seen: set[str] = set()
            for c in cand:
                if c and c not in seen:
                    seen.add(c)
                    out.append(c)
            return out

        # Paycom Merchant API: Authorization = Base64("Paycom:SECRET_KEY") yoki Paycom:guruh:key
        if username.lower() == 'paycom':
            rest_joined = ":".join(parts[1:])
            for pwd in _normalize_candidates(rest_joined):
                try:
                    if secrets.compare_digest(pwd, secret):
                        return True
                except ValueError:
                    continue
            return False

        if merchant_id and username == merchant_id:
            rest_joined = ":".join(parts[1:])
            for pwd in _normalize_candidates(rest_joined):
                try:
                    if secrets.compare_digest(pwd, secret):
                        return True
                except ValueError:
                    continue

        return False
    except Exception:
        return False


def create_payme_error(code: int, message, data: Optional[str] = None):
    """Payme xatolik qismi. message — str yoki {\"ru\",\"uz\",\"en\"} multilingual obyekt."""
    error: dict = {
        "code": code,
        "message": message,
    }
    if data:
        error["data"] = data
    return {"error": error}


class PaymeRpcError(Exception):
    """Handler ichidagi JSON-RPC xato (Payme uchun data maydoni bilan)."""

    __slots__ = ("code", "message", "data")

    def __init__(self, code: int, message, data: Optional[str] = None):
        self.code = code
        self.message = message
        self.data = data


def _amount_mismatch_message(expected: int, got: int) -> dict:
    """Payme INVALID_ACCOUNT (-31050) uchun multilingual message (sandbox talabi)."""
    som = expected // 100
    return {
        "ru": (
            f"Сумма не соответствует заказу (ожидается {expected} тийн ≈ {som} сум в базе; "
            f"получено {got})."
        ),
        "uz": (
            f"Buyurtma summasi mos emas (kutilgan {expected} tiyin ≈ jami {som} so'm; "
            f"kelgan {got})."
        ),
        "en": (
            f"Amount does not match order (expected {expected} tiyn = order total {som} som; "
            f"Payme sends amount in tiyn). Got {got}."
        ),
    }


def auth_failed_json_rpc(request_id) -> dict:
    """HTTP 401 o'rniga Payme spetsifikatsiyasi: JSON-RPC + 200 (sandbox kutilishi)."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        **create_payme_error(
            PaymeError.INSUFFICIENT_PRIVILEGE,
            "Invalid authorization",
        ),
    }


@payme_router.post('/', name='Payme Merchant API (slash)', include_in_schema=False)
@payme_router.post('', name='Payme Merchant API')
async def payme_webhook(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """
    Payme Merchant API endpoint
    Payme JSON-RPC 2.0 protokolidan foydalanadi
    """
    body: dict = {}
    try:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "jsonrpc": "2.0",
                "id": None,
                **create_payme_error(
                    PaymeError.INVALID_JSON_RPC,
                    "Invalid JSON-RPC request",
                ),
            },
        )

    request_id = body.get('id')

    if not verify_payme_auth(authorization):
        # Payme sandbox: RPC xatoliklar HTTP 200 bilan qaytishi kerak
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=auth_failed_json_rpc(request_id),
        )

    method = body.get('method')
    params = body.get('params') or {}

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
    except PaymeRpcError as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            **create_payme_error(e.code, e.message, e.data),
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
    account = params.get('account') or {}
    order_id = _parse_payme_order_id(account.get('order_id'))
    amount = _parse_payme_amount_tiyin(params.get('amount'))

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail=f"Order not found: {order_id}"
        )

    payment_val = getattr(order.payment, "value", str(order.payment))
    if payment_val != Order.Payment.PAYME.value:
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail="Buyurtma Payme to'lovi emas",
        )

    # Buyurtma statusini tekshirish
    if order.status != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=PaymeError.COULD_NOT_PERFORM,
            detail=f"Order status is not NEW: {order.status}"
        )

    expected_amount = await get_order_amount_tiyin(order_id)
    if (
        resolve_payme_amount_tiyin(
            amount,
            expected_amount,
            relax_som_equivalent=conf.PAYME_RELAX_AMOUNT_UNITS,
        )
        is None
    ):
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _amount_mismatch_message(expected_amount, amount),
            data="order_id",
        )

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
    amount = _parse_payme_amount_tiyin(params.get('amount'))
    account = params.get('account') or {}
    order_id = _parse_payme_order_id(account.get('order_id'))

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

    payment_val = getattr(order.payment, "value", str(order.payment))
    if payment_val != Order.Payment.PAYME.value:
        raise HTTPException(
            status_code=PaymeError.INVALID_ACCOUNT,
            detail="Buyurtma Payme to'lovi emas",
        )

    if order.status != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=PaymeError.COULD_NOT_PERFORM,
            detail=f"Order status is not NEW: {order.status}",
        )

    expected_amount = await get_order_amount_tiyin(order_id)
    canonical_tiyin = resolve_payme_amount_tiyin(
        amount,
        expected_amount,
        relax_som_equivalent=conf.PAYME_RELAX_AMOUNT_UNITS,
    )
    if canonical_tiyin is None:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _amount_mismatch_message(expected_amount, amount),
            data="order_id",
        )

    # Yangi tranzaksiya yaratish
    receipt = await PaymentReceipt.create(
        order_id=order_id,
        payment_system='payme',
        transaction_id=transaction_id,
        amount=canonical_tiyin,
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
