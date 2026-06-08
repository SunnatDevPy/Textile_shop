"""To'lov usullari ro'yxati (checkout uchun)."""

from fastapi import APIRouter

from utils.payment_methods import get_payment_methods_list
from utils.response import ok_response

payment_methods_router = APIRouter(prefix="/payments", tags=["Payments"])


@payment_methods_router.get(
    "/list",
    name="Payment methods list",
    summary="Mavjud to'lov usullari ro'yxati",
)
async def payment_methods_list():
    """Frontend checkout: payme, click, cash va ularning icon/status holati."""
    return ok_response(get_payment_methods_list())
