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


async def get_order_amount_tiyin(order_id: int) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(OrderItem.total), 0)).where(OrderItem.order_id == order_id)
    )
    total_sum = int(result.scalar() or 0)
    return total_sum * 100


async def get_order_amount_sum(order_id: int) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(OrderItem.total), 0)).where(OrderItem.order_id == order_id)
    )
    return int(result.scalar() or 0)
