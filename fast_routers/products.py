from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import and_, select
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import require_admin
from models import AdminUser, Category, Collection, Product, ProductPhoto
from models.database import db
from utils.response import ok_response

shop_product_router = APIRouter(prefix='/products', tags=['Products'])

AdminOnlyAuth = Annotated[AdminUser, Depends(require_admin)]


def _require_image_upload(photo: UploadFile) -> None:
    if photo.content_type and not str(photo.content_type).startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fayl rasm bo'lishi kerak",
        )


@shop_product_router.get('', name='Get all products', summary="Barcha mahsulotlar ro'yxati")
async def get_all_products():
    return await Product.all()


@shop_product_router.get('/search', name='Search products', summary="Mahsulot qidirish (nom/kategoriya)")
async def search_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
):
    if search:
        products = await Product.search(search, category_id)
    elif category_id is not None:
        products = await Product.get_products_category(category_id)
    else:
        products = await Product.all()
    return ok_response(products, meta={"count": len(products)})


@shop_product_router.get(
    '/search/advanced',
    name='Advanced product search',
    summary="Mahsulotlarni kengaytirilgan filter bilan qidirish",
)
async def search_products_advanced(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    collection_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    limit: int = 100,
):
    query = select(Product)
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
    if criteria:
        query = query.where(and_(*criteria))

    query = query.limit(max(1, min(limit, 500)))
    products = (await db.execute(query)).scalars().all()
    return ok_response(products, meta={"count": len(products)})


@shop_product_router.get('/category/{category_id}', name='Products by category', summary="Kategoriya bo'yicha mahsulotlar")
async def list_products_by_category(category_id: int):
    return await Product.get_products_category(category_id)


@shop_product_router.get('/{product_id}', name='Get product', summary="Bitta mahsulotni olish")
async def get_product(product_id: int):
    product = await Product.get_or_none(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    return {'product': product}


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
