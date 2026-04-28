from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import update

from models import Order, OrderItem, ProductItems
from models.database import db

payments_router = APIRouter(prefix="/payments", tags=["Payments"])


def _status_value(s) -> Optional[str]:
    if s is None:
        return None
    if hasattr(s, "value"):
        return str(s.value)
    return str(s)


async def _deduct_stock_for_order(order_id: int) -> None:
    lines = await OrderItem.get_order_items(order_id)
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Buyurtmada mahsulot qatorlari yo'q",
        )

    for oi in lines:
        res = await db.execute(
            update(ProductItems)
            .where(
                ProductItems.id == oi.product_item_id,
                ProductItems.total_count >= oi.count,
            )
            .values(total_count=ProductItems.total_count - oi.count)
        )
        if res.rowcount != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Omborda yetarli mahsulot yo'q (product_item_id={oi.product_item_id})",
            )


async def _mark_order_as_paid(order: Order, next_status: str = Order.StatusOrder.PAID.value):
    current = _status_value(order.status)
    paid_statuses = {Order.StatusOrder.PAID.value, Order.StatusOrder.IS_PROCESS.value}

    if current in paid_statuses:
        return {"ok": True, "already_paid": True, "order_id": order.id, "status": current}

    if current != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu statusda to'lovni tasdiqlab bo'lmaydi: {current}",
        )

    try:
        await _deduct_stock_for_order(order.id)
        await db.execute(
            update(Order)
            .where(Order.id == order.id)
            .values(status=next_status)
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="To'lovni tasdiqlashda xatolik",
        )

    return {"ok": True, "already_paid": False, "order_id": order.id, "status": next_status}


class ClickPreparePayload(BaseModel):
    order_id: int = Field(..., ge=1)


class ClickCompletePayload(BaseModel):
    order_id: int = Field(..., ge=1)
    transaction_id: str
    success: bool = True


class PaymeCheckPayload(BaseModel):
    order_id: int = Field(..., ge=1)
    account: Optional[str] = None


class PaymePerformPayload(BaseModel):
    order_id: int = Field(..., ge=1)
    transaction_id: str
    success: bool = True


@payments_router.post("/click/prepare", summary="Click: buyurtmani to'lovga tayyorligini tekshirish")
async def click_prepare(payload: ClickPreparePayload):
    order = await Order.get_or_none(payload.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")
    if _status_value(order.payment) != Order.Payment.CLICK.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyurtma Click to'lovi emas")
    return {"ok": True, "order_id": order.id, "status": _status_value(order.status)}


@payments_router.post("/click/complete", summary="Click: to'lovni yakunlash va orderni paid qilish")
async def click_complete(payload: ClickCompletePayload):
    order = await Order.get_or_none(payload.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")
    if _status_value(order.payment) != Order.Payment.CLICK.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyurtma Click to'lovi emas")
    if not payload.success:
        return {"ok": False, "order_id": order.id, "status": _status_value(order.status)}
    return await _mark_order_as_paid(order)


@payments_router.post("/payme/check", summary="Payme: buyurtmani tekshirish")
async def payme_check(payload: PaymeCheckPayload):
    order = await Order.get_or_none(payload.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")
    if _status_value(order.payment) != Order.Payment.PAYME.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyurtma Payme to'lovi emas")
    return {"ok": True, "order_id": order.id, "status": _status_value(order.status)}


@payments_router.post("/payme/perform", summary="Payme: to'lovni yakunlash va orderni paid qilish")
async def payme_perform(payload: PaymePerformPayload):
    order = await Order.get_or_none(payload.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")
    if _status_value(order.payment) != Order.Payment.PAYME.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyurtma Payme to'lovi emas")
    if not payload.success:
        return {"ok": False, "order_id": order.id, "status": _status_value(order.status)}
    return await _mark_order_as_paid(order)
