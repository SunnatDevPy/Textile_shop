from enum import Enum

from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import ImageType
from sqlalchemy import Boolean, VARCHAR
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy_file import ImageField

from models.database import BaseModel


# class LanguageBanner(str, Enum):
#     UZ = 'uz'
#     RU = 'ru'
#     EN = 'en'
#
#
# language: Mapped[str] = mapped_column(SqlEnum(LanguageBanner), nullable=True)

class MainPhoto(BaseModel):
    photo: Mapped[ImageField] = mapped_column(ImageType(storage=FileSystemStorage('media/')), nullable=True)



class Country(BaseModel):
    name_uz: Mapped[str] = mapped_column(VARCHAR(255))
    name_ru: Mapped[str] = mapped_column(VARCHAR(255))
    name_en: Mapped[str] = mapped_column(VARCHAR(255))


class AdminUser(BaseModel):
    class StatusUser(str, Enum):
        ADMIN = 'admin'
        OPERATOR = 'operator'

    username: Mapped[str] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(SqlEnum(StatusUser), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean)

    def __str__(self):
        return super().__str__() + f" - {self.username}"
