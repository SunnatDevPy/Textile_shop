from typing import Annotated

from fastapi import APIRouter
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.jwt_ import get_current_user
from models import ShopProduct, Shop, BotUser
from models.products_model import LoveProducts
from utils import FavouritesSchema

favourites_router = APIRouter(prefix='/favourites-products', tags=['Favourites'])


class UserId(BaseModel):
    user: int


@favourites_router.get(path='', name="Get All Favourites")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)]) -> list[FavouritesSchema]:
    return await LoveProducts.all()


@favourites_router.get(path='/detail', name="Get favourites")
async def list_category_shop(favourites_id: int,
                             user: Annotated[UserId, Depends(get_current_user)]) -> FavouritesSchema:
    product = await LoveProducts.get(favourites_id)
    return product


@favourites_router.get(path='/from-shop', name="Get from Shop Favourites")
async def list_category_shop(shop_id: int, user: Annotated[UserId, Depends(get_current_user)]) -> list[
    FavouritesSchema]:
    products = await LoveProducts.get_from_shop(shop_id)
    return products


@favourites_router.get(path='/from-user', name="Get from User and Shop Favourites")
async def list_category_shop(shop_id: int, user_id: int) -> list[
    FavouritesSchema]:
    products = await LoveProducts.get_cart_from_shop(user_id, shop_id)
    return products


@favourites_router.post(path='', name="Create Product from Favourites")
async def list_category_shop(product_id: int, shop_id: int, user_id: int):
    user: BotUser = await BotUser.get(user_id)
    product: ShopProduct = await ShopProduct.get_shop_product(product_id, shop_id)
    shop = await Shop.get(shop_id)
    if user and shop:
        if product:
            if product.is_active:
                try:
                    products = await LoveProducts.create(shop_id=shop_id, bot_user_id=user.id,
                                                         product_id=product_id,
                                                         is_active=product.is_active)
                    return {"ok": True, "product": products}
                except DBAPIError as e:
                    return Response("Yaratishda xatolik", status.HTTP_404_NOT_FOUND)
            else:
                return Response("Yaratilmadi mahsulot activ emas", status.HTTP_404_NOT_FOUND)

        else:
            return Response("Product topilmadi Shopga tegishli emas", status.HTTP_404_NOT_FOUND)
    else:
        return Response("User yoki shop topilmadi", status.HTTP_404_NOT_FOUND)


@favourites_router.delete(path='', name="Delete Shop Favourites")
async def list_category_shop(favourites_id: int):
    product = await LoveProducts.get(favourites_id)
    if product:
        await LoveProducts.delete(favourites_id)
        return {'ok': True}
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
