"""CRUD для ProductPhoto, ProductItems, ProductDetail."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import require_admin
from models import AdminUser, Color, Product, ProductDetail, ProductItems, ProductPhoto, Size
from models.database import db

AdminOnlyAuth = Annotated[AdminUser, Depends(require_admin)]


def _require_image_upload(photo: UploadFile) -> None:
    if photo.content_type and not str(photo.content_type).startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fayl rasm bo'lishi kerak",
        )


product_photo_router = APIRouter(prefix='/product-photos', tags=['Product photos'])
product_items_router = APIRouter(prefix='/product-items', tags=['Product items'])
product_detail_router = APIRouter(prefix='/product-details', tags=['Product details'])


# --- ProductPhoto ---


@product_photo_router.get('', name='List product photos', summary="Mahsulot rasmlari ro'yxati")
async def list_product_photos(product_id: Optional[int] = None):
    if product_id is None:
        return await ProductPhoto.all()
    q = select(ProductPhoto).where(ProductPhoto.product_id == product_id)
    return list((await db.execute(q)).scalars().all())


@product_photo_router.get('/{photo_id}', name='Get product photo', summary="Bitta mahsulot rasmini olish")
async def get_product_photo(photo_id: int):
    row = await ProductPhoto.get_or_none(photo_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Rasm topilmadi')
    return row


@product_photo_router.post('', name='Create product photo', summary="Mahsulot rasmi qo'shish (admin)")
async def create_product_photo(
    _: AdminOnlyAuth,
    product_id: int = Form(),
    photo: UploadFile = File(...),
):
    if await Product.get_or_none(product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    _require_image_upload(photo)
    try:
        row = await ProductPhoto.create(product_id=product_id, photo=photo)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Rasmni saqlashda xatolik',
        )
    return {'ok': True, 'id': row.id}


@product_photo_router.patch('/{photo_id}', name='Update product photo', summary="Mahsulot rasmini yangilash (admin)")
async def update_product_photo(
    photo_id: int,
    _: AdminOnlyAuth,
    product_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(default=None),
):
    row = await ProductPhoto.get_or_none(photo_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Rasm topilmadi')
    if product_id is not None and await Product.get_or_none(product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    if photo is not None:
        _require_image_upload(photo)

    data = {k: v for k, v in {'product_id': product_id, 'photo': photo}.items() if v is not None}
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O'zgartirish uchun ma'lumot yo'q")
    try:
        await ProductPhoto.update(photo_id, **data)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'zgartirishda xatolik",
        )
    return {'ok': True}


@product_photo_router.delete('/{photo_id}', name='Delete product photo', summary="Mahsulot rasmini o'chirish (admin)")
async def delete_product_photo(photo_id: int, _: AdminOnlyAuth):
    if await ProductPhoto.get_or_none(photo_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Rasm topilmadi')
    try:
        await ProductPhoto.delete(photo_id)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'chirishda xatolik",
        )
    return {'ok': True}


# --- ProductItems ---


@product_items_router.get('', name='List product items', summary="Barcha mahsulot variantlari ro'yxati")
async def list_product_items():
    return await ProductItems.all()


@product_items_router.get(
    '/product/{product_id}',
    name='List product items by product',
    summary="Bitta mahsulotga tegishli variantlar ro'yxati",
)
async def list_product_items_by_product(product_id: int):
    return await ProductItems.get_product_items(product_id)


@product_items_router.get('/{item_id}', name='Get product item', summary="Bitta mahsulot variantini olish")
async def get_product_item(item_id: int):
    row = await ProductItems.get_or_none(item_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item topilmadi')
    return row


@product_items_router.post('', name='Create product item', summary="Mahsulot varianti yaratish (admin)")
async def create_product_item(
    _: AdminOnlyAuth,
    product_id: int = Form(),
    color_id: int = Form(),
    size_id: int = Form(),
    total_count: int = Form(),
):
    if await Product.get_or_none(product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    if await Color.get_or_none(color_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Color topilmadi')
    if await Size.get_or_none(size_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Size topilmadi')
    try:
        row = await ProductItems.create(
            product_id=product_id,
            color_id=color_id,
            size_id=size_id,
            total_count=total_count,
        )
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Item yaratishda xatolik',
        )
    return {'ok': True, 'id': row.id}


@product_items_router.patch('/{item_id}', name='Update product item', summary="Mahsulot variantini yangilash (admin)")
async def update_product_item(
    item_id: int,
    _: AdminOnlyAuth,
    product_id: Optional[int] = Form(None),
    color_id: Optional[int] = Form(None),
    size_id: Optional[int] = Form(None),
    total_count: Optional[int] = Form(None),
):
    if await ProductItems.get_or_none(item_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item topilmadi')
    if product_id is not None and await Product.get_or_none(product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    if color_id is not None and await Color.get_or_none(color_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Color topilmadi')
    if size_id is not None and await Size.get_or_none(size_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Size topilmadi')

    data = {
        k: v
        for k, v in {
            'product_id': product_id,
            'color_id': color_id,
            'size_id': size_id,
            'total_count': total_count,
        }.items()
        if v is not None
    }
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O'zgartirish uchun ma'lumot yo'q")
    try:
        await ProductItems.update(item_id, **data)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'zgartirishda xatolik",
        )
    return {'ok': True}


@product_items_router.delete('/{item_id}', name='Delete product item', summary="Mahsulot variantini o'chirish (admin)")
async def delete_product_item(item_id: int, _: AdminOnlyAuth):
    if await ProductItems.get_or_none(item_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item topilmadi')
    try:
        await ProductItems.delete(item_id)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'chirishda xatolik",
        )
    return {'ok': True}


# --- ProductDetail ---


@product_detail_router.get('', name='List product details', summary="Barcha mahsulot tafsilotlari ro'yxati")
async def list_product_details():
    return await ProductDetail.all()


@product_detail_router.get(
    '/product/{product_id}',
    name='List product details by product',
    summary="Bitta mahsulotga tegishli tafsilotlar ro'yxati",
)
async def list_product_details_by_product(product_id: int):
    q = select(ProductDetail).where(ProductDetail.product_id == product_id)
    return list((await db.execute(q)).scalars().all())


@product_detail_router.get('/{detail_id}', name='Get product detail', summary="Bitta mahsulot tafsilotini olish")
async def get_product_detail_row(detail_id: int):
    row = await ProductDetail.get_or_none(detail_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Detail topilmadi')
    return row


@product_detail_router.post('', name='Create product detail', summary="Mahsulot tafsiloti yaratish (admin)")
async def create_product_detail(
    _: AdminOnlyAuth,
    product_id: int = Form(),
    name_uz: str = Form(),
    name_ru: str = Form(),
    name_eng: str = Form(),
):
    if await Product.get_or_none(product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')
    try:
        row = await ProductDetail.create(
            product_id=product_id,
            name_uz=name_uz,
            name_ru=name_ru,
            name_eng=name_eng,
        )
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Detail yaratishda xatolik',
        )
    return {'ok': True, 'id': row.id}


@product_detail_router.patch('/{detail_id}', name='Update product detail', summary="Mahsulot tafsilotini yangilash (admin)")
async def update_product_detail(
    detail_id: int,
    _: AdminOnlyAuth,
    product_id: Optional[int] = Form(None),
    name_uz: Optional[str] = Form(None),
    name_ru: Optional[str] = Form(None),
    name_eng: Optional[str] = Form(None),
):
    if await ProductDetail.get_or_none(detail_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Detail topilmadi')
    if product_id is not None and await Product.get_or_none(product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product topilmadi')

    data = {
        k: v
        for k, v in {
            'product_id': product_id,
            'name_uz': name_uz,
            'name_ru': name_ru,
            'name_eng': name_eng,
        }.items()
        if v is not None
    }
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O'zgartirish uchun ma'lumot yo'q")
    try:
        await ProductDetail.update(detail_id, **data)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'zgartirishda xatolik",
        )
    return {'ok': True}


@product_detail_router.delete('/{detail_id}', name='Delete product detail', summary="Mahsulot tafsilotini o'chirish (admin)")
async def delete_product_detail(detail_id: int, _: AdminOnlyAuth):
    if await ProductDetail.get_or_none(detail_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Detail topilmadi')
    try:
        await ProductDetail.delete(detail_id)
    except DBAPIError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O'chirishda xatolik",
        )
    return {'ok': True}
