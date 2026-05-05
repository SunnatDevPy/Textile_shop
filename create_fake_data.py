"""Generate fake data for testing the Textile Shop application."""
import asyncio
import random
from datetime import datetime, timedelta
from models import db, Category, Collection, Color, Size, Product, ProductItems, Order, OrderItem, AdminUser
from utils.logger import logger


async def create_fake_data():
    """Create fake data for testing."""

    logger.info("Starting fake data generation...")

    # 1. Categories
    categories_data = [
        {"name_uz": "Ko'ylak", "name_ru": "Рубашка", "name_eng": "Shirt"},
        {"name_uz": "Shim", "name_ru": "Брюки", "name_eng": "Pants"},
        {"name_uz": "Futbolka", "name_ru": "Футболка", "name_eng": "T-Shirt"},
        {"name_uz": "Kurtka", "name_ru": "Куртка", "name_eng": "Jacket"},
        {"name_uz": "Ko'ylak (ayollar)", "name_ru": "Платье", "name_eng": "Dress"},
    ]

    categories = []
    for cat_data in categories_data:
        category = Category(**cat_data)
        db.add(category)
        categories.append(category)

    await db.flush()
    logger.info(f"✅ Created {len(categories)} categories")

    # 2. Collections
    collections_data = [
        {"name_uz": "Bahor 2026", "name_ru": "Весна 2026", "name_eng": "Spring 2026"},
        {"name_uz": "Yoz 2026", "name_ru": "Лето 2026", "name_eng": "Summer 2026"},
        {"name_uz": "Kuz 2026", "name_ru": "Осень 2026", "name_eng": "Autumn 2026"},
        {"name_uz": "Qish 2026", "name_ru": "Зима 2026", "name_eng": "Winter 2026"},
        {"name_uz": "Premium", "name_ru": "Премиум", "name_eng": "Premium"},
    ]

    collections = []
    for col_data in collections_data:
        collection = Collection(**col_data)
        db.add(collection)
        collections.append(collection)

    await db.flush()
    logger.info(f"✅ Created {len(collections)} collections")

    # 3. Colors
    colors_data = [
        {"color_code": "#FFFFFF"},  # Oq
        {"color_code": "#000000"},  # Qora
        {"color_code": "#FF0000"},  # Qizil
        {"color_code": "#0000FF"},  # Ko'k
        {"color_code": "#00FF00"},  # Yashil
        {"color_code": "#FFFF00"},  # Sariq
        {"color_code": "#FFA500"},  # To'q sariq
        {"color_code": "#800080"},  # Binafsha
        {"color_code": "#808080"},  # Kulrang
        {"color_code": "#A52A2A"},  # Jigarrang
    ]

    colors = []
    for color_data in colors_data:
        color = Color(**color_data)
        db.add(color)
        colors.append(color)

    await db.flush()
    logger.info(f"✅ Created {len(colors)} colors")

    # 4. Sizes
    sizes_data = [
        {"name": "XS"},
        {"name": "S"},
        {"name": "M"},
        {"name": "L"},
        {"name": "XL"},
        {"name": "XXL"},
        {"name": "XXXL"},
    ]

    sizes = []
    for size_data in sizes_data:
        size = Size(**size_data)
        db.add(size)
        sizes.append(size)

    await db.flush()
    logger.info(f"✅ Created {len(sizes)} sizes")

    # 5. Products
    products = []
    for i in range(50):
        category = random.choice(categories)
        collection = random.choice(collections)
        clothing_type = random.choice(["erkak", "ayol", "unisex"])

        product = Product(
            category_id=category.id,
            collection_id=collection.id,
            name_uz=f"Mahsulot {i+1}",
            name_ru=f"Продукт {i+1}",
            name_eng=f"Product {i+1}",
            description_uz=f"Bu {i+1}-mahsulot tavsifi",
            description_ru=f"Это описание продукта {i+1}",
            description_eng=f"This is product {i+1} description",
            is_active=random.choice([True, True, True, False]),  # 75% active
            clothing_type=clothing_type,
            price=random.randint(50000, 500000)
        )
        db.add(product)
        products.append(product)

    await db.flush()
    logger.info(f"✅ Created {len(products)} products")

    # 6. Product Items (variants)
    product_items = []
    for product in products:
        # Har bir mahsulot uchun 3-8 ta variant
        num_variants = random.randint(3, 8)
        for _ in range(num_variants):
            color = random.choice(colors)
            size = random.choice(sizes)

            product_item = ProductItems(
                product_id=product.id,
                color_id=color.id,
                size_id=size.id,
                total_count=random.randint(0, 100),
                min_stock_level=random.randint(5, 15)
            )
            db.add(product_item)
            product_items.append(product_item)

    await db.flush()
    logger.info(f"✅ Created {len(product_items)} product items")

    # 7. Orders
    orders = []
    payment_types = [Order.Payment.CLICK, Order.Payment.PAYME, Order.Payment.CASH]
    statuses = [
        Order.StatusOrder.NEW,
        Order.StatusOrder.PAID,
        Order.StatusOrder.IS_PROCESS,
        Order.StatusOrder.READY,
        Order.StatusOrder.IN_PROGRESS,
        Order.StatusOrder.DELIVERED,
        Order.StatusOrder.CANCELLED,
        Order.StatusOrder.RETURNED
    ]

    # So'nggi 90 kun uchun buyurtmalar
    for i in range(200):
        # Random sana (so'nggi 90 kun ichida)
        days_ago = random.randint(0, 90)
        created_at = datetime.now() - timedelta(days=days_ago)

        # Status va to'lov turini tanlash
        status = random.choice(statuses)

        # Yangi buyurtmalar to'lanmagan
        if status == Order.StatusOrder.NEW:
            payment = Order.Payment.CASH  # Default
        else:
            payment = random.choice(payment_types)

        order = Order(
            first_name=f"Ism{i+1}",
            last_name=f"Familiya{i+1}",
            company_name=f"Kompaniya {i+1}" if random.random() > 0.7 else None,
            country="Uzbekistan",
            address=f"Manzil {i+1}, ko'cha {random.randint(1, 100)}",
            town_city=random.choice(["Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona"]),
            payment=payment.value,
            status=status.value,
            state_county=random.choice(["Toshkent viloyati", "Samarqand viloyati", None]),
            contact=f"+998{random.randint(90, 99)}{random.randint(1000000, 9999999)}",
            email_address=f"user{i+1}@example.com" if random.random() > 0.5 else None,
            postcode_zip=random.randint(100000, 999999),
            created_at=created_at
        )
        db.add(order)
        orders.append(order)

    await db.flush()
    logger.info(f"✅ Created {len(orders)} orders")

    # 8. Order Items
    order_items_list = []
    for order in orders:
        # Har bir buyurtmada 1-5 ta mahsulot
        num_items = random.randint(1, 5)
        for _ in range(num_items):
            product_item = random.choice(product_items)
            product = next(p for p in products if p.id == product_item.product_id)

            count = random.randint(1, 3)
            price = product.price
            total = price * count

            order_item = OrderItem(
                product_id=product.id,
                product_item_id=product_item.id,
                order_id=order.id,
                count=count,
                volume=1,
                unit="dona",
                price=price,
                total=total
            )
            db.add(order_item)
            order_items_list.append(order_item)

    await db.flush()
    logger.info(f"✅ Created {len(order_items_list)} order items")

    # Commit all changes
    await db.commit()

    logger.info("=" * 60)
    logger.info("✅ Fake data generation completed successfully!")
    logger.info("=" * 60)
    logger.info(f"Categories: {len(categories)}")
    logger.info(f"Collections: {len(collections)}")
    logger.info(f"Colors: {len(colors)}")
    logger.info(f"Sizes: {len(sizes)}")
    logger.info(f"Products: {len(products)}")
    logger.info(f"Product Items: {len(product_items)}")
    logger.info(f"Orders: {len(orders)}")
    logger.info(f"Order Items: {len(order_items_list)}")
    logger.info("=" * 60)


async def main():
    """Main function."""
    try:
        await create_fake_data()
    except Exception as e:
        logger.error(f"Error generating fake data: {str(e)}")
        raise
    finally:
        await db.remove()


if __name__ == "__main__":
    asyncio.run(main())
