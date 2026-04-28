from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select

from fast_routers.admin_auth import verify_admin_credentials
from models import AdminUser, AuditLog, Order, OrderItem
from models.database import db
from utils.response import ok_response

history_router = APIRouter(prefix="/history", tags=["History"])


def _parse_date_range(
    date_from: Optional[str],
    date_to: Optional[str],
) -> tuple[Optional[datetime], Optional[datetime]]:
    dt_from = datetime.fromisoformat(date_from) if date_from else None
    dt_to = datetime.fromisoformat(date_to) if date_to else None
    return dt_from, dt_to


@history_router.get(
    "/orders",
    summary="Buyurtmalar tarixi (sanadan-sanagacha, operator/admin)",
)
async def orders_history(
    _: AdminUser = Depends(verify_admin_credentials),
    date_from: Optional[str] = Query(None, description="ISO sana: 2026-04-28 yoki 2026-04-28T10:00:00"),
    date_to: Optional[str] = Query(None, description="ISO sana: 2026-04-30 yoki 2026-04-30T23:59:59"),
    limit: int = Query(200, ge=1, le=2000),
):
    try:
        dt_from, dt_to = _parse_date_range(date_from, date_to)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sana formati noto'g'ri (ISO kerak)")

    query = select(Order).order_by(desc(Order.created_at))
    criteria = []
    if dt_from:
        criteria.append(Order.created_at >= dt_from)
    if dt_to:
        criteria.append(Order.created_at <= dt_to)
    if criteria:
        query = query.where(and_(*criteria))
    query = query.limit(limit)
    rows = (await db.execute(query)).scalars().all()
    return ok_response(rows, meta={"count": len(rows)})


@history_router.get(
    "/products",
    summary="Productlar o'zgarish tarixi (loglar asosida)",
)
async def products_history(
    _: AdminUser = Depends(verify_admin_credentials),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    action: Optional[str] = Query(None, description="Masalan: excel_create, excel_update"),
    limit: int = Query(200, ge=1, le=2000),
):
    try:
        dt_from, dt_to = _parse_date_range(date_from, date_to)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sana formati noto'g'ri (ISO kerak)")

    query = select(AuditLog).where(AuditLog.entity == "product").order_by(desc(AuditLog.created_at))
    criteria = []
    if action:
        criteria.append(AuditLog.action == action)
    if dt_from:
        criteria.append(AuditLog.created_at >= dt_from)
    if dt_to:
        criteria.append(AuditLog.created_at <= dt_to)
    if criteria:
        query = query.where(and_(*criteria))
    query = query.limit(limit)
    rows = (await db.execute(query)).scalars().all()
    return ok_response(rows, meta={"count": len(rows)})


@history_router.get(
    "/logs",
    summary="Tizim loglari tarixi",
)
async def logs_history(
    _: AdminUser = Depends(verify_admin_credentials),
    entity: Optional[str] = Query(None, description="Masalan: product, order, payment"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=3000),
):
    try:
        dt_from, dt_to = _parse_date_range(date_from, date_to)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sana formati noto'g'ri (ISO kerak)")

    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    criteria = []
    if entity:
        criteria.append(AuditLog.entity == entity)
    if dt_from:
        criteria.append(AuditLog.created_at >= dt_from)
    if dt_to:
        criteria.append(AuditLog.created_at <= dt_to)
    if criteria:
        query = query.where(and_(*criteria))
    query = query.limit(limit)
    rows = (await db.execute(query)).scalars().all()
    return ok_response(rows, meta={"count": len(rows)})


@history_router.get(
    "/stats/sales",
    summary="Sotuv statistikasi (sanadan sanagacha, operator/admin)",
)
async def sales_stats(
    _: AdminUser = Depends(verify_admin_credentials),
    date_from: Optional[str] = Query(None, description="ISO sana: 2026-04-28 yoki 2026-04-28T10:00:00"),
    date_to: Optional[str] = Query(None, description="ISO sana: 2026-04-30 yoki 2026-04-30T23:59:59"),
):
    try:
        dt_from, dt_to = _parse_date_range(date_from, date_to)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sana formati noto'g'ri (ISO kerak)")

    total_orders_query = select(func.count(Order.id))
    total_criteria = []
    if dt_from:
        total_criteria.append(Order.created_at >= dt_from)
    if dt_to:
        total_criteria.append(Order.created_at <= dt_to)
    if total_criteria:
        total_orders_query = total_orders_query.where(and_(*total_criteria))

    sold_statuses = [
        Order.StatusOrder.PAID.value,
        Order.StatusOrder.IS_PROCESS.value,
        Order.StatusOrder.READY.value,
        Order.StatusOrder.IN_PROGRESS.value,
        Order.StatusOrder.DELIVERED.value,
    ]

    sales_query = (
        select(
            func.count(func.distinct(Order.id)).label("paid_orders"),
            func.coalesce(func.sum(OrderItem.count), 0).label("sold_items_count"),
            func.coalesce(func.sum(OrderItem.total), 0).label("sales_amount"),
        )
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(Order.status.in_(sold_statuses))
    )

    sales_criteria = []
    if dt_from:
        sales_criteria.append(Order.created_at >= dt_from)
    if dt_to:
        sales_criteria.append(Order.created_at <= dt_to)
    if sales_criteria:
        sales_query = sales_query.where(and_(*sales_criteria))

    total_orders = (await db.execute(total_orders_query)).scalar() or 0
    sales_row = (await db.execute(sales_query)).one()

    payment_breakdown_query = (
        select(
            Order.payment.label("payment"),
            func.count(func.distinct(Order.id)).label("orders_count"),
            func.coalesce(func.sum(OrderItem.count), 0).label("items_count"),
            func.coalesce(func.sum(OrderItem.total), 0).label("amount"),
        )
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(Order.status.in_(sold_statuses))
        .group_by(Order.payment)
    )
    if sales_criteria:
        payment_breakdown_query = payment_breakdown_query.where(and_(*sales_criteria))

    breakdown_rows = (await db.execute(payment_breakdown_query)).all()
    payment_breakdown = {
        "click": {"orders_count": 0, "items_count": 0, "amount": 0},
        "payme": {"orders_count": 0, "items_count": 0, "amount": 0},
        "cash": {"orders_count": 0, "items_count": 0, "amount": 0},
    }
    for row in breakdown_rows:
        payment_key = getattr(row.payment, "value", str(row.payment)).lower()
        if payment_key not in payment_breakdown:
            payment_breakdown[payment_key] = {"orders_count": 0, "items_count": 0, "amount": 0}
        payment_breakdown[payment_key] = {
            "orders_count": int(row.orders_count or 0),
            "items_count": int(row.items_count or 0),
            "amount": int(row.amount or 0),
        }

    return ok_response(
        {
            "from": date_from,
            "to": date_to,
            "total_orders": int(total_orders),
            "paid_orders": int(sales_row.paid_orders or 0),
            "sold_items_count": int(sales_row.sold_items_count or 0),
            "sales_amount": int(sales_row.sales_amount or 0),
            "payment_breakdown": payment_breakdown,
            "currency": "UZS",
        }
    )
