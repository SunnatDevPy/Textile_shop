"""Dashboard statistics API endpoints."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, desc, cast, Date
from sqlalchemy.orm import joinedload

from models import db, Order, OrderItem, Product, ProductItems, AdminUser
from fast_routers.admin_auth import verify_admin_credentials
from utils.logger import logger

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/statistics")
async def get_dashboard_statistics(
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Dashboard statistikasi - bugungi, haftalik, oylik"""

    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Bugungi statistika
    today_orders = await db.scalar(
        select(func.count(Order.id)).where(Order.created_at >= today_start)
    )

    # Bugungi daromad - faqat to'langan buyurtmalar
    today_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= today_start,
                Order.payment.in_([Order.Payment.CLICK, Order.Payment.PAYME, Order.Payment.CASH])
            )
        )
    )
    today_revenue = today_revenue_result.scalar() or 0

    # Bugungi to'lanmagan buyurtmalar
    today_unpaid_result = await db.execute(
        select(func.count(Order.id)).where(
            and_(
                Order.created_at >= today_start,
                Order.status == Order.StatusOrder.NEW
            )
        )
    )
    today_unpaid = today_unpaid_result.scalar() or 0

    # Haftalik statistika
    week_orders = await db.scalar(
        select(func.count(Order.id)).where(Order.created_at >= week_start)
    )

    # Haftalik daromad - faqat to'langan buyurtmalar
    week_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= week_start,
                Order.payment.in_([Order.Payment.CLICK, Order.Payment.PAYME, Order.Payment.CASH])
            )
        )
    )
    week_revenue = week_revenue_result.scalar() or 0

    # Haftalik to'lanmagan buyurtmalar
    week_unpaid_result = await db.execute(
        select(func.count(Order.id)).where(
            and_(
                Order.created_at >= week_start,
                Order.status == Order.StatusOrder.NEW
            )
        )
    )
    week_unpaid = week_unpaid_result.scalar() or 0

    # Haftalik top mahsulotlar
    week_top_products_query = select(
        Product.id,
        Product.name_uz,
        func.sum(OrderItem.count).label('total_sold'),
        func.sum(OrderItem.total).label('total_revenue')
    ).join(OrderItem).join(Order).where(
        Order.created_at >= week_start
    ).group_by(Product.id, Product.name_uz).order_by(desc('total_sold')).limit(5)

    week_top_products_result = await db.execute(week_top_products_query)
    week_top_products = [
        {
            "product_id": row.id,
            "name": row.name_uz,
            "total_sold": row.total_sold,
            "total_revenue": row.total_revenue
        }
        for row in week_top_products_result
    ]

    # Oylik statistika
    month_orders = await db.scalar(
        select(func.count(Order.id)).where(Order.created_at >= month_start)
    )

    # Oylik daromad - faqat to'langan buyurtmalar
    month_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= month_start,
                Order.payment.in_([Order.Payment.CLICK, Order.Payment.PAYME, Order.Payment.CASH])
            )
        )
    )
    month_revenue = month_revenue_result.scalar() or 0

    # Oylik to'lanmagan buyurtmalar
    month_unpaid_result = await db.execute(
        select(func.count(Order.id)).where(
            and_(
                Order.created_at >= month_start,
                Order.status == Order.StatusOrder.NEW
            )
        )
    )
    month_unpaid = month_unpaid_result.scalar() or 0

    # O'sish foizi (haftalik vs oldingi hafta)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= prev_week_start,
                Order.created_at < week_start,
                Order.payment.in_([Order.Payment.CLICK, Order.Payment.PAYME, Order.Payment.CASH])
            )
        )
    )
    prev_week_revenue = prev_week_revenue_result.scalar() or 0

    growth_percent = 0
    if prev_week_revenue > 0:
        growth_percent = round(((week_revenue - prev_week_revenue) / prev_week_revenue) * 100, 2)

    # Ombor holati
    low_stock_query = select(ProductItems).where(
        ProductItems.total_count <= ProductItems.min_stock_level
    ).options(joinedload(ProductItems.product))
    low_stock_result = await db.execute(low_stock_query)
    low_stock_items = low_stock_result.scalars().all()

    out_of_stock_query = select(ProductItems).where(
        ProductItems.total_count == 0
    ).options(joinedload(ProductItems.product))
    out_of_stock_result = await db.execute(out_of_stock_query)
    out_of_stock_items = out_of_stock_result.scalars().all()

    # Jami ombor qiymati
    total_value_query = select(
        func.sum(ProductItems.total_count * Product.price)
    ).join(Product)
    total_value_result = await db.execute(total_value_query)
    total_inventory_value = total_value_result.scalar() or 0

    return {
        "today": {
            "orders_count": today_orders,
            "revenue": today_revenue,
            "unpaid_count": today_unpaid
        },
        "week": {
            "orders_count": week_orders,
            "revenue": week_revenue,
            "unpaid_count": week_unpaid,
            "top_products": week_top_products
        },
        "month": {
            "orders_count": month_orders,
            "revenue": month_revenue,
            "unpaid_count": month_unpaid,
            "growth_percent": growth_percent
        },
        "inventory": {
            "low_stock_count": len(low_stock_items),
            "out_of_stock_count": len(out_of_stock_items),
            "total_value": total_inventory_value,
            "low_stock_items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.name_uz if item.product else "N/A",
                    "total_count": item.total_count,
                    "min_stock_level": item.min_stock_level
                }
                for item in low_stock_items[:10]  # Faqat birinchi 10 ta
            ],
            "out_of_stock_items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.name_uz if item.product else "N/A"
                }
                for item in out_of_stock_items[:10]  # Faqat birinchi 10 ta
            ]
        }
    }


@router.get("/sales-chart")
async def get_sales_chart(
    days: int = Query(30, le=365),
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Sotuvlar grafigi - kunlik ma'lumotlar"""

    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day) - timedelta(days=days)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)

    # Kunlik sotuvlar - cast bilan date_trunc o'rniga
    daily_sales_query = select(
        cast(Order.created_at, Date).label('date'),
        func.count(func.distinct(Order.id)).label('orders_count'),
        func.coalesce(func.sum(OrderItem.total), 0).label('revenue'),
        func.coalesce(func.sum(OrderItem.count), 0).label('sold_items')
    ).join(OrderItem).where(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.payment.in_([Order.Payment.CLICK, Order.Payment.PAYME, Order.Payment.CASH])
        )
    ).group_by(cast(Order.created_at, Date)).order_by(cast(Order.created_at, Date))

    result = await db.execute(daily_sales_query)
    daily_sales = [
        {
            "date": str(row.date),
            "orders_count": row.orders_count,
            "revenue": row.revenue or 0,
            "sold_items": row.sold_items or 0
        }
        for row in result
    ]

    return {
        "period_days": days,
        "start_date": str(start_date.date()),
        "end_date": str(now.date()),
        "daily_sales": daily_sales
    }


@router.get("/top-products")
async def get_top_products(
    period: str = Query("month", regex="^(week|month|year)$"),
    limit: int = Query(10, le=50),
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Eng ko'p sotiladigan mahsulotlar"""

    now = datetime.now()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)

    top_products_query = select(
        Product.id,
        Product.name_uz,
        Product.price,
        func.sum(OrderItem.count).label('total_sold'),
        func.sum(OrderItem.total).label('total_revenue')
    ).join(OrderItem).join(Order).where(
        Order.created_at >= start_date
    ).group_by(Product.id, Product.name_uz, Product.price).order_by(
        desc('total_sold')
    ).limit(limit)

    result = await db.execute(top_products_query)
    top_products = [
        {
            "product_id": row.id,
            "name": row.name_uz,
            "price": row.price,
            "total_sold": row.total_sold,
            "total_revenue": row.total_revenue
        }
        for row in result
    ]

    return {
        "period": period,
        "start_date": str(start_date.date()),
        "top_products": top_products
    }


@router.get("/orders-by-status")
async def get_orders_by_status(
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Buyurtmalar status bo'yicha"""

    status_query = select(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status)

    result = await db.execute(status_query)
    orders_by_status = [
        {
            "status": row.status,
            "count": row.count
        }
        for row in result
    ]

    return {
        "orders_by_status": orders_by_status
    }


@router.get("/orders-by-payment")
async def get_orders_by_payment(
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Buyurtmalar to'lov turi bo'yicha"""

    payment_query = select(
        Order.payment,
        func.count(Order.id).label('count'),
        func.coalesce(func.sum(OrderItem.total), 0).label('total_amount')
    ).join(OrderItem).group_by(Order.payment)

    result = await db.execute(payment_query)
    orders_by_payment = [
        {
            "payment_type": row.payment,
            "count": row.count,
            "total_amount": row.total_amount or 0
        }
        for row in result
    ]

    # To'langan va to'lanmagan statistika
    paid_query = select(
        func.count(Order.id).label('paid_count'),
        func.coalesce(func.sum(OrderItem.total), 0).label('paid_amount')
    ).join(OrderItem).where(
        Order.payment.in_([Order.Payment.CLICK, Order.Payment.PAYME, Order.Payment.CASH])
    )

    unpaid_query = select(
        func.count(Order.id).label('unpaid_count')
    ).where(Order.status == Order.StatusOrder.NEW)

    paid_result = await db.execute(paid_query)
    unpaid_result = await db.execute(unpaid_query)

    paid_row = paid_result.first()
    unpaid_row = unpaid_result.first()

    return {
        "orders_by_payment": orders_by_payment,
        "summary": {
            "paid_count": paid_row.paid_count if paid_row else 0,
            "paid_amount": paid_row.paid_amount if paid_row else 0,
            "unpaid_count": unpaid_row.unpaid_count if unpaid_row else 0
        }
    }
