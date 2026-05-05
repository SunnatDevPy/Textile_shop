import csv
import io
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import require_admin
from models import AdminUser, Category, Collection, Product, ProductPhoto
from models.database import db
from utils.response import ok_response

shop_product_router = APIRouter(prefix='/products', tags=['Products'])

AdminOnlyAuth = Annotated[AdminUser, Depends(require_admin)]

PRODUCT_SORT_FIELDS = {
    "id": Product.id,
    "name_uz": Product.name_uz,
    "price": Product.price,
    "is_active": Product.is_active,
    "clothing_type": Product.clothing_type,
}


def _require_image_upload(photo: UploadFile) -> None:
    if photo.content_type and not str(photo.content_type).startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fayl rasm bo'lishi kerak",
        )


@shop_product_router.get('', name='Get all products', summary="Barcha mahsulotlar ro'yxati")
async def get_all_products(include_inactive: bool = False, limit: int = 100):
    """
    Barcha mahsulotlar ro'yxati (default: faqat faol mahsulotlar).
    Limit: max 500 ta mahsulot.
    """
    limit = max(1, min(limit, 500))
    query = select(Product).limit(limit)
    if not include_inactive:
        query = query.where(Product.is_active == True)
    products = (await db.execute(query)).scalars().all()
    return products


@shop_product_router.get('/search', name='Search products', summary="Mahsulot qidirish (nom/kategoriya)")
async def search_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    include_inactive: bool = False,
    limit: int = 100,
):
    """
    Mahsulotlarni qidirish. Limit: max 500.
    """
    limit = max(1, min(limit, 500))
    query = select(Product).limit(limit)

    criteria = []
    if search:
        s = f"%{search}%"
        criteria.append((Product.name_uz.ilike(s)) | (Product.name_ru.ilike(s)) | (Product.name_eng.ilike(s)))
    if category_id is not None:
        criteria.append(Product.category_id == category_id)
    if not include_inactive:
        criteria.append(Product.is_active == True)

    if criteria:
        query = query.where(and_(*criteria))

    products = (await db.execute(query)).scalars().all()
    return ok_response(products, meta={"count": len(products)})


@shop_product_router.get('/search/advanced', name='Advanced product search', summary="Mahsulotlarni kengaytirilgan filter bilan qidirish")
async def search_products_advanced(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    collection_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    clothing_type: Optional[str] = None,
    color_id: Optional[int] = None,
    size_id: Optional[int] = None,
    in_stock: Optional[bool] = None,
    sort_by: str = "id",
    sort_dir: str = "desc",
    limit: int = 100,
):
    """
    Kengaytirilgan qidiruv:
    - search: mahsulot nomi (uz/ru/eng)
    - category_id, collection_id: kategoriya/kolleksiya
    - min_price, max_price: narx oralig'i
    - clothing_type: erkak/ayol/unisex
    - color_id, size_id: rang va o'lcham
    - in_stock: faqat omborda bor mahsulotlar
    - sort_by: id, name_uz, price, created_at
    - sort_dir: asc, desc
    """
    from models import ProductItems
    from sqlalchemy.orm import joinedload

    query = select(Product).options(joinedload(Product.product_items))
    criteria = []

    if search:
        s = f"%{search}%"
        criteria.append(
            (Product.name_uz.ilike(s)) | (Product.name_ru.ilike(s)) | (Product.name_eng.ilike(s))
        )
    if category_id is not None:
        criteria.append(Product.category_id == category_id)
    if collection_id is not None:
        criteria.append(Product.collection_id == collection_id)
    if is_active is not None:
        criteria.append(Product.is_active == is_active)
    if min_price is not None:
        criteria.append(Product.price >= min_price)
    if max_price is not None:
        criteria.append(Product.price <= max_price)
    if clothing_type is not None:
        criteria.append(Product.clothing_type == clothing_type)

    # Rang va o'lcham bo'yicha filter
    if color_id is not None or size_id is not None or in_stock is not None:
        subquery = select(ProductItems.product_id).distinct()
        item_criteria = []
        if color_id is not None:
            item_criteria.append(ProductItems.color_id == color_id)
        if size_id is not None:
            item_criteria.append(ProductItems.size_id == size_id)
        if in_stock:
            item_criteria.append(ProductItems.total_count > 0)
        if item_criteria:
            subquery = subquery.where(and_(*item_criteria))
        criteria.append(Product.id.in_(subquery))

    if criteria:
        query = query.where(and_(*criteria))

    # Sorting
    sort_fields = {
        "id": Product.id,
        "name_uz": Product.name_uz,
        "price": Product.price,
        "created_at": Product.created_at,
    }
    sort_col = sort_fields.get(sort_by, Product.id)
    if sort_dir.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    query = query.limit(max(1, min(limit, 500)))
    products = (await db.execute(query)).scalars().unique().all()

    return ok_response(products, meta={"count": len(products), "sort_by": sort_by, "sort_dir": sort_dir})


@shop_product_router.get('/category/{category_id}', name='Products by category', summary="Kategoriya bo'yicha mahsulotlar")
async def list_products_by_category(category_id: int, include_inactive: bool = False, limit: int = 100):
    """
    Kategoriya bo'yicha mahsulotlar. Limit: max 500.
    """
    limit = max(1, min(limit, 500))
    query = select(Product).where(Product.category_id == category_id).limit(limit)
    if not include_inactive:
        query = query.where(Product.is_active == True)
    products = (await db.execute(query)).scalars().all()
    return products


@shop_product_router.get('/{product_id}', name='Get product', summary="Bitta mahsulotni olish")
async def get_product(product_id: int):
    product = await Product.get_or_none(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    return {'product': product}


@shop_product_router.get('/admin-table', summary="Mahsulotlar admin jadvali: pagination + sort + filter")
async def products_admin_table(
    _: AdminOnlyAuth,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "id",
    sort_dir: str = "desc",
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    collection_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    clothing_type: Optional[str] = None,
):
    page = max(1, int(page))
    page_size = max(1, min(int(page_size), 200))
    sort_col = PRODUCT_SORT_FIELDS.get(sort_by, Product.id)
    sort_expr = desc(sort_col) if str(sort_dir).lower() == "desc" else asc(sort_col)

    criteria = []
    if search:
        s = f"%{search}%"
        criteria.append((Product.name_uz.ilike(s)) | (Product.name_ru.ilike(s)) | (Product.name_eng.ilike(s)))
    if category_id is not None:
        criteria.append(Product.category_id == category_id)
    if collection_id is not None:
        criteria.append(Product.collection_id == collection_id)
    if is_active is not None:
        criteria.append(Product.is_active == is_active)
    if min_price is not None:
        criteria.append(Product.price >= min_price)
    if max_price is not None:
        criteria.append(Product.price <= max_price)
    if clothing_type is not None:
        criteria.append(Product.clothing_type == clothing_type)

    where_clause = and_(*criteria) if criteria else None
    count_q = select(func.count(Product.id))
    data_q = select(Product).order_by(sort_expr).offset((page - 1) * page_size).limit(page_size)
    if where_clause is not None:
        count_q = count_q.where(where_clause)
        data_q = data_q.where(where_clause)

    total = int((await db.execute(count_q)).scalar() or 0)
    rows = (await db.execute(data_q)).scalars().all()
    total_pages = (total + page_size - 1) // page_size if total else 0

    chips = []
    for key, value in {
        "search": search,
        "category_id": category_id,
        "collection_id": collection_id,
        "is_active": is_active,
        "min_price": min_price,
        "max_price": max_price,
        "clothing_type": clothing_type,
    }.items():
        if value not in (None, ""):
            chips.append({"key": key, "value": str(value)})

    return ok_response(
        rows,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "sort_by": sort_by,
            "sort_dir": sort_dir.lower(),
            "chips": chips,
        },
    )


@shop_product_router.get('/admin-table/export.csv', summary="Mahsulotlar admin jadvali CSV export")
async def products_admin_table_export(
    _: AdminOnlyAuth,
    sort_by: str = "id",
    sort_dir: str = "desc",
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    collection_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    clothing_type: Optional[str] = None,
):
    sort_col = PRODUCT_SORT_FIELDS.get(sort_by, Product.id)
    sort_expr = desc(sort_col) if str(sort_dir).lower() == "desc" else asc(sort_col)

    criteria = []
    if search:
        s = f"%{search}%"
        criteria.append((Product.name_uz.ilike(s)) | (Product.name_ru.ilike(s)) | (Product.name_eng.ilike(s)))
    if category_id is not None:
        criteria.append(Product.category_id == category_id)
    if collection_id is not None:
        criteria.append(Product.collection_id == collection_id)
    if is_active is not None:
        criteria.append(Product.is_active == is_active)
    if min_price is not None:
        criteria.append(Product.price >= min_price)
    if max_price is not None:
        criteria.append(Product.price <= max_price)
    if clothing_type is not None:
        criteria.append(Product.clothing_type == clothing_type)

    query = select(Product).order_by(sort_expr).limit(10000)
    if criteria:
        query = query.where(and_(*criteria))
    rows = (await db.execute(query)).scalars().all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "created_at", "name_uz", "category_id", "collection_id", "price", "clothing_type", "is_active"]
    )
    for p in rows:
        writer.writerow(
            [
                p.id,
                getattr(p, "created_at", None),
                getattr(p, "name_uz", ""),
                getattr(p, "category_id", ""),
                getattr(p, "collection_id", ""),
                getattr(p, "price", 0),
                getattr(p, "clothing_type", ""),
                getattr(p, "is_active", False),
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="products_export.csv"'},
    )


@shop_product_router.post('', name='Create product', summary="Mahsulot yaratish (admin)")
async def create_product(
    _: AdminOnlyAuth,
    category_id: int = Form(),
    collection_id: int = Form(),
    name_uz: str = Form(),
    name_ru: str = Form(),
    name_eng: str = Form(),
    description_uz: str = Form(),
    description_ru: str = Form(),
    description_eng: str = Form(),
    price: int = Form(),
    is_active: bool = Form(True),
    clothing_type: str = Form(Product.ClothingType.MEN.value),
    photo: Optional[UploadFile] = File(default=None),
):
    category = await Category.get_or_none(category_id)
    collection = await Collection.get_or_none(collection_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category topilmadi')
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Collection topilmadi')
    if photo is not None:
        _require_image_upload(photo)
    allowed_clothing_types = {Product.ClothingType.MEN.value, Product.ClothingType.WOMEN.value}
    if clothing_type not in allowed_clothing_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"clothing_type faqat: {', '.join(sorted(allowed_clothing_types))}",
        )

    try:
        product = await Product.create(
            category_id=category_id,
            collection_id=collection_id,
            name_uz=name_uz,
            name_ru=name_ru,
            name_eng=name_eng,
            description_uz=description_uz,
            description_ru=description_ru,
            description_eng=description_eng,
            price=price,
            is_active=is_active,
            clothing_type=clothing_type,
        )
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mahsulot yaratishda xatolik",
        )

    if photo is not None:
        try:
            await ProductPhoto.create(product_id=product.id, photo=photo)
        except DBAPIError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rasmni saqlashda xatolik",
            )

    return {'ok': True, 'id': product.id}


@shop_product_router.patch('/{product_id}', name='Update product', summary="Mahsulotni yangilash (admin)")
async def update_product(
    product_id: int,
    _: AdminOnlyAuth,
    category_id: Optional[int] = Form(None),
    collection_id: Optional[int] = Form(None),
    name_uz: Optional[str] = Form(None),
    name_ru: Optional[str] = Form(None),
    name_eng: Optional[str] = Form(None),
    description_uz: Optional[str] = Form(None),
    description_ru: Optional[str] = Form(None),
    description_eng: Optional[str] = Form(None),
    price: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    clothing_type: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(default=None),
):
    product = await Product.get_or_none(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')

    if category_id is not None:
        if await Category.get_or_none(category_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category topilmadi')
    if collection_id is not None:
        if await Collection.get_or_none(collection_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Collection topilmadi')

    if photo is not None:
        _require_image_upload(photo)
    if clothing_type is not None:
        allowed_clothing_types = {Product.ClothingType.MEN.value, Product.ClothingType.WOMEN.value}
        if clothing_type not in allowed_clothing_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"clothing_type faqat: {', '.join(sorted(allowed_clothing_types))}",
            )

    update_data = {
        k: v
        for k, v in {
            'category_id': category_id,
            'collection_id': collection_id,
            'name_uz': name_uz,
            'name_ru': name_ru,
            'name_eng': name_eng,
            'description_uz': description_uz,
            'description_ru': description_ru,
            'description_eng': description_eng,
            'price': price,
            'is_active': is_active,
            'clothing_type': clothing_type,
        }.items()
        if v is not None
    }

    try:
        if update_data:
            await Product.update(product_id, **update_data)
        if photo is not None:
            await ProductPhoto.create(product_id=product_id, photo=photo)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'zgartirishda xatolik",
        )

    if not update_data and photo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O'zgartirish uchun ma'lumot yo'q",
        )

    return {'ok': True}


@shop_product_router.delete('/{product_id}', name='Delete product', summary="Mahsulotni o'chirish (admin)")
async def delete_product(product_id: int, _: AdminOnlyAuth):
    product = await Product.get_or_none(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    try:
        await Product.delete(product_id)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'chirishda xatolik",
        )
    return {'ok': True}
