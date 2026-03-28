from typing import Optional, Annotated

from fastapi import APIRouter
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError
from starlette import status

from fast_routers.jwt_ import get_current_user
from models import Shop, Order, CallCenters, AdminPanelUser
from utils import OrderModel

contact_router = APIRouter(prefix='/contact', tags=['Contact'])


@contact_router.get(path='', name="Contacts")
async def list_category_shop():
    orders = await CallCenters.all()
    return orders


@contact_router.get(path='/detail', name="Get CallCenter")
async def list_category_shop(contact_id: int) -> OrderModel:
    order = await CallCenters.get(contact_id)
    return order


@contact_router.get(path='/from-shop', name="Get CallCenters")
async def list_category_shop(shop_id: int):
    orders = await CallCenters.filter(CallCenters.shop_id == shop_id)
    if orders:
        return {'contacts': orders}
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


class UserId(BaseModel):
    id: Optional[int] = None


@contact_router.post(path='', name="Create Order from User")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], contact: str, shop_id: int):
    user = await AdminPanelUser.get(user.id)
    shop = await Shop.get(shop_id)
    contact = await CallCenters.filter(CallCenters.contact == contact.strip())
    if contact:
        return Response("Bunday contact bor", status.HTTP_404_NOT_FOUND)

    if user and shop:
        if user.status in ['moderator', 'call center', 'admin', 'superuser']:

            try:
                order = await CallCenters.create(contact=contact, shop_id=shop_id)
                return {"ok": True, "order": order}
            except DBAPIError as e:
                print(e)
                return Response("O'zgarishda xatolik", status.HTTP_404_NOT_FOUND)

        else:
            return Response("Xuquq yoq", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Not Found", status.HTTP_404_NOT_FOUND)


@contact_router.patch(path='', name="Update Order")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], contact_id: int, new_contact: str):
    user = await AdminPanelUser.get(user.id)
    contact: CallCenters = await CallCenters.get(contact_id)
    if contact and user:
        if contact.contact != new_contact and user.status in ['moderator', 'admin', 'superuser']:
            try:
                contact = await CallCenters.update(contact_id, new_contact=new_contact)
                return {"ok": True, "contact": contact}
            except DBAPIError as e:
                print(e)
                return Response("O'zgarishda xatolik", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


@contact_router.patch(path='/delete', name="Contact Delete")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], contact_id: int):
    order = await CallCenters.get(contact_id)
    user = await AdminPanelUser.get(user.id)
    if order and user:
        if user.status in ['moderator', 'admin', 'superuser']:
            await Order.update(order.id, status="CANCELLED")
            return {"ok": True, "order": order}
        else:
            return Response("Xuquq yoq", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
