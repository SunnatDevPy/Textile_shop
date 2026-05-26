"""Payme/Click to'lov havolalarini yaratish."""

import base64
from typing import Optional

from sqlalchemy import func, select

from config import conf
from models import OrderItem
from models.database import db


def payme_return_url(order_id: int) -> Optional[str]:
    base = (conf.PUBLIC_BASE_URL or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}/order/{order_id}/success"


def build_payme_checkout_url(order_id: int, amount_tiyin: int, return_url: Optional[str] = None) -> str:
    merchant_id = (conf.PAYME_MERCHANT_ID or "").strip()
    if not merchant_id:
        raise ValueError("PAYME_MERCHANT_ID sozlanmagan")
    
    if not conf.PAYME_SECRET_KEY:
        raise ValueError("PAYME_SECRET_KEY sozlanmagan")

    params = {
        "m": merchant_id,
        "ac.order_id": str(order_id),
        "a": str(amount_tiyin),
    }
    callback = return_url if return_url is not None else payme_return_url(order_id)
    if callback:
        params["c"] = callback

    params_str = ";".join(f"{k}={v}" for k, v in params.items())
    encoded_params = base64.b64encode(params_str.encode()).decode()
    
    # PAYME_ENDPOINT default qiymati test muhit uchun
    endpoint = (conf.PAYME_ENDPOINT or "https://checkout.test.paycom.uz").rstrip("/")
    return f"{endpoint}/{encoded_params}"


def _order_id_int(order_id) -> int:
    if isinstance(order_id, bool) or order_id is None:
        raise ValueError("order_id noto'g'ri")
    return int(str(order_id).strip())


async def get_order_amount_tiyin(order_id: int) -> int:
    oid = _order_id_int(order_id)
    result = await db.execute(
        select(func.coalesce(func.sum(OrderItem.total), 0)).where(OrderItem.order_id == oid)
    )
    total_sum = int(result.scalar() or 0)
    return total_sum * 100


async def get_order_amount_sum(order_id: int) -> int:
    oid = _order_id_int(order_id)
    result = await db.execute(
        select(func.coalesce(func.sum(OrderItem.total), 0)).where(OrderItem.order_id == oid)
    )
    return int(result.scalar() or 0)


def resolve_payme_amount_tiyin(
    amount_rpc: int, expected_tiyin: int, *, relax_som_equivalent: bool
) -> Optional[int]:
    """Payme RPC ``amount`` ni saqlash/kontrakt uchun tiyin qiymatiga keltirish.

    Rasmiy: ``amount_rpc == expected_tiyin``.
    ``relax_som_equivalent``: ``amount_rpc == expected_tiyin // 100`` bo'lsa (faqat test),
    chekda ``expected_tiyin`` yoziladi (noto'g'ri kichik summa saqlanmasin).

    Mos kelmasa ``None``.
    """
    if expected_tiyin <= 0:
        return None
    if amount_rpc == expected_tiyin:
        return expected_tiyin
    if relax_som_equivalent and expected_tiyin % 100 == 0 and amount_rpc == (expected_tiyin // 100):
        return expected_tiyin
    return None
