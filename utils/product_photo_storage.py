"""Mahsulot rasmlarini saqlash, almashtirish va eski faylni o'chirish."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import select

from models import ProductPhoto
from models.database import db


def _product_photo_column_type():
    return ProductPhoto.__table__.columns.photo.type


def delete_stored_image(image_value) -> None:
    """Diskdagi eski rasm faylini o'chirish (yangilashda cache muammosini oldini oladi)."""
    if image_value is None:
        return
    try:
        if hasattr(image_value, "delete"):
            image_value.delete()
            return
    except OSError:
        pass
    except Exception:
        pass

    raw = None
    if hasattr(image_value, "name"):
        raw = image_value.name
    elif isinstance(image_value, str):
        raw = image_value
    if not raw:
        return

    try:
        path = Path("media") / str(raw).lstrip("/")
        if path.is_file():
            path.unlink()
    except OSError:
        pass


def stamp_upload_filename(upload: UploadFile, unique_key: str) -> None:
    """Bir xil nom bilan yuklansa ham yangi fayl nomi (cache bust)."""
    original = upload.filename or "image.jpg"
    stem = Path(original).stem or "image"
    ext = Path(original).suffix or ".jpg"
    upload.filename = f"{stem}_{unique_key}{ext}"


def save_product_photo_upload(
    upload: UploadFile,
    *,
    unique_key: Optional[str] = None,
) -> str:
    """Upload faylni siqib saqlaydi; `unique_key` URL/cache yangilanishi uchun."""
    if unique_key:
        stamp_upload_filename(upload, unique_key)
    col_type = _product_photo_column_type()
    return col_type.save(upload)


async def replace_product_photo_row(row: ProductPhoto, upload: UploadFile) -> None:
    """Mavjud `ProductPhoto` yozuvidagi rasmni to'liq almashtirish."""
    delete_stored_image(row.photo)
    saved = save_product_photo_upload(upload, unique_key=str(row.id))
    await ProductPhoto.update(row.id, photo=saved)


async def upsert_product_main_photo(product_id: int, upload: UploadFile) -> int:
    """Mahsulotning birinchi rasmini yangilaydi yoki yangi qo'shadi."""
    res = await db.execute(
        select(ProductPhoto)
        .where(ProductPhoto.product_id == product_id)
        .order_by(ProductPhoto.id.asc())
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if row is None:
        created = await ProductPhoto.create(product_id=product_id, photo=upload)
        return int(created.id)
    await replace_product_photo_row(row, upload)
    return int(row.id)
