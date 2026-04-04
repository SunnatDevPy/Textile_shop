from enum import Enum
from typing import Annotated, Optional

import bcrypt
from fastapi import APIRouter, HTTPException, Form
from fastapi.params import Depends
from pydantic import BaseModel

from fast_routers.admin_auth import UserCheck, verify_admin_credentials
from models import AdminUser

admin_user_router = APIRouter(prefix='/panel', tags=['Admin User'])


class Token(BaseModel):
    access_token: str
    token_type: str


class UserAdd(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    contact: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = False
    status: Optional[str] = "moderator"


class UserList(BaseModel):
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = False
    status: Optional[str] = None


@admin_user_router.get('', name="List Panel User")
async def user_list(_: Annotated[AdminUser, Depends(verify_admin_credentials)]) -> list[UserList]:
    users = await AdminUser.all()
    return users


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = None


@admin_user_router.get("/profile", name="Detail Panel User")
async def user_detail(user: Annotated[AdminUser, Depends(verify_admin_credentials)]):
    return await AdminUser.get(user.id)


@admin_user_router.patch("/profile", name="Update User")
async def user_patch_update(
    user: Annotated[AdminUser, Depends(verify_admin_credentials)], items: Annotated[UserUpdate, Form()]
):
    update_data = {k: v for k, v in items.dict().items() if v is not None}
    if update_data:
        await AdminUser.update(user.id, **update_data)
        return {"ok": True, "data": update_data}
    else:
        return {"ok": False, "message": "Nothing to update"}


class UserStatus(str, Enum):
    MODERATOR = "moderator"
    ADMIN = "admin"
    CALL_CENTER = "call center"


@admin_user_router.patch("/status", name="Update Status")
async def user_add(operator: Annotated[AdminUser, Depends(verify_admin_credentials)], user_id: int,
                   status: Annotated[UserStatus, Form()]):
    user = await AdminUser.get(user_id)
    if status not in ['MODERATOR', 'moderator', 'admin', "ADMIN", 'CALL_CENTER', "call center"]:
        raise HTTPException(status_code=404, detail="Not status")
    if operator.status.value == "admin":
        if status == 'string' or status == '':
            status = None
        await AdminUser.update(user.id, status=status)
        return {"ok": True, "user": user}
    else:
        raise HTTPException(status_code=404, detail="Bu userda xuquq yo'q")


@admin_user_router.delete("/")
async def user_delete(operator: Annotated[AdminUser, Depends(verify_admin_credentials)], user_id: int):
    if operator.status.value in ["admin", "superuser"]:
        await AdminUser.delete(user_id)
        return {"ok": True, 'id': user_id}
    else:
        raise HTTPException(status_code=404, detail="Bu userda xuquq yo'q")


class UserLogin(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


class Register(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    contact: Optional[str] = None
    status: UserStatus
    password: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# user: Annotated[UserId, Depends(get_current_user)]
@admin_user_router.post(path='/register', name="Register")
async def register(items: Annotated[Register, Form()]) -> UserList:
    items.password = hash_password(items.password)
    print(items)
    user: AdminUser = await AdminUser.filter(AdminUser.username == items.username)
    if items.status not in ['MODERATOR', 'moderator', 'admin', "ADMIN", 'CALL_CENTER', "call center"]:
        raise HTTPException(status_code=404, detail="Not status")
    if user:
        raise HTTPException(status_code=404, detail="Bunday username bor")

    users = await AdminUser.create(**items.dict(), is_active=False)
    return users
