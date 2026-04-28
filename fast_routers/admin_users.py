from typing import Annotated, Optional

import bcrypt
from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel

from fast_routers.admin_auth import (
    require_admin,
    verify_admin_credentials,
    verify_super_admin_credentials,
)
from models import AdminUser

admin_user_router = APIRouter(prefix="/panel", tags=["Admin Users"])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class CreateOperatorPayload(BaseModel):
    username: str
    operator_code: str
    status: AdminUser.StatusUser = AdminUser.StatusUser.OPERATOR
    is_active: bool = True

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        operator_code: str = Form(...),
        status: AdminUser.StatusUser = Form(AdminUser.StatusUser.OPERATOR),
        is_active: bool = Form(True),
    ):
        return cls(
            username=username,
            operator_code=operator_code,
            status=status,
            is_active=is_active,
        )


class UpdateUserPayload(BaseModel):
    username: Optional[str] = None
    operator_code: Optional[str] = None
    is_active: Optional[bool] = None

    @classmethod
    def as_form(
        cls,
        username: Optional[str] = Form(None),
        operator_code: Optional[str] = Form(None),
        is_active: Optional[bool] = Form(None),
    ):
        return cls(
            username=username,
            operator_code=operator_code,
            is_active=is_active,
        )


@admin_user_router.post(
    "/operators",
    summary="Super admin operator/admin yaratadi (username + operator_code)",
)
async def create_operator(
    _: Annotated[bool, Depends(verify_super_admin_credentials)],
    payload: Annotated[CreateOperatorPayload, Depends(CreateOperatorPayload.as_form)],
):
    existing = await AdminUser.filter(AdminUser.username == payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bunday username allaqachon mavjud",
        )

    user = await AdminUser.create(
        username=payload.username,
        password=hash_password(payload.operator_code),
        status=payload.status,
        is_active=payload.is_active,
    )
    return {"ok": True, "user_id": user.id, "username": user.username, "status": user.status}


@admin_user_router.get(
    "/users",
    summary="Admin/operatorlar ro'yxati (admin)",
)
async def list_users(_: Annotated[AdminUser, Depends(require_admin)]):
    return await AdminUser.all()


@admin_user_router.get(
    "/me",
    summary="Hozirgi foydalanuvchi profili",
)
async def my_profile(user: Annotated[AdminUser, Depends(verify_admin_credentials)]):
    return user


@admin_user_router.patch(
    "/users/{user_id}",
    summary="Operator/adminni tahrirlash (admin, operator_code ni almashtirish ham mumkin)",
)
async def update_user(
    user_id: int,
    _: Annotated[AdminUser, Depends(require_admin)],
    payload: Annotated[UpdateUserPayload, Depends(UpdateUserPayload.as_form)],
):
    user = await AdminUser.get_or_none(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User topilmadi")

    update_data = payload.model_dump(exclude_none=True)
    if "operator_code" in update_data:
        update_data["password"] = hash_password(update_data.pop("operator_code"))

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yangilash uchun ma'lumot yo'q")

    await AdminUser.update(user_id, **update_data)
    return {"ok": True}
