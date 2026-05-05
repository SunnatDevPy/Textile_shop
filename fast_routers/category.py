from typing import Optional, Annotated, List

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.admin_auth import require_admin
from models import AdminUser, Category
from utils.base_models_pydantic import ProductList
from utils.cache import cached, cache

categories_router = APIRouter(prefix='/categories', tags=['Categories'])


class ListCategoryModel(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    name_eng: str
    products: Optional[List['ProductList']] = None


class UpdateOrCreateCategoryModel(BaseModel):
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


@categories_router.get(path='', name="Categories", summary="Kategoriyalar ro'yxati")
@cached(ttl=600, key_prefix="categories")
async def list_category():
    """Kategoriyalar ro'yxati (10 daqiqa cache)."""
    return await Category.all()

@categories_router.get(path='/{category_id}', name="Categories Get One", summary="Bitta kategoriyani olish")
async def category_get_one(category_id: int):
    category = await Category.get_or_none(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@categories_router.post(path="", name="Create Category", summary="Kategoriya yaratish (admin)")
async def create_category(
        _: Annotated[AdminUser, Depends(require_admin)],
        payload: Annotated[UpdateOrCreateCategoryModel, Depends(UpdateOrCreateCategoryModel.as_form)]
):
    try:
        category = await Category.create(**payload.model_dump(exclude_none=True))
        # Invalidate cache after creating
        cache.invalidate_pattern("categories")
    except DBAPIError:
        return Response("Category yaratishda xatolik", status_code=status.HTTP_404_NOT_FOUND)
    return {"ok": True, "data": category}


# # Update Category
@categories_router.patch(path='/{category_id}', name="Update Category", summary="Kategoriyani yangilash (admin)")
async def list_category_shop(
        category_id: int,
        _: Annotated[AdminUser, Depends(require_admin)],
        payload: Annotated[
            UpdateOrCreateCategoryModel, Depends(UpdateOrCreateCategoryModel.as_form)]
):
    category = await Category.get_or_none(_id=category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    await category.update_from_dict(data).save()
    # Invalidate cache after updating
    cache.invalidate_pattern("categories")
    return {"ok": True, "data": category}


@categories_router.delete(path='/{category_id}', name="Delete Category", summary="Kategoriyani o'chirish (admin)")
async def list_category_shop(category_id: int, _: Annotated[AdminUser, Depends(require_admin)]):
    category = await Category.get_or_none(category_id)
    if category:
        await Category.delete(category_id)
        # Invalidate cache after deleting
        cache.invalidate_pattern("categories")
        return {"ok": True}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
