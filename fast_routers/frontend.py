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


@frontend_router.get(
    "/bootstrap/normalized",
    summary="Frontend uchun ma'lumotlar (normalized, duplicate kamroq)",
)
async def frontend_bootstrap_normalized(include_inactive: bool = False):
    products = await Product.all()
    if not include_inactive:
        products = [p for p in products if bool(getattr(p, "is_active", False))]

    categories = {}
    collections = {}
    colors = {}
    sizes = {}
    product_items = {}
    product_photos = {}
    product_details = {}

    products_entities = {}

    for p in products:
        categories[p.category.id] = {
            "id": int(p.category.id),
            "name_uz": p.category.name_uz,
            "name_ru": p.category.name_ru,
            "name_eng": p.category.name_eng,
        }
        collections[p.collection.id] = {
            "id": int(p.collection.id),
            "name_uz": p.collection.name_uz,
            "name_ru": p.collection.name_ru,
            "name_eng": p.collection.name_eng,
        }

        item_ids = []
        for item in p.product_items:
            item_ids.append(int(item.id))
            colors[item.color_id] = int(item.color_id)
            sizes[item.size_id] = int(item.size_id)
            product_items[item.id] = {
                "id": int(item.id),
                "product_id": int(item.product_id),
                "color_id": int(item.color_id),
                "size_id": int(item.size_id),
                "total_count": int(item.total_count),
            }

        detail_ids = []
        for d in p.product_details:
            detail_ids.append(int(d.id))
            product_details[d.id] = {
                "id": int(d.id),
                "product_id": int(d.product_id),
                "name_uz": d.name_uz,
                "name_ru": d.name_ru,
                "name_eng": d.name_eng,
            }

        photo_ids = []
        p_photos = p.product_photos if isinstance(p.product_photos, list) else ([p.product_photos] if p.product_photos else [])
        for ph in p_photos:
            photo_ids.append(int(ph.id))
            product_photos[ph.id] = {
                "id": int(ph.id),
                "product_id": int(ph.product_id),
                "photo": str(getattr(ph, "photo", "")),
            }

        products_entities[int(p.id)] = {
            "id": int(p.id),
            "category_id": int(p.category_id),
            "collection_id": int(p.collection_id),
            "name_uz": p.name_uz,
            "name_ru": p.name_ru,
            "name_eng": p.name_eng,
            "description_uz": p.description_uz,
            "description_ru": p.description_ru,
            "description_eng": p.description_eng,
            "is_active": bool(p.is_active),
            "price": int(p.price),
            "item_ids": item_ids,
            "photo_ids": photo_ids,
            "detail_ids": detail_ids,
        }

    color_rows = await Color.all()
    size_rows = await Size.all()
    color_entities = {
        int(c.id): {
            "id": int(c.id),
            "name_uz": c.name_uz,
            "name_ru": c.name_ru,
            "name_eng": c.name_eng,
        }
        for c in color_rows
        if int(c.id) in colors
    }
    size_entities = {
        int(s.id): {
            "id": int(s.id),
            "name": s.name,
        }
        for s in size_rows
        if int(s.id) in sizes
    }

    return {
        "ok": True,
        "banners": await MainPhoto.all(),
        "entities": {
            "categories": categories,
            "collections": collections,
            "colors": color_entities,
            "sizes": size_entities,
            "products": products_entities,
            "product_items": product_items,
            "product_photos": product_photos,
            "product_details": product_details,
        },
        "result": {
            "product_ids": [int(p.id) for p in products],
        },
    }
