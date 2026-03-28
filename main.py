from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import conf
from fast_routers import shop_product_router, shop_category_router, main_photos_router, work_router, bot_user_router, \
    admin_user_router, order_router, cart_router, jwt_router, shop_router, favourites_router, contact_router, \
    excel_router, call_order_router
from models import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mount("/media", StaticFiles(directory='media'), name='media')
    app.include_router(bot_user_router)
    app.include_router(admin_user_router)
    app.include_router(shop_router)
    app.include_router(work_router)
    app.include_router(shop_category_router)
    app.include_router(shop_product_router)
    app.include_router(favourites_router)
    # app.include_router(generate_router)
    app.include_router(main_photos_router)
    app.include_router(cart_router)
    app.include_router(order_router)
    app.include_router(contact_router)
    app.include_router(jwt_router)
    app.include_router(excel_router)
    app.include_router(call_order_router)
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
