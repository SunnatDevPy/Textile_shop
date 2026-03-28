from datetime import datetime
from enum import Enum
from typing import Optional, Annotated, List

from fastapi import APIRouter, Form, HTTPException
from fastapi import Response
from fastapi.params import Depends
from geopy.distance import geodesic
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from bot.buttuns.inline import group_order_btn
from dispatcher import bot
from fast_routers.jwt_ import get_current_user
from models import Shop, Order, CallOrder, AdminPanelUser, CallOrderItem, ProductTip
from utils import OrderModel, ProductList
from utils.details import detail_order

call_order_router = APIRouter(prefix='/call-order', tags=['Call Orders'])


class CallOrderItemsModel(BaseModel):
    id: int
    product_id: int
    order_id: int
    count: int
    volume: int
    unit: str
    price: int
    total: int


class CallOrderModel(BaseModel):
    id: int
    payment: str
    status: str
    panel_user_id: int
    address: str
    shop_id: int
    first_last_name: str
    contact: str
    driver_price: int
    total_sum: int
    lat: float
    long: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    order_items: Optional[list[CallOrderItemsModel]] = None
    product: Optional[ProductList] = None


class UserId(BaseModel):
    id: Optional[int] = None


@call_order_router.get(path='', name="Call Orders")
async def list_category_shop() -> list[CallOrderModel]:
    orders = await CallOrder.all()
    return orders


@call_order_router.get(path='/detail', name="Get Call Orders")
async def list_category_shop(call_order_id: int) -> CallOrderModel:
    order = await CallOrder.get(call_order_id)
    return order


@call_order_router.get(path='/from-call-user', name="Get Call Orders from Call User")
async def list_category_shop(call_user_id: int, shop_id: int) -> list[OrderModel]:
    # orders = await detail_orders_types(user_id)
    orders = await CallOrder.get_cart_from_shop(call_user_id, shop_id)
    return orders


@call_order_router.get(path='/from-status', name="Get Call Order from Status in User")
async def list_category_shop(call_user_id: int, status_order: str):
    if status_order not in ['yangi', 'NEW', "IN_PROGRESS", "yetkazilmoqda",
                            "IS_PROCESS", "jarayonda",
                            "READY", "tayyor",
                            "DELIVERED", "yetkazildi",
                            "CANCELLED", "bekor qilindi"]:
        return Response("Buyurtmaga notog'ri status berilgan", status.HTTP_404_NOT_FOUND)
    orders = await Order.get_from_bot_user_in_type(call_user_id, status_order)
    if orders:
        return {'orders': orders}
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


class OrderItemSchema(BaseModel):
    product_id: int
    count: int
    price: float
    id: int


class StatusOrder(str, Enum):
    NEW = "yangi"
    IS_GOING = "yig'ilmoqda"
    IN_PROGRESS = "yetkazilmoqda"
    DELIVERED = "yetkazildi"
    CANCELLED = "bekor qilindi"


class Payment(str, Enum):
    CASH = "naqt"
    TERMINAL = "karta"


class CreateOrder(BaseModel):
    payment: Payment
    long: float
    lat: float
    contact: str
    address: str
    first_last_name: str
    order_items: List[OrderItemSchema]


@call_order_router.post(path='', name="Create Call Order from User")
async def create_call_order(user: Annotated[UserId, Depends(get_current_user)], shop_id: int, order_data: CreateOrder):
    user = await AdminPanelUser.get(user.id)
    shop = await Shop.get(shop_id)

    if order_data.payment not in ['CASH', "TERMINAL", "karta", 'naqt']:
        raise HTTPException(status_code=400, detail="Notog'ri tip tolovi")

    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    if not shop:
        raise HTTPException(status_code=404, detail="Shop yoq")

    if not order_data.items:
        raise HTTPException(status_code=400, detail="zakaz yoq")

    try:
        distance_km = geodesic((shop.lat, shop.long), (order_data.lat, order_data.long)).kilometers
    except:
        distance_km = 0

    sum_order = sum(item.count * item.price for item in order_data.items)

    try:
        order = await CallOrder.create(
            **order_data.dict(exclude={"items"}),
            total_sum=sum_order,
            driver_price=distance_km,
            shop_id=shop_id,
            call_user_id=user.id,
            status="NEW"
        )

        order_items = []
        for item in order_data.items:
            tip: ProductTip = await ProductTip.get(item.id)
            order_item = await CallOrderItem.create(
                product_id=item.product_id,
                order_id=order.id,
                count=item.count,
                price=item.price,
                total=item.count * item.price,
                volume=tip.volume,
                unit=tip.unit,
            )
            order_items.append(order_item)

        try:
            message = await bot.send_message(shop.order_group_id, await detail_order(order), parse_mode="HTML",
                                             reply_markup=group_order_btn(order))
            await bot.send_location(shop.order_group_id, latitude=order.lat, longitude=order.long,
                                    reply_to_message_id=message.message_id)
        except:
            try:
                message = await bot.send_message(279361769, await detail_order(order), parse_mode="HTML",
                                                 reply_markup=group_order_btn(order))
                await bot.send_location(279361769, latitude=order.lat, longitude=order.long,
                                        reply_to_message_id=message.message_id)
            except:
                return {"ok": True, "message": "Buyurtma yaratildi lekin guruxga yuborimadi", "order": order,
                        "items": order_items}

        return {"ok": True, "message": "buyurtma yaratildi", "order": order,
                "items": order_items}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Ошибка при создании заказа")


class UpdateOrder(BaseModel):
    status: StatusOrder


@call_order_router.patch(path='', name="Update Order")
async def list_category_shop(call_order_id: int, items: Annotated[UpdateOrder, Form()],
                             user: Annotated[UserId, Depends(get_current_user)]):
    if items.status not in ['yangi', 'NEW', "IS_PROCESS", "jarayonda",
                            "IN_PROGRESS", "yetkazilmoqda",
                            "READY", "tayyor",
                            "DELIVERED", "yetkazildi",
                            "CANCELLED", "bekor qilindi"]:
        return Response("Buyurtmaga notog'ri status berilgan", status.HTTP_404_NOT_FOUND)
    order = await CallOrder.get(call_order_id)
    if order:
        update_data = {k: v for k, v in items.dict().items() if v is not None}
        if update_data:
            try:
                await CallOrder.update(call_order_id, **update_data)
                return {"ok": True, "order": order}
            except DBAPIError as e:
                print(e)
                return Response("O'zgarishda xatolik", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


@call_order_router.patch(path='/canceled', name="Canceled Order")
async def list_category_shop(call_order_id: int, user: Annotated[UserId, Depends(get_current_user)]):
    order = await CallOrder.get(call_order_id)
    if order:
        await CallOrder.update(order.id, status="CANCELLED")
        return {"ok": True, "order": order}
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
