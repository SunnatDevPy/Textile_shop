from typing import Optional, Annotated

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import require_admin
from models import AdminUser, Size

size_router = APIRouter(prefix='/size', tags=['Size'])


class ListSizeModel(BaseModel):
    id: int
    name: str


class UpdateOrCreateSizeModel(BaseModel):
    name: str

    @classmethod
    def as_form(
            cls,
            name: Optional[str] = Form(None)
    ):
        return cls(name=name)


@size_router.get(path='/', name="Size", summary="O'lchamlar ro'yxati")
async def list_size() -> list[ListSizeModel]:
    return await Size.all()


@size_router.get(path='/{size_id}', name="Collections Get One", summary="Bitta o'lchamni olish")
async def size_get_one(size_id: int):
    size_row = await Size.get_or_none(size_id)
    if not size_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size not found")
    return size_row


@size_router.post(path="/", name="Create Size", summary="O'lcham yaratish (admin)")
async def create_size(
        _: Annotated[AdminUser, Depends(require_admin)],
        payload: Annotated[UpdateOrCreateSizeModel, Depends(UpdateOrCreateSizeModel.as_form)]
):
    try:
        size = await Size.create(**payload.model_dump(exclude_none=True))
    except DBAPIError:
        return Response("Size yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
    return {"ok": True, "data": size}


# # Update Size
@size_router.patch(path='/{size_id}', name="Update Size", summary="O'lchamni yangilash (admin)")
async def list_size(
        size_id: int,
        _: Annotated[AdminUser, Depends(require_admin)],
        payload: Annotated[
            UpdateOrCreateSizeModel, Depends(UpdateOrCreateSizeModel.as_form)]
):
    size = await Size.get_or_none(_id=size_id)
    if not size:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size not found")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)  # только то, что реально пришло
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    await size.update_from_dict(data).save()
    return {"ok": True, "data": size}


@size_router.delete(path='/{size_id}', name="Delete Size", summary="O'lchamni o'chirish (admin)")
async def list_size(size_id: int, _: Annotated[AdminUser, Depends(require_admin)]):
    size = await Size.get_or_none(size_id)
    if size:
        await Size.delete(size_id)
        return {"ok": True}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size not found")
