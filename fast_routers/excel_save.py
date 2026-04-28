import os
import tempfile
from io import BytesIO
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from fast_routers.admin_auth import require_admin
from models import AdminUser, Category, Collection, Product
from utils.audit import write_audit_log

excel_router = APIRouter(prefix="/excel", tags=["Excel"])


@excel_router.get(
    "/products/template",
    summary="Product import uchun Excel shablonini yuklab olish",
)
async def download_products_import_template(
    _: Annotated[AdminUser, Depends(require_admin)],
):
    df = pd.DataFrame(
        [
            {
                "id": "",
                "category_id": 1,
                "collection_id": 1,
                "name_uz": "Mahsulot nomi UZ",
                "name_ru": "Название RU",
                "name_eng": "Product name EN",
                "description_uz": "Tavsif UZ",
                "description_ru": "Описание RU",
                "description_eng": "Description EN",
                "price": 100000,
                "is_active": True,
            }
        ]
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="products")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=products_import_template.xlsx"},
    )


@excel_router.post(
    "/products/import",
    summary="Excel orqali product create/update qilish (admin)",
)
async def import_products_from_excel(
    user: Annotated[AdminUser, Depends(require_admin)],
    excel_file: UploadFile = File(...),
):
    if not excel_file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fayl topilmadi")

    suffix = ".xlsx" if excel_file.filename.lower().endswith(".xlsx") else ".xls"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            tmp.write(await excel_file.read())

        df = pd.read_excel(tmp_path)

        required_cols = {
            "category_id",
            "collection_id",
            "name_uz",
            "name_ru",
            "name_eng",
            "description_uz",
            "description_ru",
            "description_eng",
            "price",
            "is_active",
        }
        missing = required_cols - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Excelda ustunlar yetishmaydi: {', '.join(sorted(missing))}",
            )

        created = 0
        updated = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                category_id = int(row["category_id"])
                collection_id = int(row["collection_id"])
                category = await Category.get_or_none(category_id)
                collection = await Collection.get_or_none(collection_id)
                if not category:
                    raise ValueError(f"category_id topilmadi: {category_id}")
                if not collection:
                    raise ValueError(f"collection_id topilmadi: {collection_id}")

                payload = {
                    "category_id": category_id,
                    "collection_id": collection_id,
                    "name_uz": str(row["name_uz"]).strip(),
                    "name_ru": str(row["name_ru"]).strip(),
                    "name_eng": str(row["name_eng"]).strip(),
                    "description_uz": str(row["description_uz"]).strip(),
                    "description_ru": str(row["description_ru"]).strip(),
                    "description_eng": str(row["description_eng"]).strip(),
                    "price": int(row["price"]),
                    "is_active": bool(row["is_active"]),
                }

                product_id = row.get("id")
                if pd.notna(product_id):
                    existing = await Product.get_or_none(int(product_id))
                else:
                    existing = None

                if existing:
                    await Product.update(existing.id, **payload)
                    updated += 1
                    await write_audit_log(
                        entity="product",
                        entity_id=existing.id,
                        action="excel_update",
                        actor=user.username,
                        details="Excel orqali yangilandi",
                    )
                else:
                    created_obj = await Product.create(**payload)
                    created += 1
                    await write_audit_log(
                        entity="product",
                        entity_id=created_obj.id,
                        action="excel_create",
                        actor=user.username,
                        details="Excel orqali yaratildi",
                    )
            except Exception as exc:
                errors.append({"row": int(idx) + 2, "error": str(exc)})

        return {
            "ok": True,
            "created": created,
            "updated": updated,
            "errors_count": len(errors),
            "errors": errors[:100],
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
