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
    products_all = await Product.all()
    products = products_all if include_inactive else [p for p in products_all if bool(getattr(p, "is_active", False))]
    product_ids_set = {int(p.id) for p in products}
    category_ids_set = {int(p.category_id) for p in products}
    collection_ids_set = {int(p.collection_id) for p in products}

    categories = [
        {
            "id": int(c.id),
            "name_uz": c.name_uz,
            "name_ru": c.name_ru,
            "name_eng": c.name_eng,
        }
        for c in await Category.all()
        if int(c.id) in category_ids_set
    ]
    collections = [
        {
            "id": int(c.id),
            "name_uz": c.name_uz,
            "name_ru": c.name_ru,
            "name_eng": c.name_eng,
        }
        for c in await Collection.all()
        if int(c.id) in collection_ids_set
    ]

    product_items = [
        {
            "id": int(i.id),
            "product_id": int(i.product_id),
            "color_id": int(i.color_id),
            "size_id": int(i.size_id),
            "total_count": int(i.total_count),
        }
        for i in await ProductItems.all()
        if int(i.product_id) in product_ids_set
    ]
    product_photos = [
        {
            "id": int(ph.id),
            "product_id": int(ph.product_id),
            "photo": str(getattr(ph, "photo", "")),
        }
        for ph in await ProductPhoto.all()
        if int(ph.product_id) in product_ids_set
    ]
    product_details = [
        {
            "id": int(d.id),
            "product_id": int(d.product_id),
            "name_uz": d.name_uz,
            "name_ru": d.name_ru,
            "name_eng": d.name_eng,
        }
        for d in await ProductDetail.all()
        if int(d.product_id) in product_ids_set
    ]
    products_payload = [
        {
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
            "clothing_type": str(getattr(p, "clothing_type", Product.ClothingType.MEN.value)),
            "price": int(p.price),
        }
        for p in products
    ]

    return {
        "ok": True,
        "banners": await MainPhoto.all(),
        "categories": categories,
        "collections": collections,
        "colors": await Color.all(),
        "sizes": await Size.all(),
        "products": products_payload,
        "product_items": product_items,
        "product_photos": product_photos,
        "product_details": product_details,
    }


@frontend_router.get(
    "/bootstrap/normalized",
    summary="Frontend uchun ma'lumotlar (normalized, duplicate kamroq)",
)
async def frontend_bootstrap_normalized(include_inactive: bool = False):
    products_all = await Product.all()
    products = products_all if include_inactive else [p for p in products_all if bool(getattr(p, "is_active", False))]

    categories_all = await Category.all()
    collections_all = await Collection.all()
    colors_all = await Color.all()
    sizes_all = await Size.all()
    items_all = await ProductItems.all()
    photos_all = await ProductPhoto.all()
    details_all = await ProductDetail.all()

    product_ids_set = {int(p.id) for p in products}
    category_ids_set = {int(p.category_id) for p in products}
    collection_ids_set = {int(p.collection_id) for p in products}

    items_by_product = {}
    used_color_ids = set()
    used_size_ids = set()
    product_items = {}
    for item in items_all:
        pid = int(item.product_id)
        if pid not in product_ids_set:
            continue
        iid = int(item.id)
        items_by_product.setdefault(pid, []).append(iid)
        used_color_ids.add(int(item.color_id))
        used_size_ids.add(int(item.size_id))
        product_items[iid] = {
            "id": iid,
            "product_id": pid,
            "color_id": int(item.color_id),
            "size_id": int(item.size_id),
            "total_count": int(item.total_count),
        }

    photos_by_product = {}
    product_photos = {}
    for ph in photos_all:
        pid = int(ph.product_id)
        if pid not in product_ids_set:
            continue
        phid = int(ph.id)
        photos_by_product.setdefault(pid, []).append(phid)
        product_photos[phid] = {
            "id": phid,
            "product_id": pid,
            "photo": str(getattr(ph, "photo", "")),
        }

    details_by_product = {}
    product_details = {}
    for d in details_all:
        pid = int(d.product_id)
        if pid not in product_ids_set:
            continue
        did = int(d.id)
        details_by_product.setdefault(pid, []).append(did)
        product_details[did] = {
            "id": did,
            "product_id": pid,
            "name_uz": d.name_uz,
            "name_ru": d.name_ru,
            "name_eng": d.name_eng,
        }

    categories = {
        int(c.id): {
            "id": int(c.id),
            "name_uz": c.name_uz,
            "name_ru": c.name_ru,
            "name_eng": c.name_eng,
        }
        for c in categories_all
        if int(c.id) in category_ids_set
    }
    collections = {
        int(c.id): {
            "id": int(c.id),
            "name_uz": c.name_uz,
            "name_ru": c.name_ru,
            "name_eng": c.name_eng,
        }
        for c in collections_all
        if int(c.id) in collection_ids_set
    }
    color_entities = {
        int(c.id): {
            "id": int(c.id),
            "color_code": c.color_code,
        }
        for c in colors_all
        if int(c.id) in used_color_ids
    }
    size_entities = {
        int(s.id): {
            "id": int(s.id),
            "name": s.name,
        }
        for s in sizes_all
        if int(s.id) in used_size_ids
    }

    products_entities = {
        int(p.id): {
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
            "clothing_type": str(getattr(p, "clothing_type", Product.ClothingType.MEN.value)),
            "price": int(p.price),
            "item_ids": items_by_product.get(int(p.id), []),
            "photo_ids": photos_by_product.get(int(p.id), []),
            "detail_ids": details_by_product.get(int(p.id), []),
        }
        for p in products
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
