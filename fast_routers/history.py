from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, select

from fast_routers.admin_auth import verify_admin_credentials
from models import AdminUser, AuditLog, Order
from models.database import db

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
    return (await db.execute(query)).scalars().all()


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
    return (await db.execute(query)).scalars().all()


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
    return (await db.execute(query)).scalars().all()
