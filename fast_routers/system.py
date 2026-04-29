from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete as sqlalchemy_delete, text

from fast_routers.admin_auth import verify_super_admin_credentials
from models import Category, Collection, Color, Order, OrderItem, Product, ProductDetail, ProductItems, ProductPhoto, Size
from models.database import db
from utils.response import ok_response

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


@system_router.post("/dev/seed-fake", summary="DEV: fake obyektlar yaratish (super admin)")
async def seed_fake_data(
    _: bool = Depends(verify_super_admin_credentials),
    n: int = Query(3, ge=1, le=20, description="Har bir asosiy entity uchun nechta obyekt yaratish"),
    clear_before: bool = Query(False, description="True bo'lsa, seeddan oldin asosiy jadvallar tozalanadi"),
):
    created = {
        "categories": 0,
        "collections": 0,
        "colors": 0,
        "sizes": 0,
        "products": 0,
        "product_items": 0,
        "product_details": 0,
        "product_photos": 0,
        "orders": 0,
        "order_items": 0,
    }

    categories = []
    collections = []
    colors = []
    sizes = []
    products = []

    cleared = {
        "order_items": 0,
        "orders": 0,
        "product_details": 0,
        "product_photos": 0,
        "product_items": 0,
        "products": 0,
        "sizes": 0,
        "colors": 0,
        "collections": 0,
        "categories": 0,
    }

    if clear_before:
        # FK cheklovlari uchun tozalash tartibi muhim.
        del_order_items = await db.execute(sqlalchemy_delete(OrderItem))
        del_orders = await db.execute(sqlalchemy_delete(Order))
        del_product_details = await db.execute(sqlalchemy_delete(ProductDetail))
        del_product_photos = await db.execute(sqlalchemy_delete(ProductPhoto))
        del_product_items = await db.execute(sqlalchemy_delete(ProductItems))
        del_products = await db.execute(sqlalchemy_delete(Product))
        del_sizes = await db.execute(sqlalchemy_delete(Size))
        del_colors = await db.execute(sqlalchemy_delete(Color))
        del_collections = await db.execute(sqlalchemy_delete(Collection))
        del_categories = await db.execute(sqlalchemy_delete(Category))
        await db.commit()

        cleared["order_items"] = int(del_order_items.rowcount or 0)
        cleared["orders"] = int(del_orders.rowcount or 0)
        cleared["product_details"] = int(del_product_details.rowcount or 0)
        cleared["product_photos"] = int(del_product_photos.rowcount or 0)
        cleared["product_items"] = int(del_product_items.rowcount or 0)
        cleared["products"] = int(del_products.rowcount or 0)
        cleared["sizes"] = int(del_sizes.rowcount or 0)
        cleared["colors"] = int(del_colors.rowcount or 0)
        cleared["collections"] = int(del_collections.rowcount or 0)
        cleared["categories"] = int(del_categories.rowcount or 0)

    for i in range(1, n + 1):
        c = await Category.create(
            name_uz=f"Fake kategoriya {i}",
            name_ru=f"Фейк категория {i}",
            name_eng=f"Fake category {i}",
        )
        categories.append(c)
        created["categories"] += 1

        col = await Collection.create(
            name_uz=f"Fake kolleksiya {i}",
            name_ru=f"Фейк коллекция {i}",
            name_eng=f"Fake collection {i}",
        )
        collections.append(col)
        created["collections"] += 1

        clr = await Color.create(
            color_code=f"#AA{i:02d}{(i*7)%99:02d}",
        )
        colors.append(clr)
        created["colors"] += 1

        sz = await Size.create(name=f"{40 + i}")
        sizes.append(sz)
        created["sizes"] += 1

    for i in range(1, n + 1):
        p = await Product.create(
            category_id=categories[(i - 1) % len(categories)].id,
            collection_id=collections[(i - 1) % len(collections)].id,
            name_uz=f"Fake mahsulot {i}",
            name_ru=f"Фейк товар {i}",
            name_eng=f"Fake product {i}",
            description_uz=f"Fake tavsif {i}",
            description_ru=f"Фейк описание {i}",
            description_eng=f"Fake description {i}",
            price=100000 + (i * 10000),
            is_active=True,
            clothing_type=Product.ClothingType.MEN.value if i % 2 else Product.ClothingType.WOMEN.value,
        )
        products.append(p)
        created["products"] += 1

        await ProductDetail.create(
            product_id=p.id,
            name_uz=f"Detail UZ {i}",
            name_ru=f"Detail RU {i}",
            name_eng=f"Detail EN {i}",
        )
        created["product_details"] += 1

        await ProductItems.create(
            product_id=p.id,
            color_id=colors[(i - 1) % len(colors)].id,
            size_id=sizes[(i - 1) % len(sizes)].id,
            total_count=50 + i,
        )
        created["product_items"] += 1

    # ProductPhoto modeli UploadFile qabul qiladi, shu sababli fake seedda rasm yaratilmaydi.
    created["product_photos"] = 0

    payments = [Order.Payment.CLICK.value, Order.Payment.PAYME.value, Order.Payment.CASH.value]
    statuses = [
        Order.StatusOrder.NEW.value,
        Order.StatusOrder.PAID.value,
        Order.StatusOrder.IS_PROCESS.value,
    ]
    product_items = await ProductItems.all()

    for i in range(1, n + 1):
        order = await Order.create(
            first_name=f"Ali{i}",
            last_name=f"Valiyev{i}",
            company_name=None,
            country="Uzbekistan",
            address=f"Fake ko'cha {i}",
            town_city="Tashkent",
            payment=payments[(i - 1) % len(payments)],
            status=statuses[(i - 1) % len(statuses)],
            state_county=None,
            contact=f"+99890123{i:04d}",
            email_address=f"fake{i}@mail.uz",
            postcode_zip=100000 + i,
        )
        created["orders"] += 1

        item = product_items[(i - 1) % len(product_items)]
        product = products[(i - 1) % len(products)]
        count = (i % 3) + 1
        await OrderItem.create(
            product_id=product.id,
            product_item_id=item.id,
            order_id=order.id,
            count=count,
            volume=count,
            unit="dona",
            price=product.price,
            total=product.price * count,
        )
        created["order_items"] += 1

    await db.commit()
    return ok_response(
        {
            "message": "Fake data yaratildi",
            "clear_before": clear_before,
            "cleared": cleared,
            "created": created,
            "note": "Bu endpoint vaqtinchalik (dev) uchun.",
        }
    )


@system_router.delete("/dev/clear-fake", summary="DEV: fake/test ma'lumotlarni tozalash (super admin)")
async def clear_fake_data(
    _: bool = Depends(verify_super_admin_credentials),
):
    # FK cheklovlari uchun tozalash tartibi muhim.
    del_order_items = await db.execute(sqlalchemy_delete(OrderItem))
    del_orders = await db.execute(sqlalchemy_delete(Order))
    del_product_details = await db.execute(sqlalchemy_delete(ProductDetail))
    del_product_photos = await db.execute(sqlalchemy_delete(ProductPhoto))
    del_product_items = await db.execute(sqlalchemy_delete(ProductItems))
    del_products = await db.execute(sqlalchemy_delete(Product))
    del_sizes = await db.execute(sqlalchemy_delete(Size))
    del_colors = await db.execute(sqlalchemy_delete(Color))
    del_collections = await db.execute(sqlalchemy_delete(Collection))
    del_categories = await db.execute(sqlalchemy_delete(Category))
    await db.commit()

    return ok_response(
        {
            "message": "Fake/test data tozalandi",
            "cleared": {
                "order_items": int(del_order_items.rowcount or 0),
                "orders": int(del_orders.rowcount or 0),
                "product_details": int(del_product_details.rowcount or 0),
                "product_photos": int(del_product_photos.rowcount or 0),
                "product_items": int(del_product_items.rowcount or 0),
                "products": int(del_products.rowcount or 0),
                "sizes": int(del_sizes.rowcount or 0),
                "colors": int(del_colors.rowcount or 0),
                "collections": int(del_collections.rowcount or 0),
                "categories": int(del_categories.rowcount or 0),
            },
            "note": "Bu endpoint vaqtinchalik (dev) uchun.",
        }
    )
