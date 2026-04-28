from fastapi import APIRouter

from models import (
    Category,
    Collection,
    Color,
    MainPhoto,
    Product,
    ProductDetail,
    ProductItems,
    ProductPhoto,
    Size,
)

frontend_router = APIRouter(prefix="/frontend", tags=["Frontend"])


@frontend_router.get(
    "/bootstrap",
    summary="Frontend uchun barcha asosiy ma'lumotlar",
)
async def frontend_bootstrap(include_inactive: bool = False):
    products = await Product.all()
    if not include_inactive:
        products = [p for p in products if bool(getattr(p, "is_active", False))]

    return {
        "ok": True,
        "banners": await MainPhoto.all(),
        "categories": await Category.all(),
        "collections": await Collection.all(),
        "colors": await Color.all(),
        "sizes": await Size.all(),
        "products": products,
        "product_items": await ProductItems.all(),
        "product_photos": await ProductPhoto.all(),
        "product_details": await ProductDetail.all(),
    }
