from typing import Annotated

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.params import Depends
from starlette import status

from fast_routers.admin_auth import require_admin
from models import AdminUser, MainPhoto

main_photos_router = APIRouter(prefix='/banners', tags=['Banners'])
AdminOnlyAuth = Annotated[AdminUser, Depends(require_admin)]


@main_photos_router.get(path="/", name="All banner photos", summary="Bannerlar ro'yxati")
async def list_banner_photos():
    photos = await MainPhoto.all()
    return {"photos": photos}


@main_photos_router.post("/", name="Create Photo", summary="Banner rasmi qo'shish (admin)")
async def create_banner_photo(
        _: AdminOnlyAuth,
        photo: UploadFile = File(...),
):
    await MainPhoto.create(photo=photo)
    return {"ok": True}


@main_photos_router.delete(path='/{photo_id}', name="Delete Banner photo", summary="Banner rasmini o'chirish (admin)")
async def delete_banner_photo(
    _: AdminOnlyAuth,
    photo_id: int,
):
    photo = await MainPhoto.get_or_none(photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bunday idli rasm yo'q")

    await MainPhoto.delete(photo_id)
    return {"ok": True}
