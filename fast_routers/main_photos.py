from typing import Annotated

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.params import Depends
from starlette import status

from fast_routers.admin_auth import verify_admin_credentials
from models import MainPhoto, AdminUser

main_photos_router = APIRouter(prefix='/banners', tags=['Banners'])


@main_photos_router.get(path="/", name="All banner photos")
async def list_banner_photos():
    photos = await MainPhoto.all()
    return {"photos": photos}


@main_photos_router.post("/", name="Create Photo")
async def create_banner_photo(
        user: Annotated[AdminUser, Depends(verify_admin_credentials)],
        photo: UploadFile = File(...),
):
    if user.status not in {"moderator", "admin", "superuser"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu userda xuquq yo'q")

    await MainPhoto.create(photo=photo)
    return {"ok": True}


@main_photos_router.delete(path='/{photo_id}', name="Delete Banner photo")
async def delete_banner_photo(
    user: Annotated[AdminUser, Depends(verify_admin_credentials)],
    photo_id: int,
):
    if user.status not in {"moderator", "admin", "superuser"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu userda xuquq yo'q")

    photo = await MainPhoto.get_or_none(photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bunday idli rasm yo'q")

    await MainPhoto.delete(photo_id)
    return {"ok": True}
