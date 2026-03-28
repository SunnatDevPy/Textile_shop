from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Form
from fastapi.params import Depends
from pydantic import BaseModel
from fast_routers.jwt_ import get_current_user_bot, get_current_user
from models import BotUser, AdminPanelUser

bot_user_router = APIRouter(prefix='/bot-users', tags=['Bot User'])


class UserList(BaseModel):
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = None


class UserId(BaseModel):
    id: Optional[int] = None


@bot_user_router.get('', name="List Bot User")
async def user_list(user: Annotated[UserId, Depends(get_current_user)]) -> list[UserList]:
    users = await BotUser.all()
    return users


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = None


@bot_user_router.get("/profile", name="Detail Bot User")
async def user_detail(user: Annotated[UserId, Depends(get_current_user_bot)]):
    return user


@bot_user_router.patch("/profile", name="Update Bot User")
async def user_patch_update(user: Annotated[UserId, Depends(get_current_user_bot)],
                            items: Annotated[UserUpdate, Form()]):
    update_data = {k: v for k, v in items.dict().items() if v is not None}
    if update_data:
        await BotUser.update(user.id, **update_data)
        return {"ok": True, "data": update_data}
    else:
        return {"ok": False, "message": "Nothing to update"}


@bot_user_router.delete("/")
async def user_delete(bot_user_id: int, user: Annotated[UserId, Depends(get_current_user_bot)]):
    user = await BotUser.get(bot_user_id)
    if user:
        if user.status.value in ['moderator', "admin"]:
            await BotUser.delete(bot_user_id)
            return {"ok": True, 'id': bot_user_id}
        else:
            raise HTTPException(status_code=404, detail="Bu userda xuquq yo'q")
    else:
        raise HTTPException(status_code=404, detail="Item not found")
