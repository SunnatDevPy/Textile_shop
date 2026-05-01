from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import conf
from fast_routers.products import shop_product_router
from fast_routers.product_subresources import (
    product_detail_router,
    product_items_router,
    product_photo_router,
)
from fast_routers.main_photos import main_photos_router
from fast_routers.orders import order_router
from fast_routers.category import categories_router
from fast_routers.collection import collections_router
from fast_routers.color import color_router
from fast_routers.size import size_router
from fast_routers.system import system_router
from fast_routers.frontend import frontend_router
from fast_routers.admin_users import admin_user_router
from fast_routers.payments import payments_router
from fast_routers.excel_save import excel_router
from fast_routers.history import history_router
from fast_routers.telegram_bot import telegram_router
from models import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mount("/media", StaticFiles(directory='media'), name='media')
    app.include_router(shop_product_router)
    app.include_router(product_photo_router)
    app.include_router(product_items_router)
    app.include_router(product_detail_router)
    app.include_router(main_photos_router)
    app.include_router(order_router)
    app.include_router(categories_router)
    app.include_router(collections_router)
    app.include_router(color_router)
    app.include_router(size_router)
    app.include_router(system_router)
    app.include_router(frontend_router)
    app.include_router(admin_user_router)
    app.include_router(payments_router)
    app.include_router(excel_router)
    app.include_router(history_router)
    app.include_router(telegram_router)
    await db.create_all()
    # Legacy DBlar uchun color_code ustunini avtomatik qo'shamiz.
    await db.execute(text("ALTER TABLE colors ADD COLUMN IF NOT EXISTS color_code VARCHAR(255)"))
    await db.execute(text("UPDATE colors SET color_code = COALESCE(color_code, '#000000')"))
    # Legacy DBlar uchun clothing_type ustunini qo'shamiz.
    await db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS clothing_type VARCHAR(20)"))
    await db.execute(text("UPDATE products SET clothing_type = COALESCE(clothing_type, 'erkak')"))
    await db.commit()
    yield


app = FastAPI(
    title="Textile Shop API",
    description=(
        "Textile Shop backend API.\n\n"
        "Swagger orqali endpointlarni oddiy usulda test qilishingiz mumkin.\n"
        "Autentifikatsiya: faqat Basic Auth (JWT ishlatilmaydi).\n"
        "Super admin operator/admin yaratadi, operator asosan buyurtma bilan ishlaydi.\n"
        "Click/Payme uchun callback endpointlar tayyorlangan.\n"
        "Excel import, order/product history va loglar API mavjud.\n"
        "JWT endpointlari bu loyihada o'chirilgan."
    ),
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)
app.mount("/admin", StaticFiles(directory="admin_panel", html=True), name="admin_panel")


@app.get("/admin", include_in_schema=False)
async def admin_root_redirect():
    return RedirectResponse(url="/admin/home.html")
# app.add_middleware(
#     # CORSMiddleware,
#     # # allow_origins=["https://web.telegram.org", "https://your-client.com"],
#     # allow_origins=["*"],
#     # allow_credentials=True,
#     # allow_methods=["*"],
#     # allow_headers=["*"],
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Явное указание методов
#     allow_headers=["*"],
#     expose_headers=["*"],
#     max_age=600  # Кеширование CORS-префлайт запросов (в секундах)
# )
# # "https://web.telegram.org",
# # "https://gxfl20sh-5173.euw.devtunnels.ms/",
# # "http://localhost:3000",
# # "http://localhost:5173"

app.add_middleware(SessionMiddleware, secret_key=conf.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    finally:
        await db.remove()


@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
    return Response(status_code=200, headers=headers)
