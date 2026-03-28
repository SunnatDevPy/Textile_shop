from typing import Optional, Annotated

import aiofiles
import pandas as pd
from fastapi import APIRouter, UploadFile, File
from fastapi import Response
from fastapi.params import Depends
from pydantic import BaseModel
from starlette import status
from fast_routers.jwt_ import get_current_user
from models import AdminPanelUser, ShopProduct, ShopCategory, Shop, ProductTip

excel_router = APIRouter(prefix='/excel', tags=['Excel'])


class UserId(BaseModel):
    id: Optional[int] = None


@excel_router.post("/product", name="Create or Update Product")
async def upload_excel(user: Annotated[UserId, Depends(get_current_user)], excel_file: UploadFile = File(...)):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    if user is None:
        return Response("Item not found", status.HTTP_404_NOT_FOUND)

    if user.status not in ['moderator', 'admin', 'superuser']:
        return Response("Item not found", status.HTTP_404_NOT_FOUND)
    file_path = f"temp_{user.id}.xlsx"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await excel_file.read())

    df = pd.read_excel(file_path)

    new_products = []
    new_update = []

    error = 0
    errors_ids = []
    for _, row in df.iterrows():
        try:
            category_id = row.get("category_id")
            if category_id:
                try:
                    category = await ShopCategory.get(int(category_id))
                except:
                    category = None
            else:
                category = None

            shop_id = row.get("shop_id")
            if shop_id:
                try:
                    shop = await Shop.get(int(shop_id))
                except:
                    shop = None
            else:
                shop = None

            if category and shop:  # Если есть category_id → это товар
                product_data = {
                    "category_id": category.id,
                    "name_uz": row.get("name_uz"),
                    "name_ru": row.get("name_ru"),
                    "description_uz": row["description_uz"],
                    "description_ru": row["description_ru"],
                    "shop_id": shop.id,
                    "price": row.get("price", 0),
                    "volume": row.get("volume"),
                    "unit": row.get("unit", ""),
                }

                existing_product: ShopProduct = await ShopProduct.get(int(row["id"]))
                if existing_product:
                    await ShopProduct.update(existing_product.id, **product_data)
                    new_update.append(product_data)
                else:
                    product_data["id"] = int(row["id"])
                    new_products.append(ShopProduct.create(**product_data))

            else:
                errors_ids.append(row)
                error += 1

        except Exception as e:
            print(f"Ошибка при обработке строки {row['id']}: {e}")

    return {
        "message": "Fayl yuklandi",
        "error": error,
        "errors": errors_ids,
        "new_product": new_products,
        "update_product": new_update
    }


@excel_router.post(path='/tips', name="Create or Update Product tips")
async def list_category_shop(user: Annotated[UserId, Depends(get_current_user)], excel_file: UploadFile = File()):
    user: AdminPanelUser = await AdminPanelUser.get(user.id)
    if user is None:
        return Response("Item not found", status.HTTP_404_NOT_FOUND)

    if user.status not in ['moderator', 'admin', 'superuser']:
        return Response("Item not found", status.HTTP_404_NOT_FOUND)
    file_path = f"temp_{user.id}.xlsx"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await excel_file.read())

    df = pd.read_excel(file_path)

    new_product_tips = []
    new_update = []

    error = 0
    errors_ids = []
    for _, row in df.iterrows():
        try:
            product_id = row.get("product_id")
            if product_id:
                try:
                    product = await ShopProduct.get(int(product_id))
                except:
                    product = None
            else:
                product = None

            if product:
                product_data = {
                    "product_id": product.id,
                    "price": row.get("price", 0),
                    "volume": row.get("volume"),
                    "unit": row.get("unit", ""),
                }

                existing_product: ProductTip = await ProductTip.get(int(row["id"]))
                if existing_product:
                    await ProductTip.update(existing_product.id, **product_data)
                    new_update.append(product_data)
                else:
                    product_data["id"] = int(row["id"])
                    new_product_tips.append(ProductTip.create(**product_data))

            else:
                errors_ids.append(row)
                error += 1

        except Exception as e:
            print(f"Ошибка при обработке строки {row['id']}: {e}")

    return {
        "message": "Fayl yuklandi",
        "error": error,
        "errors": errors_ids,
        "new_product": new_product_tips,
        "update_product": new_update
    }
