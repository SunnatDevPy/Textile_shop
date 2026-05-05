from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette import status

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
from fast_routers.payme import payme_router
from fast_routers.click import click_router
from fast_routers.payment_urls import payment_url_router
from fast_routers.stock_movements import router as stock_movements_router
from fast_routers.dashboard import router as dashboard_router
from fast_routers.alerts import router as alerts_router
from fast_routers.bot_settings import router as bot_settings_router
from models import db
from utils.performance import PerformanceMonitoringMiddleware
from utils.logger import logger
from utils.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Textile Shop API", {"version": "1.0.0"})
    app.mount("/media", StaticFiles(directory='media'), name='media')
    app.include_router(shop_product_router, prefix="/api")
    app.include_router(product_photo_router, prefix="/api")
    app.include_router(product_items_router, prefix="/api")
    app.include_router(product_detail_router, prefix="/api")
    app.include_router(main_photos_router, prefix="/api")
    app.include_router(order_router, prefix="/api")
    app.include_router(categories_router, prefix="/api")
    app.include_router(collections_router, prefix="/api")
    app.include_router(color_router, prefix="/api")
    app.include_router(size_router, prefix="/api")
    app.include_router(system_router, prefix="/api")
    app.include_router(frontend_router, prefix="/api")
    app.include_router(admin_user_router, prefix="/api")
    app.include_router(payments_router, prefix="/api")
    app.include_router(excel_router, prefix="/api")
    app.include_router(history_router, prefix="/api")
    app.include_router(telegram_router, prefix="/api")
    app.include_router(payme_router, prefix="/api")
    app.include_router(click_router, prefix="/api")
    app.include_router(payment_url_router, prefix="/api")
    app.include_router(stock_movements_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(alerts_router, prefix="/api")
    app.include_router(bot_settings_router, prefix="/api")
    await db.create_all()
    # Legacy DBlar uchun color_code ustunini avtomatik qo'shamiz.
    await db.execute(text("ALTER TABLE colors ADD COLUMN IF NOT EXISTS color_code VARCHAR(255)"))
    await db.execute(text("UPDATE colors SET color_code = COALESCE(color_code, '#000000')"))
    # Legacy DBlar uchun clothing_type ustunini qo'shamiz.
    await db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS clothing_type VARCHAR(20)"))
    await db.execute(text("UPDATE products SET clothing_type = COALESCE(clothing_type, 'erkak')"))
    # Legacy DBlar uchun RETURNED statusini qo'shamiz
    await db.execute(text("ALTER TYPE statusorder ADD VALUE IF NOT EXISTS 'vozvrat'"))
    # Legacy DBlar uchun min_stock_level ustunini qo'shamiz
    await db.execute(text("ALTER TABLE product_items ADD COLUMN IF NOT EXISTS min_stock_level BIGINT DEFAULT 10"))
    await db.commit()
    logger.info("Database migrations completed")

    # Create indexes for performance
    logger.info("Creating database indexes...")
    try:
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_products_collection ON products(collection_id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_product_items_product_id ON product_items(product_id)"))
        await db.commit()
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning: {str(e)}")

    yield
    logger.info("Shutting down Textile Shop API")


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
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Frontend (React Admin Panel) - root path
admin_static_dir = Path("frontend-react/dist")
if admin_static_dir.exists():
    app.mount("/", StaticFiles(directory=str(admin_static_dir), html=True), name="frontend")
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

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=int(conf.RATE_LIMIT_PER_MINUTE),
    requests_per_hour=int(conf.RATE_LIMIT_PER_MINUTE) * 10
)

# Add performance monitoring middleware
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold_ms=1000.0)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    scope_token = db.set_scope(f"req-{id(request)}")
    try:
        return await call_next(request)
    except Exception as e:
        logger.log_error_with_trace(e, {"path": request.url.path, "method": request.method})
        raise
    finally:
        await db.remove()
        db.reset_scope(scope_token)


@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
    return Response(status_code=200, headers=headers)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(
        "Validation error",
        {
            "path": request.url.path,
            "method": request.method,
            "errors": str(exc.errors())
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Ma'lumotlar noto'g'ri formatda",
            "errors": exc.errors()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        f"HTTP {exc.status_code}",
        {
            "path": request.url.path,
            "method": request.method,
            "detail": exc.detail
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.log_error_with_trace(
        exc,
        {
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Serverda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
        }
    )
