from fastapi import APIRouter
from sqlalchemy import text

from models.database import db

system_router = APIRouter(prefix="/system", tags=["System"])


@system_router.get("/health", summary="API holatini tekshirish")
async def health_check():
    return {"ok": True, "service": "textile-shop-api"}


@system_router.get("/ready", summary="DB ulanishini tekshirish")
async def readiness_check():
    await db.execute(text("SELECT 1"))
    return {"ok": True, "database": "connected"}


@system_router.get("/auth-mode", summary="Loyihadagi autentifikatsiya turi")
async def auth_mode():
    return {"auth": "basic", "jwt_enabled": False}
