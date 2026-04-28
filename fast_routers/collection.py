from typing import Optional, Annotated, List

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import verify_admin_credentials
from models import AdminUser, Category, Collection
from utils.base_models_pydantic import ProductList

collections_router = APIRouter(prefix='/collections', tags=['Collections'])


class ListCollectionModel(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    name_eng: str
    products: Optional[List['ProductList']] = None


ListCollectionModel.model_rebuild()


class UpdateOrCreateCollectionModel(BaseModel):
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


@collections_router.get(path='/', name="Collections")
async def list_collection() -> list[ListCollectionModel]:
    return await Collection.all()

@collections_router.get(path='/', name="Collections Get One")
async def collection_get_one(collection_id: int):
    return await Collection.get_or_none(collection_id)

@collections_router.post(path="/", name="Create Collections")
async def create_collection(
        _: Annotated[AdminUser, Depends(verify_admin_credentials)],
        payload: Annotated[UpdateOrCreateCollectionModel, Depends(UpdateOrCreateCollectionModel.as_form)]
):
    try:
        collection = await Collection.create(**payload.model_dump(exclude_none=True))
    except DBAPIError:
        return Response("Color yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
    return {"ok": True, "data": collection}


# # Update Collection
@collections_router.patch(path='/{collection_id}', name="Update Collections")
async def list_collection(
        collection_id: int,
        _: Annotated[AdminUser, Depends(verify_admin_credentials)],
        payload: Annotated[
            UpdateOrCreateCollectionModel, Depends(UpdateOrCreateCollectionModel.as_form)]
):
    collection = await Collection.get_or_none(_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)  # только то, что реально пришло
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    await collection.update_from_dict(data).save()
    return {"ok": True, "data": collection}


@collections_router.delete(path='/{collection_id}', name="Delete Collections")
async def list_collection(collection_id: int, _: Annotated[AdminUser, Depends(verify_admin_credentials)]):
    collection = await Collection.get_or_none(collection_id)
    if collection:
        await Collection.delete(collection_id)
        return {"ok": True}
    else:
        return Response("Note found", status.HTTP_404_NOT_FOUND)
