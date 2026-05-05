"""Dashboard statistics API endpoints."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, desc
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

    today_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= today_start,
                Order.status.in_(["to'landi", "tayyor", "yetkazilmoqda", "yetkazildi"])
            )
        )
    )
    today_revenue = today_revenue_result.scalar() or 0

    # Haftalik statistika
    week_orders = await db.scalar(
        select(func.count(Order.id)).where(Order.created_at >= week_start)
    )

    week_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= week_start,
                Order.status.in_(["to'landi", "tayyor", "yetkazilmoqda", "yetkazildi"])
            )
        )
    )
    week_revenue = week_revenue_result.scalar() or 0

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

    month_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= month_start,
                Order.status.in_(["to'landi", "tayyor", "yetkazilmoqda", "yetkazildi"])
            )
        )
    )
    month_revenue = month_revenue_result.scalar() or 0

    # O'sish foizi (haftalik vs oldingi hafta)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_revenue_result = await db.execute(
        select(func.sum(OrderItem.total)).join(Order).where(
            and_(
                Order.created_at >= prev_week_start,
                Order.created_at < week_start,
                Order.status.in_(["to'landi", "tayyor", "yetkazilmoqda", "yetkazildi"])
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
            "revenue": today_revenue
        },
        "week": {
            "orders_count": week_orders,
            "revenue": week_revenue,
            "top_products": week_top_products
        },
        "month": {
            "orders_count": month_orders,
            "revenue": month_revenue,
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

    # Kunlik sotuvlar
    daily_sales_query = select(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('orders_count'),
        func.sum(OrderItem.total).label('revenue')
    ).join(OrderItem).where(
        and_(
            Order.created_at >= start_date,
            Order.status.in_(["to'landi", "tayyor", "yetkazilmoqda", "yetkazildi"])
        )
    ).group_by(func.date(Order.created_at)).order_by('date')

    result = await db.execute(daily_sales_query)
    daily_sales = [
        {
            "date": str(row.date),
            "orders_count": row.orders_count,
            "revenue": row.revenue or 0
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
