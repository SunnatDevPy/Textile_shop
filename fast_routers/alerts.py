"""Low stock alerts API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from models import db, ProductItems, Product, AdminUser
from fast_routers.admin_auth import verify_admin_credentials

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/low-stock")
async def get_low_stock_alerts(
    limit: int = Query(100, le=500),
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Kam qolgan mahsulotlar ro'yxati"""

    query = select(ProductItems).where(
        and_(
            ProductItems.total_count <= ProductItems.min_stock_level,
            ProductItems.total_count > 0
        )
    ).options(joinedload(ProductItems.product)).limit(limit)

    result = await db.execute(query)
    low_stock_items = result.scalars().all()

    return {
        "count": len(low_stock_items),
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name_uz if item.product else "N/A",
                "color_id": item.color_id,
                "size_id": item.size_id,
                "total_count": item.total_count,
                "min_stock_level": item.min_stock_level,
                "difference": item.min_stock_level - item.total_count
            }
            for item in low_stock_items
        ]
    }


@router.get("/out-of-stock")
async def get_out_of_stock_alerts(
    limit: int = Query(100, le=500),
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Tugagan mahsulotlar ro'yxati"""

    query = select(ProductItems).where(
        ProductItems.total_count == 0
    ).options(joinedload(ProductItems.product)).limit(limit)

    result = await db.execute(query)
    out_of_stock_items = result.scalars().all()

    return {
        "count": len(out_of_stock_items),
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name_uz if item.product else "N/A",
                "color_id": item.color_id,
                "size_id": item.size_id,
                "min_stock_level": item.min_stock_level
            }
            for item in out_of_stock_items
        ]
    }


@router.put("/product-items/{item_id}/min-stock")
async def update_min_stock_level(
    item_id: int,
    min_stock_level: int,
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Minimal qoldiq darajasini yangilash"""

    item = await db.get(ProductItems, item_id)
    if not item:
        return {"error": "Mahsulot topilmadi"}

    item.min_stock_level = min_stock_level
    await db.commit()

    return {
        "success": True,
        "item_id": item_id,
        "min_stock_level": min_stock_level,
        "is_low_stock": item.is_low_stock
    }
