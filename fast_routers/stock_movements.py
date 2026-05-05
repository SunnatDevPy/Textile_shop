"""Stock movements API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload

from models import db, StockMovement, ProductItems, AdminUser
from models.stock_movements import StockMovement as StockMovementModel
from fast_routers.admin_users import get_current_admin_user
from utils.logger import logger

router = APIRouter(prefix="/stock-movements", tags=["Stock Movements"])


class StockMovementCreate(BaseModel):
    product_item_id: int
    movement_type: str  # kirim, chiqim, tuzatish
    quantity: int
    reason: str  # xarid, sotuv, qaytarish, buzilgan, tuzatish, boshlangich
    reference_id: Optional[int] = None
    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: int
    product_item_id: int
    movement_type: str
    quantity: int
    reason: str
    reference_id: Optional[int]
    notes: Optional[str]
    created_by: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=StockMovementResponse)
async def create_stock_movement(
    data: StockMovementCreate,
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """Ombor harakatini yaratish"""

    # Product item mavjudligini tekshirish
    product_item = await db.get(ProductItems, data.product_item_id)
    if not product_item:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    # Ombor harakatini yaratish
    movement = StockMovement(
        product_item_id=data.product_item_id,
        movement_type=data.movement_type,
        quantity=data.quantity,
        reason=data.reason,
        reference_id=data.reference_id,
        notes=data.notes,
        created_by=current_user.id
    )

    db.add(movement)

    # Total count ni yangilash
    if data.movement_type == "kirim":
        product_item.total_count += data.quantity
    elif data.movement_type == "chiqim":
        if product_item.total_count < data.quantity:
            raise HTTPException(status_code=400, detail="Omborda yetarli mahsulot yo'q")
        product_item.total_count -= data.quantity
    elif data.movement_type == "tuzatish":
        # Tuzatish uchun yangi qiymatni to'g'ridan-to'g'ri o'rnatish
        product_item.total_count = data.quantity

    await db.commit()
    await db.refresh(movement)

    logger.info(
        "Stock movement created",
        {
            "movement_id": movement.id,
            "product_item_id": data.product_item_id,
            "type": data.movement_type,
            "quantity": data.quantity,
            "user_id": current_user.id
        }
    )

    return movement


@router.get("/", response_model=list[StockMovementResponse])
async def get_stock_movements(
    product_item_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    reason: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """Ombor harakatlarini olish"""

    query = select(StockMovement).options(
        joinedload(StockMovement.product_item),
        joinedload(StockMovement.admin_user)
    )

    if product_item_id:
        query = query.where(StockMovement.product_item_id == product_item_id)

    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)

    if reason:
        query = query.where(StockMovement.reason == reason)

    query = query.order_by(desc(StockMovement.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    movements = result.scalars().all()

    return movements


@router.get("/product-item/{product_item_id}/history")
async def get_product_item_history(
    product_item_id: int,
    limit: int = Query(50, le=200),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """Mahsulot uchun ombor harakatlari tarixi"""

    product_item = await db.get(ProductItems, product_item_id)
    if not product_item:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    query = select(StockMovement).where(
        StockMovement.product_item_id == product_item_id
    ).order_by(desc(StockMovement.created_at)).limit(limit)

    result = await db.execute(query)
    movements = result.scalars().all()

    return {
        "product_item_id": product_item_id,
        "current_stock": product_item.total_count,
        "min_stock_level": product_item.min_stock_level,
        "is_low_stock": product_item.is_low_stock,
        "movements": movements
    }


@router.get("/statistics")
async def get_stock_statistics(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """Ombor statistikasi"""

    # Jami harakatlar soni
    total_movements = await db.scalar(select(func.count(StockMovement.id)))

    # Kirim/chiqim statistikasi
    kirim_count = await db.scalar(
        select(func.count(StockMovement.id)).where(
            StockMovement.movement_type == "kirim"
        )
    )

    chiqim_count = await db.scalar(
        select(func.count(StockMovement.id)).where(
            StockMovement.movement_type == "chiqim"
        )
    )

    tuzatish_count = await db.scalar(
        select(func.count(StockMovement.id)).where(
            StockMovement.movement_type == "tuzatish"
        )
    )

    # Kam qolgan mahsulotlar
    low_stock_query = select(ProductItems).where(
        ProductItems.total_count <= ProductItems.min_stock_level
    )
    low_stock_result = await db.execute(low_stock_query)
    low_stock_items = low_stock_result.scalars().all()

    # Tugagan mahsulotlar
    out_of_stock_query = select(ProductItems).where(ProductItems.total_count == 0)
    out_of_stock_result = await db.execute(out_of_stock_query)
    out_of_stock_items = out_of_stock_result.scalars().all()

    return {
        "total_movements": total_movements,
        "movements_by_type": {
            "kirim": kirim_count,
            "chiqim": chiqim_count,
            "tuzatish": tuzatish_count
        },
        "low_stock_count": len(low_stock_items),
        "out_of_stock_count": len(out_of_stock_items),
        "low_stock_items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "total_count": item.total_count,
                "min_stock_level": item.min_stock_level
            }
            for item in low_stock_items
        ],
        "out_of_stock_items": [
            {
                "id": item.id,
                "product_id": item.product_id
            }
            for item in out_of_stock_items
        ]
    }
