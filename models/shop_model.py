from enum import Enum

from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import ImageType
from sqlalchemy import BigInteger, Enum as SqlEnum, VARCHAR, ForeignKey, select, desc, Integer, JSON, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy_file import ImageField

from models.database import BaseModel, db


class Shop(BaseModel):
    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('admin_panel_users.id', ondelete='CASCADE'),
                                          nullable=True)
    lat: Mapped[float]
    long: Mapped[float]
    address: Mapped[str]
    order_group_id: Mapped[int] = mapped_column(BigInteger)
    cart_number: Mapped[int] = mapped_column(BigInteger)
    photo: Mapped[ImageField] = mapped_column(ImageType(storage=FileSystemStorage('media/')))
    is_active: Mapped[bool] = mapped_column(nullable=False)
    work: Mapped[list['WorkTimes']] = relationship('WorkTimes', lazy='selectin', back_populates='shop')


class WorkTimes(BaseModel):
    shop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shops.id', ondelete='CASCADE'))
    open_time: Mapped[str]
    close_time: Mapped[str]
    weeks: Mapped[list] = mapped_column(JSON)
    shop: Mapped[list['Shop']] = relationship('Shop', lazy='selectin', back_populates='work')


class CallCenters(BaseModel):
    shop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shops.id', ondelete='CASCADE'))
    contact: Mapped[str]


