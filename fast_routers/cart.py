from typing import Optional, Annotated

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from models import BotUser, Cart, ProductTip, ShopProduct, Shop
from utils import CartModel
from utils.details import sum_price_carts
from fast_routers.jwt_ import get_current_user

cart_router = APIRouter(prefix='/carts', tags=['Cart'])


class UserId(BaseModel):
    id: Optional[int] = None


@cart_router.get(path='', name="Carts")
async def list_category_shop() -> list[CartModel]:
    carts = await Cart.all()
    return carts


@cart_router.get(path='/detail', name="Get Cart")
async def list_category_shop(cart_id: int) -> CartModel:
    cart = await Cart.get(cart_id)
    return cart


@cart_router.get(path='/from-user', name="Get Cart")
async def list_category_shop(user_id: int) -> list[CartModel]:
    carts = await Cart.get_from_bot_user(user_id)
    return carts


@cart_router.get(path='/from-user-shop', name="Get Cart in Shop")
async def list_category_shop(user_id: int, shop_id: int):
    carts = await Cart.get_cart_from_shop(user_id, shop_id)
    carts.append({'sum': await sum_price_carts(carts)})
    return carts


@cart_router.post(path='', name="Create Cart from User")
async def list_category_shop(user_id: int,
                             product_id: int = Form(),
                             tip_id: int = Form(),
                             shop_id: int = Form(),
                             count: int = Form()):
    user = await BotUser.get(user_id)
    cart = await Cart.get_cart_from_product(user.id, product_id)
    tip = await ProductTip.get_product_and_tip(product_id, tip_id)
    product: ShopProduct = await ShopProduct.get(product_id)
    shop: Shop = await Shop.get(shop_id)
    if user:
        if shop:
            if tip:
                if product:
                    try:
                        if cart:
                            await Cart.update(cart.id, count=count, tip_id=tip_id, total=tip.price * count)
                            return {"ok": True, "update": cart.id}
                        else:
                            cart = await Cart.create(bot_user_id=user.id, product_id=product_id, count=count,
                                                     shop_id=shop_id, tip_id=tip_id, total=tip.price * count)
                            return {"ok": True, "create": cart}
                    except DBAPIError as e:
                        return Response("Yaratishda xatolik", status.HTTP_404_NOT_FOUND)
                else:
                    return Response("Product topilmadi", status.HTTP_404_NOT_FOUND)
            else:
                return Response("Tip topilmadi yoki productga tegishli emas", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Shop topilmadi", status.HTTP_404_NOT_FOUND)
    else:
        return Response("User topilmadi", status.HTTP_404_NOT_FOUND)


@cart_router.delete("/delete", name="Delete Product in cart")
async def user_delete(cart_id: int):
    cart = await Cart.get(cart_id)
    if cart:
        await Cart.delete(cart.id)
        return {"ok": True}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


@cart_router.patch(path='', name="Update Cart")
async def list_category_shop(cart_id: int, count: int,
                             tip_id: Optional[int] = None):
    cart: Cart = await Cart.get(cart_id)
    tip: ProductTip = await ProductTip.get(tip_id)
    if cart:
        if tip:
            try:
                if cart.product_id == tip.product_id:
                    total = count * tip.price
                    tip_id = tip_id
                else:
                    return Response(f"Tip id productga {cart.product_id} tegishli emas", status.HTTP_404_NOT_FOUND)
            except DBAPIError as e:
                return Response("Yaratishda xatolik", status.HTTP_404_NOT_FOUND)
        else:
            total = count * cart.tip.price
            tip_id = cart.tip_id
        await Cart.update(cart.id, count=count, total=total, tip_id=tip_id)
        return {"ok": True}
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
