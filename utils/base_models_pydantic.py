from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel



class ProductItemSchema(BaseModel):
    id: int
    product_id: int
    color_id: int
    size_id: int
    total_count: int


class ProductDetailSchema(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    name_eng: str


class ProductPhotoSchema(BaseModel):
    id: int
    product_id: int
    photo: str


class ProductList(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    name_eng: str
    description_uz: str
    description_ru: str
    description_eng: str

    category_id: int
    collection_id: int
    category_id: int

    photo: str
    is_active: bool
    price: int
    items: Optional[List[ProductItemSchema]] = None  # Prevent recursion
    details: Optional[List[ProductDetailSchema]] = None
    photos: Optional[List[ProductDetailSchema]] = None



class OrderItemsModel(BaseModel):
    id: int
    product_id: int
    product_item_id: int
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




class ListCategoryModel(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    shop_id: int
    photo: str
    is_active: bool
    products: Optional[List['ProductList']] = None

