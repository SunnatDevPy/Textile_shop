from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class WorkModel(BaseModel):
    id: int
    shop_id: int
    open_time: str
    close_time: str
    weeks: list


class ListShopsModel(BaseModel):
    id: Optional[int]
    owner_id: Optional[int]
    name_uz: Optional[str]
    name_ru: Optional[str]
    lat: Optional[float]
    long: Optional[float]
    address: Optional[str] = None
    order_group_id: Optional[int] = None
    cart_number: Optional[int] = None
    photo: Optional[str] = None
    is_active: Optional[bool] = None
    work: Optional[List[WorkModel]] = None


class ProductTipSchema(BaseModel):
    id: int
    price: int
    volume: int
    unit: str


class ProductList(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    description_uz: str
    description_ru: str
    owner_id: int
    category_id: int
    photo: str
    shop_id: int
    is_active: bool
    price: int
    volume: int
    unit: str
    tips: Optional[List[ProductTipSchema]] = None  # Prevent recursion


class OrderItemsModel(BaseModel):
    id: int
    product_id: int
    order_id: int
    count: int
    volume: int
    unit: str
    price: int
    total: int
    product: Optional[ProductList] = None


class OrderModel(BaseModel):
    id: int
    payment: str
    status: str
    bot_user_id: int
    address: str
    shop_id: int
    first_last_name: str
    contact: str
    driver_price: int
    total_sum: int
    lat: float
    long: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    order_items: Optional[list[OrderItemsModel]] = None


class FavouritesSchema(BaseModel):
    id: int
    product_id: int
    shop_id: int
    bot_user_id: int
    product: Optional[ProductList] = None
    is_active: Optional[bool] = None


class CartModel(BaseModel):
    id: int
    bot_user_id: int
    product_id: int
    shop_id: int
    tip_id: int
    count: int
    total: int
    product_in_cart: Optional[ProductList] = None
    tip: Optional[ProductTipSchema] = None


class ListCategoryModel(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    shop_id: int
    photo: str
    is_active: bool
    products: Optional[List['ProductList']] = None


class ListShopsModelAll(BaseModel):
    id: Optional[int]
    owner_id: Optional[int]
    name_uz: Optional[str]
    name_ru: Optional[str]
    lat: Optional[float]
    long: Optional[float]
    address: Optional[str] = None
    order_group_id: Optional[int] = None
    cart_number: Optional[int] = None
    photo: Optional[str] = None
    is_active: Optional[bool] = None
    work: Optional[List[WorkModel]] = None
    category: Optional[List['ListCategoryModel']] = None
