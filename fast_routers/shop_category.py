from typing import Optional, Annotated

from fastapi import APIRouter, Form, UploadFile, File
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status
import pandas as pd
from models import AdminPanelUser, ShopCategory, Shop
from fast_routers.jwt_ import get_current_user

shop_category_router = APIRouter(prefix='/shop-categories', tags=['Shop Categories'])


class UserId(BaseModel):
    id: int


@shop_category_router.get(path='', name="Categories")
async def list_category_shop():
    categories = await ShopCategory.all()
    return categories


@shop_category_router.get(path='/from-shop', name="List from Shop")
async def list_category_shop(shop_id: int):
    shop = await Shop.get(shop_id)
    if shop:
        category = await ShopCategory.get_shop_categories(shop_id)
        return category
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


# @shop_category_router.post(path='/save-excel', name="Create Excel file Category")
# async def list_category_shop(user_id: int, file: UploadFile = File(...)):
#     user = await AdminPanelUser.get(user_id)
#     if user:
#         if not file.filename.endswith(".xlsx"):
#             return {"error": "Fayl faqat xlsx formatda bo'lish kerak"}
#     else:
#         return Response("User topilmadi", status.HTTP_404_NOT_FOUND)


@shop_category_router.post(path='', name="Create Category")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)],
                             shop_id: int = Form(),
                             name_uz: str = Form(),
                             name_ru: str = Form(),
                             parent_id: int = Form(default=None),
                             photo: UploadFile = File()
                             ):
    seller: AdminPanelUser = await AdminPanelUser.get(user.id)
    shop = await Shop.get(shop_id)
    if seller and shop:
        if seller.id == shop.owner_id or seller.status in ['moderator', "admin", "superuser"]:
            if parent_id == 0:
                parent_id = None
            try:
                category = await ShopCategory.create(name_uz=name_uz, name_ru=name_ru, shop_id=shop_id,
                                                     parent_id=parent_id,
                                                     photo=photo, is_active=True)
            except DBAPIError as e:
                print(e)
                return Response("Category yaratishda xatolik", status.HTTP_404_NOT_FOUND)
            return {"ok": True, "data": category}
        else:
            return Response("Bu userda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


# # Update Category
@shop_category_router.patch(path='/detail', name="Update Category")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)],
                             category_id: int,
                             name_uz: str = Form(),
                             name_ru: str = Form(),
                             parent_id: int = Form(default=None),
                             is_active: bool = Form(default=None),
                             photo: UploadFile = File(default=None),
                             ):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    if parent_id == 0:
        parent_id = None
    if photo:
        if not photo.content_type.startswith("image/"):
            return Response("fayl rasim bo'lishi kerak", status.HTTP_404_NOT_FOUND)
    if user:
        update_data = {k: v for k, v in
                       {"name_uz": name_uz, "name_ru": name_ru, "parent_id": parent_id, "is_active": is_active,
                        "photo": photo}.items() if
                       v is not None}
        if user.status in ['moderator', "admin", "superuser"]:
            shop = await ShopCategory.get(category_id)
            if shop:
                if update_data:
                    try:
                        await ShopCategory.update(category_id, **update_data)
                        return {"ok": True}
                    except DBAPIError as e:
                        print(e)
                        return Response("O'zgarishta xatolik", status.HTTP_404_NOT_FOUND)
                else:
                    return Response("O'zgarish uchun malumot yoq", status.HTTP_404_NOT_FOUND)
            else:
                return Response("Bunday sho'p id yo'q", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Bu userda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


@shop_category_router.delete(path='', name="Delete Category")
async def list_category_shop(category_id: int, user: Annotated[UserId, Depends(get_current_user)]):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    if user:
        if user.status in ['moderator', "admin", "superuser"]:
            category = await ShopCategory.get(category_id)
            if category:
                await ShopCategory.delete(category_id)
                return {"ok": True}
            else:
                return Response("Bunday sho'p id yo'q", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Bu userda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
