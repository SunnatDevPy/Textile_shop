from typing import Annotated

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from models import MainPhoto, AdminPanelUser, MainVideo
from fast_routers.jwt_ import get_current_user

main_photos_router = APIRouter(prefix='/banners', tags=['Banners'])


class UserId(BaseModel):
    id: int


@main_photos_router.get(path="-photo", name="All banner photos")
async def list_banner_photos():
    try:
        photos = await MainPhoto.all()
        if not photos:
            raise HTTPException(status_code=404, detail="No banner photos found")
        return {"photos": photos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")




@main_photos_router.get(path='-video', name="All banner videos")
async def list_category_shop():
    photos = await MainVideo.all()
    return {'photos': photos}


@main_photos_router.post("-photo", name="Create Photo")
async def list_category_shop(
        user: Annotated[UserId, Depends(get_current_user)],
        language: str = Form(...),
        photo: UploadFile = File(None),
):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)

    if user:
        if user.status in ["moderator", "admin", "superuser"]:
            try:
                await MainPhoto.create(photo=photo, language=language)
                return {"ok": True}
            except DBAPIError:
                return Response("Yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return Response("Bu userda xuquq yo'q", status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response("User yo'q", status_code=status.HTTP_404_NOT_FOUND)


@main_photos_router.post("-video", name="Create Video ")
async def list_category_shop(
        user: Annotated[UserId, Depends(get_current_user)],
        language: str = Form(...),
        video: UploadFile = File(None),
):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)

    if user:
        if user.status in ["moderator", "admin", "superuser"]:
            try:
                await MainVideo.create(language=language, video=video)
                return {"ok": True}
            except DBAPIError:
                return Response("Yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return Response("Bu userda xuquq yo'q", status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response("User yo'q", status_code=status.HTTP_404_NOT_FOUND)


@main_photos_router.delete(path='-photo', name="Delete Banner photo")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], photo_id: int = Form()):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    if user:
        if user.status in ['moderator', "admin", "superuser"]:
            if await MainPhoto.get(photo_id):
                await MainPhoto.delete(photo_id)
                return {"ok": True}
            else:
                return Response("Bunday idli rasim yo'q", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Bu userda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("User yo'q", status.HTTP_404_NOT_FOUND)


@main_photos_router.delete(path='-video', name="Delete Banner Video")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], video_id: int = Form()):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    if user:
        if user.status in ['moderator', "admin", "superuser"]:
            if await MainVideo.get(video_id):
                await MainVideo.delete(video_id)
                return {"ok": True}
            else:
                return Response("Bunday idli rasim yo'q", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Bu userda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("User yo'q", status.HTTP_404_NOT_FOUND)
