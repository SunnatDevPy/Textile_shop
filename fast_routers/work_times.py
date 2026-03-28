from typing import Optional, Annotated

from fastapi import APIRouter, Form
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from starlette import status

from fast_routers.jwt_ import get_current_user
from models import AdminPanelUser, Shop, WorkTimes

work_router = APIRouter(prefix='/work', tags=['Work Shop'])


class UserId(BaseModel):
    id: int


@work_router.get(path='', name="Work all")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)]):
    return await WorkTimes.all()


@work_router.get(path='/detail', name="Get Work")
async def list_category_shop(work_id: int, user: Annotated[UserId, Depends(get_current_user)]):
    return await WorkTimes.get(work_id)


@work_router.get(path='/from_shop', name="Get Work in Shop")
async def list_category_shop(shop_id: int, user: Annotated[UserId, Depends(get_current_user)]):
    return await WorkTimes.from_shop(shop_id)


@work_router.post(path='', name="Create Work from User")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)],
                             shop_id: int = Form(),
                             open_time: str = Form(),
                             close_time: str = Form(),
                             weeks: list = Form()):
    shop = await Shop.get(shop_id)
    if shop:
        work = await WorkTimes.create(shop_id=shop_id, open_time=open_time, close_time=close_time, weeks=weeks)
        return {"ok": True, "object": work}
    else:
        return Response("Item Not Found", status.HTTP_404_NOT_FOUND)


class UpdateWork(BaseModel):
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    weeks: Optional[list] = None


@work_router.patch(path='', name="Update Work")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], work_id: int,
                             items: Annotated[UpdateWork, Form()]):
    work = await WorkTimes.get(work_id)
    if user.status in ["moderator", "admin", "superuser"]:
        if work:
            update_data = {k: v for k, v in items.dict().items() if v is not None}
            if update_data:
                await WorkTimes.update(work_id, **update_data)
                return {"ok": True}
            else:
                return Response("O'zgartirish uchun malumot yoq", status.HTTP_404_NOT_FOUND)
        else:
            return Response("Item Not Found", status.HTTP_404_NOT_FOUND)
    else:
        return Response("Bu userda xuquq yoq", status.HTTP_404_NOT_FOUND)
