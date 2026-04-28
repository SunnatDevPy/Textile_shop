from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
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
from fast_routers.jwt_ import jwt_router
from fast_routers.orders import order_router
from fast_routers.category import categories_router
from fast_routers.collection import collections_router
from fast_routers.color import color_router
from fast_routers.size import size_router
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
    app.include_router(jwt_router)
    app.include_router(categories_router)
    app.include_router(collections_router)
    app.include_router(color_router)
    app.include_router(size_router)
    await db.create_all()
    yield


app = FastAPI(docs_url="/docs", lifespan=lifespan)
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
    allow_origins=["*"],  # или список конкретных доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    headers = {
        "Access-Control-Allow-Origin": "*",  # Или конкретные домены
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
    return Response(status_code=200, headers=headers)
