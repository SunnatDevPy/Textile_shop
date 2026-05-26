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

# Payme Merchant API: account — faqat shu kalitlar (prod); testda qo'shimcha kalit sandbox xatosi.
_PAYME_ACCOUNT_ALLOWED_KEYS = frozenset({"order_id"})


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
    # Bitta buyurtma bo'yicha Payme trx yaratilgan, Perform/Cancel kutilyapti (sandbox «Обрабатывается»).
    ACCOUNT_BUSY_TRANSACTION = -31088


# help.paycom.uz: CreateTransaction natijasida state=1, PerformTransaction dan keyin state=2
STATE_WAITING_PAY = 1
STATE_PAY_ACCEPTED = 2


def _payme_rpc_tx_state(receipt: PaymentReceipt) -> int:
    """DB holatini Payme Merchant API `result.state` ga aylantirish."""
    st = int(receipt.state) if receipt.state is not None else 0
    if st < 0:
        return st
    if receipt.perform_time is not None:
        return STATE_PAY_ACCEPTED
    return STATE_WAITING_PAY


def _payme_check_perform_time_rpc(rpc_state: int, db_perform_time) -> int:
    """CheckTransaction / GetStatement: bekor (state < 0) bo‘lsa `perform_time` 0 (sandbox)."""
    if rpc_state < 0:
        return 0
    if rpc_state == STATE_WAITING_PAY:
        return 0
    if db_perform_time is None:
        return 0
    return int(db_perform_time)


def _payme_check_cancel_time_rpc(receipt: PaymentReceipt, rpc_state: int) -> int:
    """Kutmoqda (1) va to‘langan (2): cancel_time har doim 0; manfiy state: timestamp."""
    if rpc_state < 0:
        return int(receipt.cancel_time or 0)
    return 0


def _payme_check_reason_rpc(receipt: PaymentReceipt, rpc_state: int):
    """Kutmoqda yoki yakunlangan: reason null (JSON); bekor uchun raqam."""
    if rpc_state < 0:
        return receipt.reason
    return None


async def _payme_has_waiting_payme_receipt(order_id: int) -> bool:
    """Perform yoki Cancel tugamagan faol Payme cheki (band hisob)."""
    res = await db.execute(
        select(PaymentReceipt.id)
        .where(
            PaymentReceipt.order_id == order_id,
            PaymentReceipt.payment_system == "payme",
            PaymentReceipt.perform_time.is_(None),
            PaymentReceipt.cancel_time.is_(None),
            PaymentReceipt.state >= 0,
        )
        .limit(1)
    )
    return res.scalar_one_or_none() is not None


def _payme_account_missing_message() -> dict:
    return {
        "ru": "Параметр account не передан.",
        "uz": "account parametri berilmagan.",
        "en": "Missing account parameter.",
    }


def _payme_account_not_object_message() -> dict:
    return {
        "ru": "Параметр account должен быть объектом.",
        "uz": "account obyekt bo'lishi kerak.",
        "en": "The account parameter must be a JSON object.",
    }


def _payme_order_id_missing_message() -> dict:
    return {
        "ru": "Не указан order_id в account.",
        "uz": "account.order_id ko'rsatilmagan.",
        "en": "order_id is missing in account.",
    }


def _payme_order_id_invalid_message() -> dict:
    return {
        "ru": "Неверный order_id.",
        "uz": "order_id noto'g'ri.",
        "en": "Invalid order_id.",
    }


def _payme_order_not_found_message(order_id: int) -> dict:
    return {
        "ru": f"Заказ не найден: {order_id}.",
        "uz": f"Buyurtma topilmadi: {order_id}.",
        "en": f"Order not found: {order_id}.",
    }


def _payme_order_not_payme_message() -> dict:
    return {
        "ru": "Заказ недоступен для оплаты через Payme.",
        "uz": "Buyurtma Payme orqali to'lanmaydi.",
        "en": "This order is not payable via Payme.",
    }


def _payme_account_blocked_status_message(status: str) -> dict:
    """Счёт уже оплачен / отменён / не в состоянии оплаты."""
    return {
        "ru": f"Счёт недоступен для оплаты (статус заказа: {status}).",
        "uz": f"To'lov uchun hisob band: buyurtma holati {status}.",
        "en": f"The account cannot accept payment (order status: {status}).",
    }


def _payme_account_busy_payme_message(order_id: int) -> dict:
    return {
        "ru": f"По заказу уже создана транзакция Payme (ожидается проведение или отмена): {order_id}.",
        "uz": f"Bu buyurtma bo'yicha Payme tranzaksiyasi allaqachon yaratilgan: {order_id}.",
        "en": f"A Payme transaction is already in progress for this order: {order_id}.",
    }


def _payme_unknown_account_field_message(field: str) -> dict:
    return {
        "ru": f"Недопустимое поле account: {field}.",
        "uz": f"account uchun ruxsat etilmagan maydon: {field}.",
        "en": f"Invalid account field: {field}.",
    }


def _payme_amount_missing_message() -> dict:
    return {
        "ru": "Сумма не указана.",
        "uz": "Summa ko'rsatilmagan.",
        "en": "Amount not provided.",
    }


def _payme_amount_invalid_message() -> dict:
    return {
        "ru": "Неверная сумма.",
        "uz": "Noto'g'ri summa.",
        "en": "Invalid amount.",
    }


def _payme_amount_too_small_message(amount: int) -> dict:
    return {
        "ru": f"Сумма слишком мала: {amount}.",
        "uz": f"Summa juda kichik: {amount}.",
        "en": f"Amount is too small: {amount}.",
    }


def _require_payme_account_dict(params: dict) -> dict:
    """JSON-RPC params.account — obyekt bo'lishi kerak (help.paycom.uz: -31050..-31099 + data)."""
    raw = params.get("account")
    if raw is None:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_account_missing_message(),
            data="account",
        )
    if not isinstance(raw, dict):
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_account_not_object_message(),
            data="account",
        )
    return raw


def _validate_payme_account_keyset(account: dict) -> None:
    """Sandbox: account ichida order_id dan boshqa kalitlar — noto'g'ri parametrlar."""
    if not conf.PAYME_ACCOUNT_REJECT_EXTRA_KEYS:
        return
    extra = set(account.keys()) - _PAYME_ACCOUNT_ALLOWED_KEYS
    if extra:
        field = sorted(extra)[0]
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_unknown_account_field_message(field),
            data=field,
        )


def _parse_payme_order_id(raw) -> int:
    """Payme account.order_id ko'pincha JSON da string ('3') — DB bigint bilan moslash uchun."""
    if raw is None or raw == "":
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_id_missing_message(),
            data="order_id",
        )
    if isinstance(raw, bool):
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_id_invalid_message(),
            data="order_id",
        )
    try:
        oid = int(str(raw).strip())
    except (TypeError, ValueError):
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_id_invalid_message(),
            data="order_id",
        )
    if oid < 1:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_id_invalid_message(),
            data="order_id",
        )
    return oid


def _parse_payme_amount_tiyin(raw) -> int:
    """amount tiyinda int bo'lishi kerak (-31001 noto'g'ri miqdor uchun)."""
    if raw is None:
        raise PaymeRpcError(
            PaymeError.INVALID_AMOUNT,
            _payme_amount_missing_message(),
            data="amount",
        )
    try:
        if isinstance(raw, float):
            if not raw.is_integer():
                raise ValueError("fractional amount")
            raw = int(raw)
        amt = int(raw)
    except (TypeError, ValueError):
        raise PaymeRpcError(
            PaymeError.INVALID_AMOUNT,
            _payme_amount_invalid_message(),
            data="amount",
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


def _payme_parse_allow_order_ids() -> Optional[frozenset[int]]:
    """PAYME_ALLOW_ORDER_IDS CSV; bo‘sh bo‘lsa allowlist tekshiruvi yo‘q."""
    raw = (conf.PAYME_ALLOW_ORDER_IDS or "").strip()
    if not raw:
        return None
    out: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            continue
    return frozenset(out) if out else None


def _payme_require_order_allowed(order_id: int) -> None:
    """Sozlangan allowlist ichida bo‘lmagan order uchun INVALID_ACCOUNT."""
    allowed = _payme_parse_allow_order_ids()
    if allowed is None or order_id in allowed:
        return
    raise PaymeRpcError(
        PaymeError.INVALID_ACCOUNT,
        {
            "ru": f"Недопустимые параметры аккаунта (order_id={order_id}).",
            "uz": f"Hesob parametrlari yaroqsiz (order_id={order_id}).",
            "en": f"Invalid account parameters (order_id={order_id}).",
        },
        data="order_id",
    )


def _amount_mismatch_message(expected: int, got: int) -> dict:
    """Payme INVALID_AMOUNT (-31001): сумма платежа не совпадает с заказом."""
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
    account = _require_payme_account_dict(params)
    _validate_payme_account_keyset(account)
    order_id = _parse_payme_order_id(account.get('order_id'))
    _payme_require_order_allowed(order_id)
    amount = _parse_payme_amount_tiyin(params.get('amount'))

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_not_found_message(order_id),
            data="order_id",
        )

    payment_val = getattr(order.payment, "value", str(order.payment))
    if payment_val != Order.Payment.PAYME.value:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_not_payme_message(),
            data="order_id",
        )

    # Buyurtma statusini tekshirish (sandbox «Заблокирован» — -31008 emas, balki -31050..)
    if order.status != Order.StatusOrder.NEW.value:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_account_blocked_status_message(str(order.status)),
            data="order_id",
        )

    if conf.PAYME_CHECKPERFORM_BUSY_ACCOUNT and await _payme_has_waiting_payme_receipt(
        order_id
    ):
        raise PaymeRpcError(
            PaymeError.ACCOUNT_BUSY_TRANSACTION,
            _payme_account_busy_payme_message(order_id),
            data="order_id",
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
            PaymeError.INVALID_AMOUNT,
            _amount_mismatch_message(expected_amount, amount),
            data="amount",
        )

    if amount < PAYME_MIN_AMOUNT:
        raise PaymeRpcError(
            PaymeError.INVALID_AMOUNT,
            _payme_amount_too_small_message(amount),
            data="amount",
        )

    return {"allow": True}


async def create_transaction(params: dict):
    """
    Tranzaksiya yaratish
    """
    transaction_id = params.get('id')
    time = params.get('time')
    account = _require_payme_account_dict(params)
    _validate_payme_account_keyset(account)
    order_id = _parse_payme_order_id(account.get('order_id'))
    _payme_require_order_allowed(order_id)
    amount = _parse_payme_amount_tiyin(params.get('amount'))

    # Mavjud tranzaksiyani tekshirish
    existing = await db.execute(
        select(PaymentReceipt).where(PaymentReceipt.transaction_id == transaction_id)
    )
    existing_receipt = existing.scalar()

    if existing_receipt:
        if existing_receipt.perform_time is not None:
            raise HTTPException(
                status_code=PaymeError.COULD_NOT_PERFORM,
                detail="Transaction already performed",
            )
        db_st = int(existing_receipt.state) if existing_receipt.state is not None else 0
        if db_st < 0:
            # Payme sandbox bitta transaction_id bilan ketma-ket stsenariylar; bekor qilingan yozuvni
            # qayta Create da "yaratildi" holatiga qaytaramiz (prod da id takrorlanmaydi).
            order = await Order.get_or_none(order_id)
            if not order:
                raise PaymeRpcError(
                    PaymeError.INVALID_ACCOUNT,
                    _payme_order_not_found_message(order_id),
                    data="order_id",
                )
            payment_val = getattr(order.payment, "value", str(order.payment))
            if payment_val != Order.Payment.PAYME.value:
                raise PaymeRpcError(
                    PaymeError.INVALID_ACCOUNT,
                    _payme_order_not_payme_message(),
                    data="order_id",
                )
            if order.status != Order.StatusOrder.NEW.value:
                raise PaymeRpcError(
                    PaymeError.INVALID_ACCOUNT,
                    _payme_account_blocked_status_message(str(order.status)),
                    data="order_id",
                )
            expected_amount = await get_order_amount_tiyin(order_id)
            canonical_tiyin = resolve_payme_amount_tiyin(
                amount,
                expected_amount,
                relax_som_equivalent=conf.PAYME_RELAX_AMOUNT_UNITS,
            )
            if canonical_tiyin is None:
                raise PaymeRpcError(
                    PaymeError.INVALID_AMOUNT,
                    _amount_mismatch_message(expected_amount, amount),
                    data="amount",
                )
            await PaymentReceipt.update(
                existing_receipt.id,
                order_id=order_id,
                amount=canonical_tiyin,
                state=0,
                cancel_time=None,
                reason=None,
                perform_time=None,
                create_time=time,
                receipt_data=json.dumps(params),
            )
            return {
                "create_time": time,
                "transaction": str(existing_receipt.id),
                "state": STATE_WAITING_PAY,
            }
        return {
            "create_time": existing_receipt.create_time,
            "transaction": str(existing_receipt.id),
            "state": STATE_WAITING_PAY,
        }

    # Buyurtmani tekshirish
    order = await Order.get_or_none(order_id)
    if not order:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_not_found_message(order_id),
            data="order_id",
        )

    payment_val = getattr(order.payment, "value", str(order.payment))
    if payment_val != Order.Payment.PAYME.value:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_order_not_payme_message(),
            data="order_id",
        )

    if order.status != Order.StatusOrder.NEW.value:
        raise PaymeRpcError(
            PaymeError.INVALID_ACCOUNT,
            _payme_account_blocked_status_message(str(order.status)),
            data="order_id",
        )

    expected_amount = await get_order_amount_tiyin(order_id)
    canonical_tiyin = resolve_payme_amount_tiyin(
        amount,
        expected_amount,
        relax_som_equivalent=conf.PAYME_RELAX_AMOUNT_UNITS,
    )
    if canonical_tiyin is None:
        raise PaymeRpcError(
            PaymeError.INVALID_AMOUNT,
            _amount_mismatch_message(expected_amount, amount),
            data="amount",
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
        "state": STATE_WAITING_PAY,
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
            detail="Transaction not found",
        )

    st_rc = int(receipt.state) if receipt.state is not None else 0
    if st_rc < 0:
        raise HTTPException(
            status_code=PaymeError.COULD_NOT_PERFORM,
            detail=f"Invalid state: {receipt.state}",
        )

    if receipt.perform_time is not None:
        return {
            "transaction": str(receipt.id),
            "perform_time": receipt.perform_time,
            "state": STATE_PAY_ACCEPTED,
        }

    if receipt.cancel_time is not None:
        raise HTTPException(
            status_code=PaymeError.COULD_NOT_PERFORM,
            detail=f"Invalid state: {receipt.state}",
        )

    perform_time = int(datetime.utcnow().timestamp() * 1000)
    await PaymentReceipt.update(
        receipt.id,
        state=STATE_PAY_ACCEPTED,
        perform_time=perform_time,
    )

    from fast_routers.orders import _deduct_stock_for_order
    from utils.telegram_bot import send_payment_notification

    try:
        await _deduct_stock_for_order(receipt.order_id)
        await Order.update(receipt.order_id, status=Order.StatusOrder.PAID.value)

        await send_payment_notification(
            order_id=receipt.order_id,
            amount=receipt.amount // 100,
            payment_system="payme",
        )
    except Exception:
        await PaymentReceipt.update(
            receipt.id,
            state=-1,
            cancel_time=perform_time,
            reason=1,
            perform_time=None,
        )
        raise

    return {
        "transaction": str(receipt.id),
        "perform_time": perform_time,
        "state": STATE_PAY_ACCEPTED,
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

    st = int(receipt.state) if receipt.state is not None else 0

    # Payme idempotentligi: allaqachon bekor bo'lsa, birinchi Cancel dagi cancel_time/state.
    # (perform_time branch perform qilingan yozuvda birinchi tekshiruv bo'lib qolganda
    # takroriy chaqiruqlar har safar yangi cancel_time yozardi.)
    if st < 0:
        return {
            "transaction": str(receipt.id),
            "cancel_time": int(receipt.cancel_time or 0),
            "state": st,
        }

    if receipt.perform_time is not None:
        cancel_time = int(datetime.utcnow().timestamp() * 1000)
        await PaymentReceipt.update(
            receipt.id,
            state=-1,
            cancel_time=cancel_time,
            reason=reason,
        )

        return {
            "transaction": str(receipt.id),
            "cancel_time": cancel_time,
            "state": -1,
        }

    # Perform qilinmagan (odatda state=0)
    cancel_time = int(datetime.utcnow().timestamp() * 1000)
    await PaymentReceipt.update(
        receipt.id,
        state=-2,
        cancel_time=cancel_time,
        reason=reason,
    )

    return {
        "transaction": str(receipt.id),
        "cancel_time": cancel_time,
        "state": -2,
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

    rpc_state = (
        _payme_rpc_tx_state(receipt)
        if receipt.payment_system == "payme"
        else int(receipt.state) if receipt.state is not None else 0
    )

    if receipt.payment_system == "payme":
        result = {
            "create_time": receipt.create_time,
            "perform_time": _payme_check_perform_time_rpc(rpc_state, receipt.perform_time),
            "cancel_time": _payme_check_cancel_time_rpc(receipt, rpc_state),
            "transaction": str(receipt.id),
            "state": rpc_state,
            "reason": _payme_check_reason_rpc(receipt, rpc_state),
        }
    else:
        result = {
            "create_time": receipt.create_time,
            "perform_time": receipt.perform_time,
            "cancel_time": receipt.cancel_time,
            "transaction": str(receipt.id),
            "state": rpc_state,
            "reason": receipt.reason,
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
        rpc_st = _payme_rpc_tx_state(receipt)
        transactions.append(
            {
                "id": receipt.transaction_id,
                "time": receipt.create_time,
                "amount": receipt.amount,
                "account": {
                    "order_id": receipt.order_id,
                },
                "create_time": receipt.create_time,
                "perform_time": _payme_check_perform_time_rpc(rpc_st, receipt.perform_time),
                "cancel_time": _payme_check_cancel_time_rpc(receipt, rpc_st),
                "transaction": str(receipt.id),
                "state": rpc_st,
                "reason": _payme_check_reason_rpc(receipt, rpc_st),
            }
        )

    return {"transactions": transactions}
