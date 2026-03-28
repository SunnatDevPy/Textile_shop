from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import ImageType
from sqlalchemy import BigInteger, String, VARCHAR, ForeignKey, select, BIGINT, update as sqlalchemy_update
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy_file import ImageField

from models.database import BaseModel, db


class ShopCategory(BaseModel):
    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    shop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shops.id', ondelete='CASCADE'))
    parent_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shop_categories.id', ondelete='CASCADE'),
                                           nullable=True)
    photo: Mapped[ImageField] = mapped_column(ImageType(storage=FileSystemStorage('media/')))
    is_active: Mapped[bool]

    @classmethod
    async def get_shop_categories(cls, id_):
        query = select(cls).filter(cls.shop_id == id_)
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def get_from_shop(cls, shop_id, category_id):
        query = select(cls).filter(cls.shop_id == shop_id, cls.id == category_id)
        return (await db.execute(query)).scalars().all()


class ShopProduct(BaseModel):
    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    description_uz: Mapped[str] = mapped_column(String(255))
    description_ru: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('admin_panel_users.id', ondelete='CASCADE'))
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(ShopCategory.id, ondelete='CASCADE'))
    photo: Mapped[ImageField] = mapped_column(ImageType(storage=FileSystemStorage('media/')), nullable=True)
    shop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shops.id', ondelete='CASCADE'))
    is_active: Mapped[bool]
    price: Mapped[int] = mapped_column(BigInteger)
    volume: Mapped[int]
    unit: Mapped[str]
    tips: Mapped[list['ProductTip']] = relationship('ProductTip', lazy='selectin', back_populates='product')

    love_products: Mapped[list['LoveProducts']] = relationship('LoveProducts', back_populates='product')
    carts: Mapped[list['Cart']] = relationship('Cart', back_populates='product_in_cart')
    order_item: Mapped[list['OrderItem']] = relationship('OrderItem', back_populates='product')
    call_order_item: Mapped['CallOrderItem'] = relationship('CallOrderItem', lazy='selectin', back_populates='product')

    @classmethod
    async def get_products_category(cls, category_id):
        query = select(cls).filter(cls.category_id == category_id)
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def get_products_from_shop(cls, shop_id):
        query = select(cls).filter(cls.shop_id == shop_id)
        return (await db.execute(query)).scalars().all()


class ProductTip(BaseModel):
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shop_products.id', ondelete='CASCADE'))
    price: Mapped[int] = mapped_column(BigInteger)
    volume: Mapped[int]
    unit: Mapped[str] = mapped_column(String, nullable=False)
    product: Mapped['ShopProduct'] = relationship('ShopProduct', back_populates='tips')
    cart: Mapped[list['Cart']] = relationship('Cart', back_populates='tip')

    @classmethod
    async def get_product_tips(cls, id_):
        query = select(cls).filter(cls.product_id == id_)
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def get_product_and_tip(cls, id_, tip_id):
        query = select(cls).filter(cls.product_id == id_, cls.id == tip_id)
        return (await db.execute(query)).scalar()


class LoveProducts(BaseModel):
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shop_products.id', ondelete='CASCADE'))
    shop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shops.id', ondelete='CASCADE'))
    bot_user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('bot_users.id', ondelete='CASCADE'))
    product: Mapped['ShopProduct'] = relationship('ShopProduct', lazy='selectin', back_populates='love_products')
    is_active: Mapped[bool]

    @classmethod
    async def update_all_active(cls, id_, is_active):
        query = (
            sqlalchemy_update(cls)
            .where(cls.id == id_)
            .values(is_active=is_active)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await cls.commit()
