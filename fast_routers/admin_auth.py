"""Basic auth va rollarga asoslangan ruxsatlar."""

import secrets
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config import Configuration
from models import AdminUser

security = HTTPBasic()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


async def verify_admin_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> AdminUser:
    user = await AdminUser.filter(AdminUser.username == credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not active",
        )

    return user


async def verify_super_admin_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> bool:
    admin_username = Configuration.ADMIN_USERNAME
    admin_pass_hash = Configuration.ADMIN_PASS

    if not secrets.compare_digest(credentials.username, admin_username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid super admin credentials",
        )

    if not verify_password(credentials.password, admin_pass_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid super admin credentials",
        )
    return True


def _status_value(user: AdminUser) -> str:
    if hasattr(user.status, "value"):
        return str(user.status.value)
    return str(user.status)


async def require_admin(user: Annotated[AdminUser, Depends(verify_admin_credentials)]) -> AdminUser:
    if _status_value(user) != AdminUser.StatusUser.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat admin uchun ruxsat",
        )
    return user
