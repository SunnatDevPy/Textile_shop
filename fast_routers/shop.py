from typing import Annotated

from fastapi import APIRouter, File, UploadFile, Form
from fastapi import Response
from fastapi.params import Depends
from geopy import Nominatim
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.jwt_ import get_current_user
from models import AdminPanelUser, Shop
from utils import ListShopsModel
from utils.base_models_pydantic import ListShopsModelAll

shop_router = APIRouter(prefix='/shop', tags=['Shop'])

geolocator = Nominatim(user_agent="Backend")


class UserId(BaseModel):
    user_id: int


@shop_router.get(path='', name="Shops")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)]) -> list[ListShopsModel]:
    return await Shop.all()


@shop_router.get(path='/detail', name="Get Shop")
async def list_category_shop(shop_id: int, user: Annotated[UserId, Depends(get_current_user)]) -> list[
    ListShopsModelAll]:
    return await Shop.get(shop_id)


@shop_router.get(path='/all', name="Get Shop")
async def list_category_shop() -> list[ListShopsModelAll]:
    return await Shop.all()


@shop_router.post(path='', name="Create Shop")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)],
                             name_uz: str = Form(),
                             name_ru: str = Form(),
                             lat: float = Form(),
                             address: str = Form(None),
                             long: float = Form(),
                             is_active: bool = Form(default=True),
                             order_group_id: int = Form(),
                             cart_number: int = Form(),
                             photo: UploadFile = File()):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    if user:
        if long and lat and address == None:
            location = geolocator.reverse(f"{lat}, {long}")
            address = location.raw['address']
            name = f"{address['county']}, {address['neighbourhood']}, {address['road']}"
        else:
            name = address
        if user.status in ['moderator', "admin", "superuser"]:
            shop = await Shop.create(owner_id=user.id, name_uz=name_uz, name_ru=name_ru,
                                     address=name, lat=lat, long=long,
                                     photo=photo, is_active=is_active,
                                     order_group_id=order_group_id, cart_number=cart_number)
            return {"ok": True, "shop": shop}
        else:
            return Response("Bu userda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


# Update Shop
@shop_router.patch(path='/detail', name="Update Shop")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)],
                             shop_id: int,
                             name_uz: str = Form(default=None),
                             name_ru: str = Form(None),
                             address: str = Form(None),
                             lat: float = Form(None),
                             long: float = Form(None),
                             order_group_id: int = Form(None),
                             cart_number: int = Form(None),
                             is_active: bool = Form(None),
                             photo: UploadFile = File(None)
                             ):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    shop: Shop = await Shop.get(shop_id)
    if user and shop:
        if photo:
            if not photo.content_type.startswith("image/"):
                return Response("fayl rasim bo'lishi kerak", status.HTTP_404_NOT_FOUND)
        if long and lat and address == None:
            location = geolocator.reverse(f"{lat}, {long}")
            address = location.raw['address']
            name = f"{address['county']}, {address['neighbourhood']}, {address['road']}"
        else:
            name = address
        update_data = {k: v for k, v in {
            "name_uz": name_uz,
            "name_ru": name_ru,
            "address": name,
            "lat": lat,
            "long": long,
            "is_active": is_active,
            "order_group_id": order_group_id,
            "cart_number": cart_number}.items() if v is not None}
        if user.status in ['moderator', "admin", "superuser"] or user.id == shop.owner_id:
            if update_data:
                try:
                    await Shop.update(shop_id, **update_data)
                    return {"ok": True, "shop": shop}
                except DBAPIError as e:
                    print(e)
                    return Response(f"O'zgarishda hatolik: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response("O'zgarishda malumot yoq", status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response("Bu userda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


@shop_router.delete(path='', name="Delete Shop")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], shop_id: int):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    shop: Shop = await Shop.get(shop_id)
    if user and shop:
        if user.status in ["moderator", "admin", "superuser"]:
            await Shop.delete(shop)
            return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
        else:
            return Response("AdminPanelUserda xuquq yo'q", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
