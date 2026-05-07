from typing import Optional, Annotated, List

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import require_admin
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


def _serialize_collection(collection: Collection) -> dict:
    return {
        "id": collection.id,
        "name_uz": collection.name_uz,
        "name_ru": collection.name_ru,
        "name_eng": collection.name_eng,
    }


@collections_router.get(path='', name="Collections", summary="Kolleksiyalar ro'yxati")
async def list_collection():
    collections = await Collection.all()
    return [_serialize_collection(collection) for collection in collections]

@collections_router.get(path='/{collection_id}', name="Collections Get One", summary="Bitta kolleksiyani olish")
async def collection_get_one(collection_id: int):
    collection = await Collection.get_or_none(collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return _serialize_collection(collection)

@collections_router.post(path="", name="Create Collections", summary="Kolleksiya yaratish (admin)")
async def create_collection(
        _: Annotated[AdminUser, Depends(require_admin)],
        payload: Annotated[UpdateOrCreateCollectionModel, Depends(UpdateOrCreateCollectionModel.as_form)]
):
    try:
        collection = await Collection.create(**payload.model_dump(exclude_none=True))
    except DBAPIError:
        return Response("Color yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
    return {"ok": True, "data": _serialize_collection(collection)}


# # Update Collection
@collections_router.patch(path='/{collection_id}', name="Update Collections", summary="Kolleksiyani yangilash (admin)")
async def list_collection(
        collection_id: int,
        _: Annotated[AdminUser, Depends(require_admin)],
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
    return {"ok": True, "data": _serialize_collection(collection)}


@collections_router.delete(path='/{collection_id}', name="Delete Collections", summary="Kolleksiyani o'chirish (admin)")
async def list_collection(collection_id: int, _: Annotated[AdminUser, Depends(require_admin)]):
    collection = await Collection.get_or_none(collection_id)
    if collection:
        await Collection.delete(collection_id)
        return {"ok": True}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
