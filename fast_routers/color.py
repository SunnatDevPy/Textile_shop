from typing import Optional, Annotated, List

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import verify_admin_credentials
from models import AdminUser, Category, Collection, Color
from utils.base_models_pydantic import ProductList

color_router = APIRouter(prefix='/color', tags=['Color'])


class ListColorModel(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    name_eng: str
    products: Optional[List['ProductList']] = None


ListColorModel.model_rebuild()


class UpdateOrCreateColorModel(BaseModel):
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None
    name_eng: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            name_uz: Optional[str] = Form(None),
            name_ru: Optional[str] = Form(None),
            name_eng: Optional[str] = Form(None),
    ):
        return cls(name_uz=name_uz, name_ru=name_ru, name_eng=name_eng)


@color_router.get(path='/', name="Color")
async def list_color() -> list[ListColorModel]:
    return await Color.all()

@color_router.get(path='/', name="Collections Get One")
async def color_get_one(color_id: int):
    return await Color.get_or_none(color_id)

@color_router.post(path="/", name="Create Color")
async def create_color(
        _: Annotated[AdminUser, Depends(verify_admin_credentials)],
        payload: Annotated[UpdateOrCreateColorModel, Depends(UpdateOrCreateColorModel.as_form)]
):
    try:
        color = await Color.create(**payload.model_dump(exclude_none=True))
    except DBAPIError:
        return Response("Color yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
    return {"ok": True, "data": color}


# # Update Color
@color_router.patch(path='/{color_id}', name="Update Color")
async def list_color(
        color_id: int,
        _: Annotated[AdminUser, Depends(verify_admin_credentials)],
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


@color_router.delete(path='/{color_id}', name="Delete Color")
async def list_color(color_id: int, _: Annotated[AdminUser, Depends(verify_admin_credentials)]):
    color = await Color.get_or_none(color_id)
    if color:
        await Color.delete(color_id)
        return {"ok": True}
    else:
        return Response("Note found", status.HTTP_404_NOT_FOUND)
