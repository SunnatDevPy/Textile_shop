"""Bot settings API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from models import db, BotSettings, AdminUser
from fast_routers.admin_auth import verify_admin_credentials
from utils.logger import logger

router = APIRouter(prefix="/bot-settings", tags=["Bot Settings"])


class BotSettingsUpdate(BaseModel):
    bot_token: Optional[str] = None
    group_ids: Optional[str] = None
    is_enabled: Optional[bool] = None
    notify_new_orders: Optional[bool] = None
    notify_low_stock: Optional[bool] = None
    notify_payment: Optional[bool] = None


@router.get("/")
async def get_bot_settings(
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Bot sozlamalarini olish"""

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        # Agar sozlamalar yo'q bo'lsa, default yaratish
        settings = BotSettings(
            bot_token=None,
            group_ids=None,
            is_enabled=False,
            notify_new_orders=True,
            notify_low_stock=True,
            notify_payment=True
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {
        "id": settings.id,
        "bot_token": settings.bot_token,
        "group_ids": settings.group_ids,
        "is_enabled": settings.is_enabled,
        "notify_new_orders": settings.notify_new_orders,
        "notify_low_stock": settings.notify_low_stock,
        "notify_payment": settings.notify_payment
    }


@router.put("/")
async def update_bot_settings(
    data: BotSettingsUpdate,
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Bot sozlamalarini yangilash"""

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        # Yangi sozlamalar yaratish
        settings = BotSettings(
            bot_token=data.bot_token,
            group_ids=data.group_ids,
            is_enabled=data.is_enabled if data.is_enabled is not None else False,
            notify_new_orders=data.notify_new_orders if data.notify_new_orders is not None else True,
            notify_low_stock=data.notify_low_stock if data.notify_low_stock is not None else True,
            notify_payment=data.notify_payment if data.notify_payment is not None else True
        )
        db.add(settings)
    else:
        # Mavjud sozlamalarni yangilash
        if data.bot_token is not None:
            settings.bot_token = data.bot_token
        if data.group_ids is not None:
            settings.group_ids = data.group_ids
        if data.is_enabled is not None:
            settings.is_enabled = data.is_enabled
        if data.notify_new_orders is not None:
            settings.notify_new_orders = data.notify_new_orders
        if data.notify_low_stock is not None:
            settings.notify_low_stock = data.notify_low_stock
        if data.notify_payment is not None:
            settings.notify_payment = data.notify_payment

    await db.commit()
    await db.refresh(settings)

    logger.info(
        "Bot settings updated",
        {
            "user_id": current_user.id,
            "is_enabled": settings.is_enabled
        }
    )

    return {
        "success": True,
        "settings": {
            "id": settings.id,
            "bot_token": settings.bot_token,
            "group_ids": settings.group_ids,
            "is_enabled": settings.is_enabled,
            "notify_new_orders": settings.notify_new_orders,
            "notify_low_stock": settings.notify_low_stock,
            "notify_payment": settings.notify_payment
        }
    }


@router.post("/test")
async def test_bot_connection(
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """Bot ulanishini test qilish"""

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings or not settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token sozlanmagan")

    # Test message yuborish
    try:
        import aiohttp

        url = f"https://api.telegram.org/bot{settings.bot_token}/getMe"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        bot_info = data.get("result", {})
                        return {
                            "success": True,
                            "bot_info": {
                                "id": bot_info.get("id"),
                                "username": bot_info.get("username"),
                                "first_name": bot_info.get("first_name")
                            }
                        }

                return {
                    "success": False,
                    "error": "Bot token noto'g'ri"
                }
    except Exception as e:
        logger.error(f"Bot test error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/get-updates")
async def get_bot_updates(
    current_user: AdminUser = Depends(verify_admin_credentials)
):
    """
    Botga kelgan oxirgi xabarlarni olish (Group ID topish uchun)
    """

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings or not settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token sozlanmagan")

    try:
        import aiohttp

        url = f"https://api.telegram.org/bot{settings.bot_token}/getUpdates"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        updates = data.get("result", [])

                        # Group chat larni ajratib olish
                        groups = []
                        for update in updates:
                            message = update.get("message", {})
                            chat = message.get("chat", {})

                            if chat.get("type") in ["group", "supergroup"]:
                                groups.append({
                                    "chat_id": chat.get("id"),
                                    "title": chat.get("title"),
                                    "type": chat.get("type"),
                                    "message_text": message.get("text", ""),
                                    "from_user": message.get("from", {}).get("first_name", "")
                                })

                        return {
                            "success": True,
                            "groups": groups,
                            "total_updates": len(updates),
                            "help": "Agar guruh ko'rinmasa, guruhda /start yoki biror xabar yuboring va qayta urinib ko'ring"
                        }

                return {
                    "success": False,
                    "error": "Bot token noto'g'ri"
                }
    except Exception as e:
        logger.error(f"Get updates error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


class BotSettingsUpdate(BaseModel):
    bot_token: Optional[str] = None
    group_ids: Optional[str] = None
    is_enabled: Optional[bool] = None
    notify_new_orders: Optional[bool] = None
    notify_low_stock: Optional[bool] = None
    notify_payment: Optional[bool] = None


@router.get("/")
async def get_bot_settings(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """Bot sozlamalarini olish"""

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        # Agar sozlamalar yo'q bo'lsa, default yaratish
        settings = BotSettings(
            bot_token=None,
            group_ids=None,
            is_enabled=False,
            notify_new_orders=True,
            notify_low_stock=True,
            notify_payment=True
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {
        "id": settings.id,
        "bot_token": settings.bot_token,
        "group_ids": settings.group_ids,
        "is_enabled": settings.is_enabled,
        "notify_new_orders": settings.notify_new_orders,
        "notify_low_stock": settings.notify_low_stock,
        "notify_payment": settings.notify_payment
    }


@router.put("/")
async def update_bot_settings(
    data: BotSettingsUpdate,
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """Bot sozlamalarini yangilash"""

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        # Yangi sozlamalar yaratish
        settings = BotSettings(
            bot_token=data.bot_token,
            group_ids=data.group_ids,
            is_enabled=data.is_enabled if data.is_enabled is not None else False,
            notify_new_orders=data.notify_new_orders if data.notify_new_orders is not None else True,
            notify_low_stock=data.notify_low_stock if data.notify_low_stock is not None else True,
            notify_payment=data.notify_payment if data.notify_payment is not None else True
        )
        db.add(settings)
    else:
        # Mavjud sozlamalarni yangilash
        if data.bot_token is not None:
            settings.bot_token = data.bot_token
        if data.group_ids is not None:
            settings.group_ids = data.group_ids
        if data.is_enabled is not None:
            settings.is_enabled = data.is_enabled
        if data.notify_new_orders is not None:
            settings.notify_new_orders = data.notify_new_orders
        if data.notify_low_stock is not None:
            settings.notify_low_stock = data.notify_low_stock
        if data.notify_payment is not None:
            settings.notify_payment = data.notify_payment

    await db.commit()
    await db.refresh(settings)

    logger.info(
        "Bot settings updated",
        {
            "user_id": current_user.id,
            "is_enabled": settings.is_enabled
        }
    )

    return {
        "success": True,
        "settings": {
            "id": settings.id,
            "bot_token": settings.bot_token,
            "group_ids": settings.group_ids,
            "is_enabled": settings.is_enabled,
            "notify_new_orders": settings.notify_new_orders,
            "notify_low_stock": settings.notify_low_stock,
            "notify_payment": settings.notify_payment
        }
    }


@router.post("/test")
async def test_bot_connection(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """Bot ulanishini test qilish"""

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings or not settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token sozlanmagan")

    # Test message yuborish
    try:
        import aiohttp

        url = f"https://api.telegram.org/bot{settings.bot_token}/getMe"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        bot_info = data.get("result", {})
                        return {
                            "success": True,
                            "bot_info": {
                                "id": bot_info.get("id"),
                                "username": bot_info.get("username"),
                                "first_name": bot_info.get("first_name")
                            }
                        }

                return {
                    "success": False,
                    "error": "Bot token noto'g'ri"
                }
    except Exception as e:
        logger.error(f"Bot test error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/get-updates")
async def get_bot_updates(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Botga kelgan oxirgi xabarlarni olish (Group ID topish uchun)
    """

    query = select(BotSettings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings or not settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token sozlanmagan")

    try:
        import aiohttp

        url = f"https://api.telegram.org/bot{settings.bot_token}/getUpdates"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        updates = data.get("result", [])

                        # Group chat larni ajratib olish
                        groups = []
                        for update in updates:
                            message = update.get("message", {})
                            chat = message.get("chat", {})

                            if chat.get("type") in ["group", "supergroup"]:
                                groups.append({
                                    "chat_id": chat.get("id"),
                                    "title": chat.get("title"),
                                    "type": chat.get("type"),
                                    "message_text": message.get("text", ""),
                                    "from_user": message.get("from", {}).get("first_name", "")
                                })

                        return {
                            "success": True,
                            "groups": groups,
                            "total_updates": len(updates),
                            "help": "Agar guruh ko'rinmasa, guruhda /start yoki biror xabar yuboring va qayta urinib ko'ring"
                        }

                return {
                    "success": False,
                    "error": "Bot token noto'g'ri"
                }
    except Exception as e:
        logger.error(f"Get updates error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
