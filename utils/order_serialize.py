"""Buyurtma va qatorlarini frontend/admin uchun yagona JSON formatda qaytarish."""

from typing import Any, Optional

from models import Order, OrderItem
from utils.order_status import (
    order_workflow_status,
    payment_method_value,
    payment_status_value,
)


def _product_brief(product) -> Optional[dict[str, Any]]:
    if product is None:
        return None
    return {
        "id": product.id,
        "name_uz": getattr(product, "name_uz", None),
        "name_ru": getattr(product, "name_ru", None),
        "name_eng": getattr(product, "name_eng", None),
        "price": int(getattr(product, "price", 0) or 0),
        "is_active": bool(getattr(product, "is_active", True)),
    }


def serialize_order_item(item: OrderItem) -> dict[str, Any]:
    product_item = getattr(item, "product_item", None)
    return {
        "id": item.id,
        "order_id": item.order_id,
        "product_id": item.product_id,
        "product_item_id": item.product_item_id,
        "count": item.count,
        "volume": item.volume,
        "unit": item.unit,
        "price": int(item.price or 0),
        "total": int(item.total or 0),
        "product": _product_brief(getattr(item, "product", None)),
        "product_item": (
            {
                "id": product_item.id,
                "color_id": product_item.color_id,
                "size_id": product_item.size_id,
            }
            if product_item is not None
            else None
        ),
    }


def serialize_order(order: Order, *, include_items: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": order.id,
        "first_name": order.first_name,
        "last_name": order.last_name,
        "company_name": order.company_name,
        "country": order.country,
        "address": order.address,
        "town_city": order.town_city,
        "state_county": order.state_county,
        "contact": order.contact,
        "email_address": order.email_address,
        "postcode_zip": order.postcode_zip,
        "payment": payment_method_value(order),
        "payment_status": payment_status_value(order),
        "status": order_workflow_status(order),
        "total_sum": int(getattr(order, "total_sum", 0) or 0),
        "created_at": getattr(order, "created_at", None),
        "updated_at": getattr(order, "updated_at", None),
    }
    if include_items:
        items = [serialize_order_item(oi) for oi in (getattr(order, "order_items", None) or [])]
        data["order_items"] = items
        data["products"] = items
    return data


def serialize_orders(orders: list[Order], *, include_items: bool = True) -> list[dict[str, Any]]:
    return [serialize_order(order, include_items=include_items) for order in orders]
