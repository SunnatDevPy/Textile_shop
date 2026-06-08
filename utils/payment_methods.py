"""Mavjud to'lov usullari ro'yxati (frontend checkout uchun)."""

from config import conf
from models import Order


def _payment_icon_url(method: str) -> str:
    path = f"/static/payments/{method}.svg"
    base = (conf.PUBLIC_BASE_URL or "").strip().rstrip("/")
    if base:
        return f"{base}{path}"
    return path


def _payme_enabled() -> bool:
    return bool((conf.PAYME_MERCHANT_ID or "").strip() and (conf.PAYME_SECRET_KEY or "").strip())


def _click_enabled() -> bool:
    return bool(
        (conf.CLICK_MERCHANT_ID or "").strip()
        and (conf.CLICK_SERVICE_ID or "").strip()
        and (conf.PUBLIC_BASE_URL or "").strip()
    )


def get_payment_methods_list() -> list[dict]:
    """To'lov usullari: method, icon, status."""
    return [
        {
            "method": Order.Payment.PAYME.value,
            "icon": _payment_icon_url(Order.Payment.PAYME.value),
            "status": _payme_enabled(),
        },
        {
            "method": Order.Payment.CLICK.value,
            "icon": _payment_icon_url(Order.Payment.CLICK.value),
            "status": _click_enabled(),
        },
        {
            "method": Order.Payment.CASH.value,
            "icon": _payment_icon_url(Order.Payment.CASH.value),
            "status": True,
        },
    ]
