from typing import Optional, Annotated

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import verify_admin_credentials
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


@size_router.get(path='/', name="Size")
async def list_size() -> list[ListSizeModel]:
    return await Size.all()


@size_router.get(path='/', name="Collections Get One")
async def size_get_one(size_id: int):
    return await Size.get_or_none(size_id)


@size_router.post(path="/", name="Create Size")
async def create_size(
        _: Annotated[AdminUser, Depends(verify_admin_credentials)],
        payload: Annotated[UpdateOrCreateSizeModel, Depends(UpdateOrCreateSizeModel.as_form)]
):
    try:
        size = await Size.create(**payload.model_dump(exclude_none=True))
    except DBAPIError:
        return Response("Size yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
    return {"ok": True, "data": size}


# # Update Size
@size_router.patch(path='/{size_id}', name="Update Size")
async def list_size(
        size_id: int,
        _: Annotated[AdminUser, Depends(verify_admin_credentials)],
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


@size_router.delete(path='/{size_id}', name="Delete Size")
async def list_size(size_id: int, _: Annotated[AdminUser, Depends(verify_admin_credentials)]):
    size = await Size.get_or_none(size_id)
    if size:
        await Size.delete(size_id)
        return {"ok": True}
    else:
        return Response("Note found", status.HTTP_404_NOT_FOUND)
