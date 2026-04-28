from enum import Enum

from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import ImageType
from sqlalchemy import BigInteger, String, VARCHAR, ForeignKey, select, Enum as SqlEnum, BIGINT
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy_file import ImageField

from models.database import BaseModel, db, CreatedBaseModel


class Category(BaseModel):
    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    name_eng: Mapped[str] = mapped_column(VARCHAR(255))
    products: Mapped[list['Product']] = relationship('Product', lazy='selectin',
                                                               back_populates='category')


class Collection(BaseModel):
    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    name_eng: Mapped[str] = mapped_column(VARCHAR(255))
    products: Mapped[list['Product']] = relationship('Product', lazy='selectin',
                                                     back_populates='collection')

class Color(BaseModel):
    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    name_eng: Mapped[str] = mapped_column(VARCHAR(255))


class Size(BaseModel):
    name: Mapped[str] = mapped_column(VARCHAR(255))


class Product(BaseModel):
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id", ondelete='CASCADE'))
    collection_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("collections.id", ondelete='CASCADE'))

    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    name_eng: Mapped[str] = mapped_column(VARCHAR(255))

    description_uz: Mapped[str] = mapped_column(String(255))
    description_ru: Mapped[str] = mapped_column(String(255))
    description_eng: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool]

    price: Mapped[int] = mapped_column(BigInteger)

    product_items: Mapped[list['ProductItems']] = relationship('ProductItems', lazy='selectin',back_populates='product')
    product_details: Mapped[list['ProductDetail']] = relationship('ProductDetail', lazy='selectin',back_populates='product')
    product_photos: Mapped['ProductPhoto'] = relationship('ProductPhoto', lazy='selectin', back_populates='product')

    order_items: Mapped[list['OrderItem']] = relationship('OrderItem', back_populates='product')
    category: Mapped['Category'] = relationship('Category', back_populates='products')
    collection: Mapped['Collection'] = relationship('Collection', back_populates='products')

    @classmethod
    async def get_products_category(cls, category_id):
        query = select(cls).where(cls.category_id == category_id)
        return (await db.execute(query)).scalars().all()


class ProductDetail(BaseModel):
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE")
    )

    name_uz: Mapped[str] = mapped_column(String(255))
    name_ru: Mapped[str] = mapped_column(String(255))
    name_eng: Mapped[str] = mapped_column(String(255))

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="product_details",
    )

class ProductItems(BaseModel):
    __tablename__ = "product_items"

    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('products.id', ondelete='CASCADE'))
    color_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("colors.id", ondelete='CASCADE'))
    size_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sizes.id", ondelete='CASCADE'))

    total_count: Mapped[int]
    product: Mapped['Product'] = relationship('Product', back_populates='product_items')
    order_lines: Mapped[list['OrderItem']] = relationship('OrderItem', back_populates='product_item')

    @classmethod
    async def get_product_items(cls, id_):
        query = select(cls).where(cls.product_id == id_)
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def get_product_and_item(cls, id_, item_id):
        query = select(cls).where(cls.product_id == id_, cls.id == item_id)
        return (await db.execute(query)).scalar()


class ProductPhoto(BaseModel):
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('products.id', ondelete='CASCADE'))
    photo: Mapped[ImageField] = mapped_column(ImageType(storage=FileSystemStorage('media/')), nullable=True)
    product: Mapped['Product'] = relationship('Product', back_populates='product_photos')


class Order(CreatedBaseModel):
    class StatusOrder(str, Enum):
        NEW = "yangi"
        PAID = "to'landi"
        IS_PROCESS = "jarayonda"
        READY = "tayyor"
        IN_PROGRESS = "yetkazilmoqda"
        DELIVERED = "yetkazildi"
        CANCELLED = "bekor qilindi"

    class Payment(str, Enum):
        CLICK = "click"
        PAYME = "payme"
        CASH = "cash"

    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    company_name: Mapped[bool] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    town_city: Mapped[str] = mapped_column(String)
    payment: Mapped[bool] = mapped_column(SqlEnum(Payment), default=Payment.CLICK.value)
    status: Mapped[str] = mapped_column(SqlEnum(StatusOrder))
    state_county: Mapped[str] = mapped_column(String, nullable=True)
    contact: Mapped[str] = mapped_column(String)
    email_address: Mapped[str] = mapped_column(String, nullable=True)
    postcode_zip: Mapped[int]

    order_items: Mapped[list['OrderItem']] = relationship('OrderItem', lazy='selectin', back_populates='order')


class OrderItem(BaseModel):
    product_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("products.id", ondelete='CASCADE'))
    product_item_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("product_items.id", ondelete='RESTRICT'))
    order_id: Mapped[int] = mapped_column(BIGINT, ForeignKey(Order.id, ondelete='CASCADE'))
    count: Mapped[int] = mapped_column(default=1)
    volume: Mapped[int]
    unit: Mapped[str]
    price: Mapped[int]
    total: Mapped[int]
    order: Mapped['Order'] = relationship('Order', back_populates='order_items')
    product: Mapped['Product'] = relationship('Product', lazy='selectin', back_populates='order_items')
    product_item: Mapped['ProductItems'] = relationship('ProductItems', lazy='selectin')
