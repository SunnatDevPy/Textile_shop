"""Заказы: позиции с product_id + product_item_id + count; после оплаты — статус и списание остатков."""

from typing import Annotated, Optional, Union

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import verify_admin_credentials
from models import AdminUser, Order, OrderItem, Product, ProductItems
from models.database import db
from utils.audit import write_audit_log

order_router = APIRouter(prefix='/order', tags=['Orders'])

StaffAuth = Annotated[AdminUser, Depends(verify_admin_credentials)]


def _status_value(s: Union[str, object, None]) -> Optional[str]:
    if s is None:
        return None
    if hasattr(s, 'value'):
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
                detail=(
                    f"Omborda yetarli mahsulot yo'q (product_item_id={oi.product_item_id}, "
                    f"kerak={oi.count})"
                ),
            )


class OrderLineIn(BaseModel):
    product_id: int = Field(..., ge=1)
    product_item_id: int = Field(..., ge=1)
    count: int = Field(..., ge=1)


class CreateOrderPayload(BaseModel):
    first_name: str
    last_name: str
    country: str
    address: str
    town_city: str
    contact: str
    postcode_zip: int
    payment: str = Field(..., description="click yoki payme")
    items: list[OrderLineIn]
    email_address: Optional[str] = None
    state_county: Optional[str] = None


class ConfirmPaymentPayload(BaseModel):
    """Ixtiyoriy: boshqa status (default — to'lovdan keyin jarayonda)."""

    next_status: Optional[str] = None


@order_router.get('', name='Orders list', summary="Buyurtmalar ro'yxati (operator/admin)")
async def list_orders(_: StaffAuth):
    return await Order.all()


@order_router.get('/{order_id}', name='Order detail', summary="Bitta buyurtma tafsiloti (operator/admin)")
async def get_order(order_id: int, _: StaffAuth):
    order = await Order.get_or_none(order_id, relationship=Order.order_items)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Buyurtma topilmadi')
    return order


@order_router.post('', name='Create order', summary="Yangi buyurtma yaratish")
async def create_order(payload: CreateOrderPayload):
    pay = payload.payment.strip().lower()
    if pay not in (Order.Payment.CLICK.value, Order.Payment.PAYME.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="To'lov turi faqat 'click' yoki 'payme' bo'lishi mumkin",
        )

    payment_enum = Order.Payment.CLICK if pay == Order.Payment.CLICK.value else Order.Payment.PAYME

    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kamida bitta mahsulot qatori kerak",
        )

    for line in payload.items:
        pi = await ProductItems.get_or_none(line.product_item_id)
        if pi is None or pi.product_id != line.product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mahsulot va variant mos emas: product_id={line.product_id}, product_item_id={line.product_item_id}",
            )
        product = await Product.get_or_none(line.product_id)
        if product is None or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mahsulot mavjud emas yoki o'chirilgan: {line.product_id}",
            )

    try:
        order = await Order.create(
            first_name=payload.first_name,
            last_name=payload.last_name,
            company_name=None,
            country=payload.country,
            address=payload.address,
            town_city=payload.town_city,
            payment=payment_enum,
            status=Order.StatusOrder.NEW,
            state_county=payload.state_county,
            contact=payload.contact,
            email_address=payload.email_address,
            postcode_zip=payload.postcode_zip,
        )
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Buyurtma yaratishda xatolik',
        )

    order_items = []
    try:
        for line in payload.items:
            product = await Product.get_or_none(line.product_id)
            price = product.price
            oi = await OrderItem.create(
                product_id=line.product_id,
                product_item_id=line.product_item_id,
                order_id=order.id,
                count=line.count,
                volume=line.count,
                unit='dona',
                price=price,
                total=price * line.count,
            )
            order_items.append(oi)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Buyurtma qatorlarini saqlashda xatolik",
        )

    return {
        'ok': True,
        'order_id': order.id,
        'status': _status_value(order.status),
        'order_items': order_items,
    }


@order_router.post('/{order_id}/confirm-payment', name='Confirm payment: status + stock', summary="To'lovni tasdiqlash va stockni kamaytirish (operator/admin)")
async def confirm_payment(
    order_id: int,
    user: StaffAuth,
    body: Optional[ConfirmPaymentPayload] = None,
):
    """
    To'lov muvaffaqiyatli bo'lgach chaqiring: `total_count` kamaytiriladi, buyurtma statusi yangilanadi.
    Takroriy chaqiriq: agar allaqachon to'langan bo'lsa, qayta spisaniya qilinmaydi.
    """
    order = await Order.get_or_none(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Buyurtma topilmadi')

    current = _status_value(order.status)
    paid_statuses = {
        Order.StatusOrder.PAID.value,
        Order.StatusOrder.IS_PROCESS.value,
    }

    if current in paid_statuses:
        return {'ok': True, 'already_paid': True, 'order_id': order_id}

    if current != Order.StatusOrder.NEW.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu statusda to'lovni tasdiqlab bo'lmaydi: {current}",
        )

    next_status = Order.StatusOrder.PAID.value
    if body and body.next_status:
        allowed = {e.value for e in Order.StatusOrder}
        if body.next_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Noto'g'ri next_status",
            )
        next_status = body.next_status

    try:
        await _deduct_stock_for_order(order_id)

        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=next_status)
        )
        await db.commit()
        await write_audit_log(
            entity="order",
            entity_id=order_id,
            action="confirm_payment",
            actor=user.username,
            details=f"status={next_status}",
        )
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="To'lovni tasdiqlashda xatolik",
        )

    return {'ok': True, 'order_id': order_id, 'status': next_status}


@order_router.patch('/{order_id}/status', name='Update order status (staff)', summary="Buyurtma statusini qo'lda yangilash (operator/admin)")
async def update_order_status(
    order_id: int,
    user: StaffAuth,
    new_status: str = Form(...),
):
    """Statusni qo'lda o'zgartirish (yetkazildi, bekor va hokazo). Ombor bilan bog'liq emas."""
    order = await Order.get_or_none(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Buyurtma topilmadi')

    allowed = {e.value for e in Order.StatusOrder}
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruxsat etilgan statuslar: {', '.join(sorted(allowed))}",
        )

    current = _status_value(order.status)
    paid_statuses = {
        Order.StatusOrder.PAID.value,
        Order.StatusOrder.IS_PROCESS.value,
    }

    # NEW -> (PAID yoki IS_PROCESS) bo'lganda ombordan avtomatik kamaytirish
    should_deduct_stock = current == Order.StatusOrder.NEW.value and new_status in paid_statuses

    try:
        if should_deduct_stock:
            await _deduct_stock_for_order(order_id)

        await Order.update(order_id, status=new_status)
        await write_audit_log(
            entity="order",
            entity_id=order_id,
            action="status_update",
            actor=user.username,
            details=f"new_status={new_status}",
        )
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Statusni yangilashda xatolik",
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Statusni yangilashda xatolik",
        )
    return {'ok': True, 'order_id': order_id, 'status': new_status}
