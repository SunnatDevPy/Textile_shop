from typing import Optional, Annotated

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import require_admin
from models import AdminUser, Color

color_router = APIRouter(prefix='/color', tags=['Color'])


class ListColorModel(BaseModel):
    id: int
    color_code: str


class UpdateOrCreateColorModel(BaseModel):
    color_code: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            color_code: Optional[str] = Form(None),
    ):
        return cls(color_code=color_code)


@color_router.get(path='', name="Color", summary="Ranglar ro'yxati")
async def list_color():
    return await Color.all()

@color_router.get(path='/{color_id}', name="Collections Get One", summary="Bitta rangni olish")
async def color_get_one(color_id: int):
    color = await Color.get_or_none(color_id)
    if not color:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")
    return color

@color_router.post(path="", name="Create Color", summary="Rang yaratish (admin)")
async def create_color(
        _: Annotated[AdminUser, Depends(require_admin)],
        payload: Annotated[UpdateOrCreateColorModel, Depends(UpdateOrCreateColorModel.as_form)]
):
    try:
        color = await Color.create(**payload.model_dump(exclude_none=True))
    except DBAPIError:
        return Response("Color yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
    return {"ok": True, "data": color}


# # Update Color
@color_router.patch(path='/{color_id}', name="Update Color", summary="Rangni yangilash (admin)")
async def list_color(
        color_id: int,
        _: Annotated[AdminUser, Depends(require_admin)],
        payload: Annotated[
            UpdateOrCreateColorModel, Depends(UpdateOrCreateColorModel.as_form)]
):
    color = await Color.get_or_none(_id=color_id)
    if not color:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)  # только то, что реально пришло
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    await color.update_from_dict(data).save()
    return {"ok": True, "data": color}


@color_router.delete(path='/{color_id}', name="Delete Color", summary="Rangni o'chirish (admin)")
async def list_color(color_id: int, _: Annotated[AdminUser, Depends(require_admin)]):
    color = await Color.get_or_none(color_id)
    if color:
        await Color.delete(color_id)
        return {"ok": True}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")
