"""Database indexes migration script."""
from sqlalchemy import text
from models import db
import asyncio


async def create_indexes():
    """Create performance indexes for frequently queried columns."""

    indexes = [
        # Products table indexes
        ("idx_products_category", "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)"),
        ("idx_products_collection", "CREATE INDEX IF NOT EXISTS idx_products_collection ON products(collection_id)"),
        ("idx_products_active", "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)"),
        ("idx_products_clothing_type", "CREATE INDEX IF NOT EXISTS idx_products_clothing_type ON products(clothing_type)"),
        ("idx_products_price", "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price)"),

        # Orders table indexes
        ("idx_orders_status", "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)"),
        ("idx_orders_payment", "CREATE INDEX IF NOT EXISTS idx_orders_payment ON orders(payment)"),
        ("idx_orders_created", "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC)"),
        ("idx_orders_contact", "CREATE INDEX IF NOT EXISTS idx_orders_contact ON orders(contact)"),
        ("idx_orders_first_name", "CREATE INDEX IF NOT EXISTS idx_orders_first_name ON orders(first_name)"),

        # Order items table indexes
        ("idx_order_items_order", "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)"),
        ("idx_order_items_product", "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)"),
        ("idx_order_items_product_item", "CREATE INDEX IF NOT EXISTS idx_order_items_product_item_id ON order_items(product_item_id)"),

        # Product items table indexes
        ("idx_product_items_product", "CREATE INDEX IF NOT EXISTS idx_product_items_product_id ON product_items(product_id)"),
        ("idx_product_items_color", "CREATE INDEX IF NOT EXISTS idx_product_items_color_id ON product_items(color_id)"),
        ("idx_product_items_size", "CREATE INDEX IF NOT EXISTS idx_product_items_size_id ON product_items(size_id)"),

        # Product photos table indexes
        ("idx_product_photos_product", "CREATE INDEX IF NOT EXISTS idx_product_photos_product_id ON product_photos(product_id)"),

        # Product details table indexes
        ("idx_product_details_product", "CREATE INDEX IF NOT EXISTS idx_product_details_product_id ON product_details(product_id)"),

        # Composite indexes for common queries
        ("idx_products_category_active", "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)"),
        ("idx_products_collection_active", "CREATE INDEX IF NOT EXISTS idx_products_collection_active ON products(collection_id, is_active)"),
        ("idx_orders_status_created", "CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at DESC)"),
    ]

    print("=" * 60)
    print("Creating database indexes...")
    print("=" * 60)

    success_count = 0
    error_count = 0

    for index_name, sql in indexes:
        try:
            await db.execute(text(sql))
            print(f"✅ {index_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {index_name}: {str(e)}")
            error_count += 1

    await db.commit()

    print("=" * 60)
    print(f"Completed: {success_count} success, {error_count} errors")
    print("=" * 60)


async def main():
    """Main function."""
    await create_indexes()
    await db.remove()


if __name__ == "__main__":
    asyncio.run(main())
