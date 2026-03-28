from enum import Enum

from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import ImageType, FileType
from sqlalchemy import Boolean, select
from sqlalchemy import ForeignKey, BIGINT, Enum as SqlEnum
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy_file import ImageField, FileField

from models.database import BaseModel, db, CreatedBaseModel


class MainPhoto(BaseModel):
    class LanguageBanner(str, Enum):
        UZ = 'uz'
        RU = 'ru'

    photo: Mapped[ImageField] = mapped_column(ImageType(storage=FileSystemStorage('media/')), nullable=True)
    language: Mapped[str] = mapped_column(SqlEnum(LanguageBanner), nullable=True)


class MainVideo(BaseModel):
    class LanguageBanner(str, Enum):
        UZ = 'uz'
        RU = 'ru'

    video: Mapped[FileField] = mapped_column(FileType(storage=FileSystemStorage('media/')), nullable=True)
    language: Mapped[str] = mapped_column(SqlEnum(LanguageBanner), nullable=True)


class BotUser(BaseModel):
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    contact: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="False")

    def __str__(self):
        return super().__str__() + f" - {self.username}"


class AdminPanelUser(BaseModel):
    class StatusUser(str, Enum):
        ADMIN = 'admin'
        MODERATOR = 'moderator'
        CALL_CENTER = 'call center'

    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(SqlEnum(StatusUser), nullable=True)
    contact: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean)

    def __str__(self):
        return super().__str__() + f" - {self.username}"


class MyAddress(BaseModel):
    bot_user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("bot_users.id", ondelete='CASCADE'))
    address: Mapped[str] = mapped_column(String, nullable=True)
    lat: Mapped[float] = mapped_column(nullable=True)
    long: Mapped[float] = mapped_column(nullable=True)


class Cart(BaseModel):
    bot_user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("bot_users.id", ondelete='CASCADE'))
    product_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("shop_products.id", ondelete='CASCADE'))
    shop_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('shops.id', ondelete="CASCADE"))
    tip_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("product_tips.id", ondelete='CASCADE'))
    count: Mapped[int] = mapped_column()
    total: Mapped[int]
    product_in_cart: Mapped['ShopProduct'] = relationship('ShopProduct', lazy='selectin', back_populates='carts')
    tip: Mapped['ProductTip'] = relationship('ProductTip', lazy='selectin', back_populates='cart')


class Order(CreatedBaseModel):
    class StatusOrder(str, Enum):
        NEW = "yangi"
        IS_PROCESS = "jarayonda"
        READY = "tayyor"
        IN_PROGRESS = "yetkazilmoqda"
        DELIVERED = "yetkazildi"
        CANCELLED = "bekor qilindi"

    class Payment(str, Enum):
        CASH = "naqt"
        TERMINAL = "karta"

    payment: Mapped[bool] = mapped_column(SqlEnum(Payment), default=Payment.CASH.value)
    status: Mapped[str] = mapped_column(SqlEnum(StatusOrder))

    bot_user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('bot_users.id', ondelete='CASCADE'))
    address: Mapped[str] = mapped_column(String)
    shop_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('shops.id', ondelete="CASCADE"))
    first_last_name: Mapped[str] = mapped_column(String)
    contact: Mapped[str] = mapped_column(String)
    driver_price: Mapped[int] = mapped_column(BIGINT, default=0)
    total_sum: Mapped[int] = mapped_column(BIGINT)
    lat: Mapped[float]
    long: Mapped[float]
    order_items: Mapped[list['OrderItem']] = relationship('OrderItem', lazy='selectin', back_populates='order')

    @classmethod
    async def get_from_bot_user_in_type(cls, user_id, status):
        return ((await db.execute(
            select(cls).where(cls.bot_user_id == user_id, cls.status == status))).scalars().all())

    @classmethod
    async def get_from_bot_user_in_type_and_shop(cls, user_id, status, shop_id):
        return (await db.execute(select(cls).where(cls.bot_user_id == user_id, cls.status == status,
                                                   cls.shop_id == shop_id))).scalars().all()


class OrderItem(BaseModel):
    product_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("shop_products.id", ondelete='CASCADE'))
    order_id: Mapped[int] = mapped_column(BIGINT, ForeignKey(Order.id, ondelete='CASCADE'))
    count: Mapped[int] = mapped_column(default=1)
    volume: Mapped[int]
    unit: Mapped[str]
    price: Mapped[int]
    total: Mapped[int]
    order: Mapped['Order'] = relationship('Order', back_populates='order_items')
    product: Mapped['ShopProduct'] = relationship('ShopProduct', lazy='selectin', back_populates='order_item')


class ProjectAllStatus(BaseModel):
    day_and_night: Mapped[bool] = mapped_column(Boolean, default=False)


class CallOrder(CreatedBaseModel):
    class StatusOrder(str, Enum):
        NEW = "yangi"
        IS_GOING = "yig'ilmoqda"
        IN_PROGRESS = "yetkazilmoqda"
        DELIVERED = "yetkazildi"
        CANCELLED = "bekor qilindi"

    class Payment(str, Enum):
        CASH = "naqt"
        TERMINAL = "karta"

    payment: Mapped[bool] = mapped_column(SqlEnum(Payment), default=Payment.CASH.value)
    status: Mapped[str] = mapped_column(SqlEnum(StatusOrder))

    bot_user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('bot_users.id', ondelete='CASCADE'))
    call_user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('admin_panel_users.id', ondelete='CASCADE'))
    address: Mapped[str] = mapped_column(String)
    shop_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('shops.id', ondelete="CASCADE"))
    first_last_name: Mapped[str] = mapped_column(String)
    contact: Mapped[str] = mapped_column(String)
    driver_price: Mapped[int] = mapped_column(BIGINT, default=0)
    total_sum: Mapped[int] = mapped_column(BIGINT)
    lat: Mapped[float]
    long: Mapped[float]
    order_items: Mapped[list['CallOrderItem']] = relationship('CallOrderItem', lazy='selectin', back_populates='order')

    @classmethod
    async def get_from_bot_user_in_type(cls, user_id, status):
        return ((await db.execute(
            select(cls).where(cls.call_user_id == user_id, cls.status == status))).scalars().all())

    @classmethod
    async def get_from_bot_user_in_type_and_shop(cls, user_id, status, shop_id):
        return (await db.execute(select(cls).where(cls.call_user_id == user_id, cls.status == status,
                                                   cls.shop_id == shop_id))).scalars().all()


class CallOrderItem(BaseModel):
    product_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("shop_products.id", ondelete='CASCADE'))
    order_id: Mapped[int] = mapped_column(BIGINT, ForeignKey(CallOrder.id, ondelete='CASCADE'))
    count: Mapped[int] = mapped_column(default=1)
    volume: Mapped[int]
    unit: Mapped[str]
    price: Mapped[int]
    total: Mapped[int]
    order: Mapped['CallOrder'] = relationship('CallOrder', back_populates='order_items')
    product: Mapped['ShopProduct'] = relationship('ShopProduct', lazy='selectin', back_populates='call_order_item')
