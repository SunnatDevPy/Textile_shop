"""Проверка админа по username/password на каждый запрос (без JWT)."""

import secrets
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException
from fastapi import status
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials

from config import Configuration

security = HTTPBasic()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


async def verify_admin_credentials(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)]
) -> bool:
    admin_username = Configuration.ADMIN_USERNAME
    admin_pass_hash = Configuration.ADMIN_PASS  # bcrypt hash string

    if not secrets.compare_digest(credentials.username, admin_username):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if not verify_password(credentials.password, admin_pass_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    return True
