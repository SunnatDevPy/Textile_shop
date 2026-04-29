import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, desc, func, select

from fast_routers.admin_auth import verify_admin_credentials
from models import AdminUser, AuditLog, Order, OrderItem, Product, ProductItems
from models.database import db
from utils.response import ok_response
from utils.security import enforce_rate_limit

history_router = APIRouter(prefix="/history", tags=["History"])
logger = logging.getLogger(__name__)


def _parse_date_range(
    date_from: Optional[str],
    date_to: Optional[str],
) -> tuple[Optional[datetime], Optional[datetime]]:
    dt_from = datetime.fromisoformat(date_from) if date_from else None
    dt_to = datetime.fromisoformat(date_to) if date_to else None

    # Agar query faqat sana ko'rinishida bo'lsa (YYYY-MM-DD),
    # date_to ni shu kunning oxirigacha kengaytiramiz (23:59:59.999999).
    if date_to and "T" not in date_to and dt_to:
        dt_to = (dt_to + timedelta(days=1)) - timedelta(microseconds=1)
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
    request: Request,
    _: AdminUser = Depends(verify_admin_credentials),
    date_from: Optional[str] = Query(None, description="ISO sana: 2026-04-28 yoki 2026-04-28T10:00:00"),
    date_to: Optional[str] = Query(None, description="ISO sana: 2026-04-30 yoki 2026-04-30T23:59:59"),
):
    enforce_rate_limit(request, scope="analytics")
    # Global session oldingi requestda xato bo'lib qolgan bo'lsa, tozalab olamiz.
    await db.rollback()
    try:
        dt_from, dt_to = _parse_date_range(date_from, date_to)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sana formati noto'g'ri (ISO kerak)")
    try:
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

        gender_rows = (
            await db.execute(
                select(
                    Product.clothing_type.label("clothing_type"),
                    func.coalesce(func.sum(OrderItem.count), 0).label("sold_items"),
                    func.coalesce(func.sum(OrderItem.total), 0).label("sales_amount"),
                )
                .select_from(OrderItem)
                .join(Order, Order.id == OrderItem.order_id)
                .join(Product, Product.id == OrderItem.product_id)
                .where(Order.status.in_(sold_statuses))
                .where(and_(*sales_criteria) if sales_criteria else True)
                .group_by(Product.clothing_type)
            )
        ).all()
        sales_by_clothing_type = {
            Product.ClothingType.MEN.value: {"sold_items": 0, "sales_amount": 0},
            Product.ClothingType.WOMEN.value: {"sold_items": 0, "sales_amount": 0},
        }
        for row in gender_rows:
            key = str(row.clothing_type or Product.ClothingType.MEN.value)
            sales_by_clothing_type.setdefault(key, {"sold_items": 0, "sales_amount": 0})
            sales_by_clothing_type[key] = {
                "sold_items": int(row.sold_items or 0),
                "sales_amount": int(row.sales_amount or 0),
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
                "sales_by_clothing_type": sales_by_clothing_type,
                "currency": "UZS",
            }
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sales statistikani olishda xatolik",
        )


@history_router.get(
    "/stats/analytics-v2",
    summary="Analytics v2: top products, conversion, avg check, LTV, repeat, day/week sales",
)
async def analytics_v2(
    request: Request,
    _: AdminUser = Depends(verify_admin_credentials),
    date_from: Optional[str] = Query(None, description="ISO sana: 2026-04-28 yoki 2026-04-28T10:00:00"),
    date_to: Optional[str] = Query(None, description="ISO sana: 2026-04-30 yoki 2026-04-30T23:59:59"),
    top_limit: int = Query(10, ge=1, le=100),
):
    enforce_rate_limit(request, scope="analytics")
    # Global session oldingi requestda xato bo'lib qolgan bo'lsa, tozalab olamiz.
    await db.rollback()
    try:
        dt_from, dt_to = _parse_date_range(date_from, date_to)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sana formati noto'g'ri (ISO kerak)")
    try:
        sold_statuses = [
            Order.StatusOrder.PAID.value,
            Order.StatusOrder.IS_PROCESS.value,
            Order.StatusOrder.READY.value,
            Order.StatusOrder.IN_PROGRESS.value,
            Order.StatusOrder.DELIVERED.value,
        ]

        base_criteria = []
        if dt_from:
            base_criteria.append(Order.created_at >= dt_from)
        if dt_to:
            base_criteria.append(Order.created_at <= dt_to)

        # 1) Conversion by status + total orders
        total_orders_q = select(func.count(Order.id))
        if base_criteria:
            total_orders_q = total_orders_q.where(and_(*base_criteria))
        total_orders = int((await db.execute(total_orders_q)).scalar() or 0)

        status_q = (
            select(
                Order.status.label("status"),
                func.count(Order.id).label("count"),
            )
            .select_from(Order)
            .group_by(Order.status)
        )
        if base_criteria:
            status_q = status_q.where(and_(*base_criteria))
        status_rows = (await db.execute(status_q)).all()
        conversion_by_status = {}
        for row in status_rows:
            status_key = getattr(row.status, "value", str(row.status))
            count_val = int(row.count or 0)
            conversion_by_status[status_key] = {
                "orders_count": count_val,
                "rate": (count_val / total_orders) if total_orders else 0.0,
            }

        # 2) Top products (by quantity + revenue)
        top_products_q = (
            select(
                OrderItem.product_id.label("product_id"),
                Product.name_uz.label("name_uz"),
                func.sum(OrderItem.count).label("sold_items"),
                func.sum(OrderItem.total).label("revenue"),
            )
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(Order.status.in_(sold_statuses))
            .group_by(OrderItem.product_id, Product.name_uz)
            .order_by(desc(func.sum(OrderItem.count)), desc(func.sum(OrderItem.total)))
            .limit(top_limit)
        )
        if base_criteria:
            top_products_q = top_products_q.where(and_(*base_criteria))
        top_rows = (await db.execute(top_products_q)).all()
        top_products = [
            {
                "product_id": int(row.product_id),
                "name_uz": row.name_uz,
                "sold_items": int(row.sold_items or 0),
                "revenue": int(row.revenue or 0),
            }
            for row in top_rows
        ]

        # 3) Average check (sold orders only)
        sold_order_totals_q = (
            select(
                Order.id.label("order_id"),
                func.coalesce(func.sum(OrderItem.total), 0).label("order_total"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.status.in_(sold_statuses))
            .group_by(Order.id)
        )
        if base_criteria:
            sold_order_totals_q = sold_order_totals_q.where(and_(*base_criteria))
        sold_order_totals_rows = (await db.execute(sold_order_totals_q)).all()
        sold_orders_count = len(sold_order_totals_rows)
        sold_orders_revenue = sum(int(r.order_total or 0) for r in sold_order_totals_rows)
        avg_check = int(sold_orders_revenue / sold_orders_count) if sold_orders_count else 0

        # 4) LTV (by customer contact)
        ltv_q = (
            select(
                Order.contact.label("contact"),
                func.count(func.distinct(Order.id)).label("orders_count"),
                func.coalesce(func.sum(OrderItem.total), 0).label("revenue"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.status.in_(sold_statuses))
            .group_by(Order.contact)
        )
        if base_criteria:
            ltv_q = ltv_q.where(and_(*base_criteria))
        ltv_rows = (await db.execute(ltv_q)).all()
        customers_count = len(ltv_rows)
        total_ltv_revenue = sum(int(r.revenue or 0) for r in ltv_rows)
        avg_ltv = int(total_ltv_revenue / customers_count) if customers_count else 0
        top_customers_by_ltv = [
            {
                "contact": r.contact,
                "orders_count": int(r.orders_count or 0),
                "ltv": int(r.revenue or 0),
            }
            for r in sorted(ltv_rows, key=lambda x: int(x.revenue or 0), reverse=True)[:top_limit]
        ]

        # 5) Repeat sales (by contact)
        repeat_customers = sum(1 for r in ltv_rows if int(r.orders_count or 0) > 1)
        repeat_sales = {
            "customers_count": customers_count,
            "repeat_customers_count": int(repeat_customers),
            "repeat_customer_rate": (repeat_customers / customers_count) if customers_count else 0.0,
        }

        # 6) Sales by day
        sales_by_day_q = (
            select(
                func.date_trunc("day", Order.created_at).label("bucket"),
                func.count(func.distinct(Order.id)).label("orders_count"),
                func.coalesce(func.sum(OrderItem.total), 0).label("revenue"),
                func.coalesce(func.sum(OrderItem.count), 0).label("sold_items"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.status.in_(sold_statuses))
            .group_by(func.date_trunc("day", Order.created_at))
            .order_by(func.date_trunc("day", Order.created_at))
        )
        if base_criteria:
            sales_by_day_q = sales_by_day_q.where(and_(*base_criteria))
        sales_by_day_rows = (await db.execute(sales_by_day_q)).all()
        sales_by_day = []
        for row in sales_by_day_rows:
            if not row.bucket:
                continue
            sales_by_day.append(
                {
                    "date": row.bucket.date().isoformat(),
                    "orders_count": int(row.orders_count or 0),
                    "sold_items": int(row.sold_items or 0),
                    "revenue": int(row.revenue or 0),
                }
            )

        # 7) Sales by week
        sales_by_week_q = (
            select(
                func.date_trunc("week", Order.created_at).label("bucket"),
                func.count(func.distinct(Order.id)).label("orders_count"),
                func.coalesce(func.sum(OrderItem.total), 0).label("revenue"),
                func.coalesce(func.sum(OrderItem.count), 0).label("sold_items"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.status.in_(sold_statuses))
            .group_by(func.date_trunc("week", Order.created_at))
            .order_by(func.date_trunc("week", Order.created_at))
        )
        if base_criteria:
            sales_by_week_q = sales_by_week_q.where(and_(*base_criteria))
        sales_by_week_rows = (await db.execute(sales_by_week_q)).all()
        sales_by_week = []
        for row in sales_by_week_rows:
            if not row.bucket:
                continue
            sales_by_week.append(
                {
                    "week_start": row.bucket.date().isoformat(),
                    "orders_count": int(row.orders_count or 0),
                    "sold_items": int(row.sold_items or 0),
                    "revenue": int(row.revenue or 0),
                }
            )

        return ok_response(
            {
                "from": date_from,
                "to": date_to,
                "currency": "UZS",
                "top_products": top_products,
                "conversion_by_status": conversion_by_status,
                "average_check": {
                    "sold_orders_count": sold_orders_count,
                    "sold_orders_revenue": sold_orders_revenue,
                    "avg_check": avg_check,
                },
                "ltv": {
                    "customers_count": customers_count,
                    "avg_ltv": avg_ltv,
                    "top_customers": top_customers_by_ltv,
                },
                "repeat_sales": repeat_sales,
                "sales_by_day": sales_by_day,
                "sales_by_week": sales_by_week,
            }
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("analytics_v2 failed: %s", exc)
        # Bu endpoint demo/panel uchun tez-tez ishlatiladi.
        # Xatolik bo'lsa ham 500 bermay, bo'sh fallback qaytaramiz.
        return ok_response(
            {
                "from": date_from,
                "to": date_to,
                "currency": "UZS",
                "top_products": [],
                "conversion_by_status": {},
                "average_check": {
                    "sold_orders_count": 0,
                    "sold_orders_revenue": 0,
                    "avg_check": 0,
                },
                "ltv": {
                    "customers_count": 0,
                    "avg_ltv": 0,
                    "top_customers": [],
                },
                "repeat_sales": {
                    "customers_count": 0,
                    "repeat_customers_count": 0,
                    "repeat_customer_rate": 0.0,
                },
                "sales_by_day": [],
                "sales_by_week": [],
                "warning": f"analytics_v2 fallback: {exc.__class__.__name__}",
            },
            meta={"partial": True},
        )


@history_router.get(
    "/stats/dashboard",
    summary="Admin dashboard summary: today/week sales, new orders, low stock, top products",
)
async def dashboard_stats(
    request: Request,
    _: AdminUser = Depends(verify_admin_credentials),
    low_stock_threshold: int = Query(5, ge=0, le=1000),
    low_stock_limit: int = Query(10, ge=1, le=100),
    top_limit: int = Query(10, ge=1, le=100),
):
    enforce_rate_limit(request, scope="analytics")

    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=today_start.weekday())

    sold_statuses = [
        Order.StatusOrder.PAID.value,
        Order.StatusOrder.IS_PROCESS.value,
        Order.StatusOrder.READY.value,
        Order.StatusOrder.IN_PROGRESS.value,
        Order.StatusOrder.DELIVERED.value,
    ]

    async def _sales_between(start_dt: datetime):
        row = (
            await db.execute(
                select(
                    func.count(func.distinct(Order.id)).label("orders_count"),
                    func.coalesce(func.sum(OrderItem.count), 0).label("sold_items"),
                    func.coalesce(func.sum(OrderItem.total), 0).label("revenue"),
                )
                .select_from(Order)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(Order.status.in_(sold_statuses), Order.created_at >= start_dt)
            )
        ).one()
        return {
            "orders_count": int(row.orders_count or 0),
            "sold_items": int(row.sold_items or 0),
            "revenue": int(row.revenue or 0),
        }

    today_sales = await _sales_between(today_start)
    week_sales = await _sales_between(week_start)

    new_orders = int(
        (
            await db.execute(
                select(func.count(Order.id)).where(Order.status == Order.StatusOrder.NEW.value)
            )
        ).scalar()
        or 0
    )

    low_stock_rows = (
        await db.execute(
            select(
                ProductItems.id.label("product_item_id"),
                ProductItems.product_id.label("product_id"),
                ProductItems.color_id.label("color_id"),
                ProductItems.size_id.label("size_id"),
                ProductItems.total_count.label("stock"),
                Product.name_uz.label("product_name_uz"),
            )
            .select_from(ProductItems)
            .join(Product, Product.id == ProductItems.product_id)
            .where(ProductItems.total_count <= low_stock_threshold)
            .order_by(ProductItems.total_count.asc(), ProductItems.id.asc())
            .limit(low_stock_limit)
        )
    ).all()
    low_stock = [
        {
            "product_item_id": int(r.product_item_id),
            "product_id": int(r.product_id),
            "product_name_uz": r.product_name_uz,
            "color_id": int(r.color_id),
            "size_id": int(r.size_id),
            "stock": int(r.stock),
        }
        for r in low_stock_rows
    ]

    top_products_rows = (
        await db.execute(
            select(
                OrderItem.product_id.label("product_id"),
                Product.name_uz.label("name_uz"),
                func.sum(OrderItem.count).label("sold_items"),
                func.sum(OrderItem.total).label("revenue"),
            )
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(Order.status.in_(sold_statuses))
            .group_by(OrderItem.product_id, Product.name_uz)
            .order_by(desc(func.sum(OrderItem.count)), desc(func.sum(OrderItem.total)))
            .limit(top_limit)
        )
    ).all()
    top_products = [
        {
            "product_id": int(r.product_id),
            "name_uz": r.name_uz,
            "sold_items": int(r.sold_items or 0),
            "revenue": int(r.revenue or 0),
        }
        for r in top_products_rows
    ]

    inventory_row = (
        await db.execute(
            select(
                func.coalesce(func.sum(ProductItems.total_count), 0).label("total_stock"),
                func.coalesce(func.sum(ProductItems.total_count * Product.price), 0).label("total_inventory_value"),
                func.count(func.distinct(Product.id)).label("products_count"),
                func.count(ProductItems.id).label("sku_count"),
            )
            .select_from(ProductItems)
            .join(Product, Product.id == ProductItems.product_id)
        )
    ).one()
    inventory_summary = {
        "products_count": int(inventory_row.products_count or 0),
        "sku_count": int(inventory_row.sku_count or 0),
        "total_stock": int(inventory_row.total_stock or 0),
        "total_inventory_value": int(inventory_row.total_inventory_value or 0),
    }

    inventory_gender_rows = (
        await db.execute(
            select(
                Product.clothing_type.label("clothing_type"),
                func.coalesce(func.sum(ProductItems.total_count), 0).label("stock"),
                func.coalesce(func.sum(ProductItems.total_count * Product.price), 0).label("inventory_value"),
            )
            .select_from(ProductItems)
            .join(Product, Product.id == ProductItems.product_id)
            .group_by(Product.clothing_type)
        )
    ).all()
    inventory_by_clothing_type = {
        Product.ClothingType.MEN.value: {"stock": 0, "inventory_value": 0},
        Product.ClothingType.WOMEN.value: {"stock": 0, "inventory_value": 0},
    }
    for row in inventory_gender_rows:
        key = str(row.clothing_type or Product.ClothingType.MEN.value)
        inventory_by_clothing_type.setdefault(key, {"stock": 0, "inventory_value": 0})
        inventory_by_clothing_type[key] = {
            "stock": int(row.stock or 0),
            "inventory_value": int(row.inventory_value or 0),
        }

    return ok_response(
        {
            "generated_at": now.isoformat(),
            "today_sales": today_sales,
            "week_sales": week_sales,
            "new_orders": new_orders,
            "low_stock": low_stock,
            "top_products": top_products,
            "inventory_summary": inventory_summary,
            "inventory_by_clothing_type": inventory_by_clothing_type,
            "currency": "UZS",
        }
    )


@history_router.get(
    "/stats/inventory",
    summary="Sklad statistikasi: jami stock va umumiy tovar qiymati",
)
async def inventory_stats(
    request: Request,
    _: AdminUser = Depends(verify_admin_credentials),
):
    enforce_rate_limit(request, scope="analytics")
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(ProductItems.total_count), 0).label("total_stock"),
                func.coalesce(func.sum(ProductItems.total_count * Product.price), 0).label("total_inventory_value"),
                func.count(func.distinct(Product.id)).label("products_count"),
                func.count(ProductItems.id).label("sku_count"),
            )
            .select_from(ProductItems)
            .join(Product, Product.id == ProductItems.product_id)
        )
    ).one()
    by_gender_rows = (
        await db.execute(
            select(
                Product.clothing_type.label("clothing_type"),
                func.coalesce(func.sum(ProductItems.total_count), 0).label("stock"),
                func.coalesce(func.sum(ProductItems.total_count * Product.price), 0).label("inventory_value"),
            )
            .select_from(ProductItems)
            .join(Product, Product.id == ProductItems.product_id)
            .group_by(Product.clothing_type)
        )
    ).all()
    by_clothing_type = {
        Product.ClothingType.MEN.value: {"stock": 0, "inventory_value": 0},
        Product.ClothingType.WOMEN.value: {"stock": 0, "inventory_value": 0},
    }
    for r in by_gender_rows:
        key = str(r.clothing_type or Product.ClothingType.MEN.value)
        by_clothing_type.setdefault(key, {"stock": 0, "inventory_value": 0})
        by_clothing_type[key] = {
            "stock": int(r.stock or 0),
            "inventory_value": int(r.inventory_value or 0),
        }

    return ok_response(
        {
            "products_count": int(row.products_count or 0),
            "sku_count": int(row.sku_count or 0),
            "total_stock": int(row.total_stock or 0),
            "total_inventory_value": int(row.total_inventory_value or 0),
            "by_clothing_type": by_clothing_type,
            "currency": "UZS",
        }
    )
