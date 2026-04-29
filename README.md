# Textile Shop API (FastAPI)

Ushbu loyiha `Textile Shop` uchun backend API.

- Stack: `FastAPI + PostgreSQL + SQLAlchemy (async)`
- Swagger: `/docs`
- Admin panel UI: `/admin`
- Base URL (local): `http://localhost:8000`

---

## 1) Backend qisqacha

Backend quyidagilarni boshqaradi:

- Mahsulotlar (`/products`)
- Mahsulot subresurslari (`/product-photos`, `/product-items`, `/product-details`)
- Kataloglar (`/categories`, `/collections`, `/color`, `/size`)
- Bannerlar (`/banners`)
- Buyurtmalar (`/order`)
- To'lov callbacklari (`/payments/*`)
- Foydalanuvchi paneli (`/panel/*`)
- Excel import (`/excel/*`)
- Tarix (`/history/*`)
- Tizim endpointlari (`/system/*`)
- Frontend bootstrap (`/frontend/bootstrap`)
- Telegram bot (aiogram, guruh bildirishnomalari)

---

## 2) Auth va ruxsatlar

Loyihada amaldagi auth turi: **HTTP Basic Auth**.

### Kimlar bor

- `super admin` (`.env` dagi `ADMIN_USERNAME` + `ADMIN_PASS`)
- `admin` (DB dagi `AdminUser`)
- `operator` (DB dagi `AdminUser`)

### Endpointlarda auth belgisi

- `Public` - auth kerak emas
- `Admin` - faqat `admin`
- `Staff` - `admin` yoki `operator`
- `Super admin` - faqat `.env` dagi super admin

---

## 3) Javob formati (muhim)

Loyihada ikki xil javob uslubi bor.

### A) Standart wrapper (`ok_response`)

```json
{
  "ok": true,
  "data": {},
  "meta": {},
  "error": null
}
```

### B) To'g'ridan-to'g'ri obyekt

Ba'zi endpointlar to'g'ridan-to'g'ri obyekt/list qaytaradi, masalan:

```json
{
  "ok": true,
  "id": 12
}
```

yoki

```json
{
  "photos": []
}
```

### Xatolik

Xatoliklar odatda `HTTPException` orqali qaytadi (`detail` maydoni bilan), masalan 400/401/403/404/409/500.

---

## 4) API hujjati - har bir URL nima qiladi

Quyida **har bir endpoint** uchun: vazifa, nima yuboriladi, nima qaytadi.

---

## 4.1 System API (`/system`) - Public

### `GET /system/health`
- Vazifa: API ishlayotganini tekshiradi.
- Yuboriladi: hech narsa.
- Qaytadi:
```json
{ "ok": true, "service": "textile-shop-api" }
```

### `GET /system/ready`
- Vazifa: DB ulanishini tekshiradi.
- Yuboriladi: hech narsa.
- Qaytadi:
```json
{ "ok": true, "database": "connected" }
```

### `GET /system/auth-mode`
- Vazifa: autentifikatsiya rejimini ko'rsatadi.
- Yuboriladi: hech narsa.
- Qaytadi:
```json
{ "auth": "basic", "jwt_enabled": false }
```

### `POST /system/dev/seed-fake` (Super admin, vaqtinchalik)
- Vazifa: test uchun fake ma'lumotlar yaratadi (`categories`, `collections`, `colors`, `sizes`, `products`, `product_items`, `product_details`, `orders`, `order_items`).
- Query:
  - `n` (default `3`, min `1`, max `20`) - har bir asosiy entity soni.
  - `clear_before` (bool, default `false`) - `true` bo'lsa, oldin eski ma'lumotlarni tozalaydi.
- Auth: Basic (`super admin` `.env` credentials)
- Qaytadi (`ok_response`):
```json
{
  "ok": true,
  "data": {
    "message": "Fake data yaratildi",
    "clear_before": true,
    "cleared": {
      "order_items": 12,
      "orders": 12,
      "product_details": 8,
      "product_photos": 0,
      "product_items": 8,
      "products": 8,
      "sizes": 8,
      "colors": 8,
      "collections": 8,
      "categories": 8
    },
    "created": {
      "categories": 3,
      "collections": 3,
      "colors": 3,
      "sizes": 3,
      "products": 3,
      "product_items": 3,
      "product_details": 3,
      "product_photos": 0,
      "orders": 3,
      "order_items": 3
    },
    "note": "Bu endpoint vaqtinchalik (dev) uchun."
  },
  "meta": {},
  "error": null
}
```

### `DELETE /system/dev/clear-fake` (Super admin, vaqtinchalik)
- Vazifa: fake/test ma'lumotlarni tozalaydi.
- Auth: Basic (`super admin` `.env` credentials)
- Qaytadi (`ok_response`):
```json
{
  "ok": true,
  "data": {
    "message": "Fake/test data tozalandi",
    "cleared": {
      "order_items": 12,
      "orders": 12,
      "product_details": 8,
      "product_photos": 0,
      "product_items": 8,
      "products": 8,
      "sizes": 8,
      "colors": 8,
      "collections": 8,
      "categories": 8
    },
    "note": "Bu endpoint vaqtinchalik (dev) uchun."
  },
  "meta": {},
  "error": null
}
```

---

## 4.2 Frontend API (`/frontend`) - Public

### `GET /frontend/bootstrap`
- Vazifa: frontend uchun boshlang'ich ma'lumotlarni bitta so'rovda beradi.
- Query:
  - `include_inactive` (bool, default: `false`)
- Qaytadi:
```json
{
  "ok": true,
  "banners": [],
  "categories": [],
  "collections": [],
  "colors": [],
  "sizes": [],
  "products": [],
  "product_items": [],
  "product_photos": [],
  "product_details": []
}
```

### `GET /frontend/bootstrap/normalized`
- Vazifa: eski bootstrapga o'xshash, lekin duplicate kamroq (`entities + ids` format).
- Query:
  - `include_inactive` (bool, default: `false`)
- Qaytadi:
  - `entities.categories|collections|colors|sizes|products|product_items|product_photos|product_details`
  - `result.product_ids`
- Izoh:
  - eski endpoint saqlanadi (`/frontend/bootstrap`)
  - yangi endpointda bir xil obyektlar bitta joyda saqlanadi, bog'lanishlar `*_ids` orqali beriladi.
  - tayyor TypeScript tiplari: `frontend_bootstrap_normalized.types.ts`

---

## 4.3 Products API (`/products`)

### `GET /products` (Public)
- Vazifa: barcha mahsulotlar ro'yxati.
- Query:
  - `include_inactive` (bool, default `false`)
- Qaytadi: `Product[]` (to'g'ridan-to'g'ri list).

### `GET /products/search` (Public)
- Vazifa: oddiy qidiruv/filter.
- Query:
  - `search` (string, ixtiyoriy)
  - `category_id` (int, ixtiyoriy)
  - `include_inactive` (bool, default `false`)
- Qaytadi (`ok_response`):
```json
{ "ok": true, "data": [], "meta": { "count": 0 }, "error": null }
```

### `GET /products/search/advanced` (Public)
- Vazifa: kengaytirilgan filter.
- Query:
  - `search`, `category_id`, `collection_id`, `is_active`, `min_price`, `max_price`, `limit` (default 100, max 500)
- Qaytadi (`ok_response`): `data = Product[]`, `meta.count`.

### `GET /products/category/{category_id}` (Public)
- Vazifa: kategoriya bo'yicha mahsulotlar.
- Yuboriladi: `category_id` (path).
- Query:
  - `include_inactive` (bool, default `false`)
- Qaytadi: `Product[]`.

### `GET /products/{product_id}` (Public)
- Vazifa: bitta mahsulot.
- Yuboriladi: `product_id` (path).
- Qaytadi:
```json
{ "product": { } }
```
- 404: `Product topilmadi`.

### `POST /products` (Admin)
- Vazifa: yangi mahsulot yaratish.
- Content-Type: `multipart/form-data`
- Yuboriladi (form):
  - `category_id` (int, required)
  - `collection_id` (int, required)
  - `name_uz`, `name_ru`, `name_eng` (str, required)
  - `description_uz`, `description_ru`, `description_eng` (str, required)
  - `price` (int, required)
  - `clothing_type` (`erkak` yoki `ayol`, required)
  - `is_active` (bool, optional, default `true`)
  - `photo` (file, optional, faqat image)
- Qaytadi:
```json
{ "ok": true, "id": 123 }
```

### `PATCH /products/{product_id}` (Admin)
- Vazifa: mahsulotni qisman yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy form fieldlar):
  - `category_id`, `collection_id`, `name_uz`, `name_ru`, `name_eng`, `description_uz`, `description_ru`, `description_eng`, `price`, `is_active`, `photo`
  - `clothing_type` (`erkak` yoki `ayol`)
- Qaytadi:
```json
{ "ok": true }
```
- 400: "O'zgartirish uchun ma'lumot yo'q"

### `DELETE /products/{product_id}` (Admin)
- Vazifa: mahsulotni o'chirish.
- Yuboriladi: `product_id` (path).
- Qaytadi:
```json
{ "ok": true }
```

---

## 4.4 Product Photos API (`/product-photos`)

### `GET /product-photos` (Public)
- Vazifa: product rasmlar ro'yxati.
- Query:
  - `product_id` (int, ixtiyoriy)
- Qaytadi: `ProductPhoto[]`.

### `GET /product-photos/{photo_id}` (Public)
- Vazifa: bitta rasm.
- Qaytadi: `ProductPhoto`.

### `POST /product-photos` (Admin)
- Vazifa: mahsulotga rasm qo'shish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `product_id` (int, required)
  - `photo` (file, required, image)
- Qaytadi:
```json
{ "ok": true, "id": 1 }
```

### `PATCH /product-photos/{photo_id}` (Admin)
- Vazifa: rasmni yoki product bog'lanishini yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy):
  - `product_id` (int)
  - `photo` (file)
- Qaytadi: `{ "ok": true }`

### `DELETE /product-photos/{photo_id}` (Admin)
- Vazifa: rasmni o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.5 Product Items API (`/product-items`)

### `GET /product-items` (Public)
- Vazifa: mahsulot variantlari listi.
- Query:
  - `product_id` (int, ixtiyoriy)
- Qaytadi: `ProductItems[]`.

### `GET /product-items/{item_id}` (Public)
- Vazifa: bitta variant.
- Qaytadi: `ProductItems`.

### `POST /product-items` (Admin)
- Vazifa: yangi variant yaratish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `product_id` (int)
  - `color_id` (int)
  - `size_id` (int)
  - `total_count` (int)
- Qaytadi:
```json
{ "ok": true, "id": 1 }
```

### `PATCH /product-items/{item_id}` (Admin)
- Vazifa: variantni qisman yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy):
  - `product_id`, `color_id`, `size_id`, `total_count`
- Qaytadi: `{ "ok": true }`

### `DELETE /product-items/{item_id}` (Admin)
- Vazifa: variantni o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.6 Product Details API (`/product-details`)

### `GET /product-details` (Public)
- Vazifa: mahsulot tafsilotlari listi.
- Query:
  - `product_id` (int, ixtiyoriy)
- Qaytadi: `ProductDetail[]`.

### `GET /product-details/{detail_id}` (Public)
- Vazifa: bitta tafsilot.
- Qaytadi: `ProductDetail`.

### `POST /product-details` (Admin)
- Vazifa: tafsilot qo'shish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `product_id` (int)
  - `name_uz`, `name_ru`, `name_eng` (str)
- Qaytadi:
```json
{ "ok": true, "id": 1 }
```

### `PATCH /product-details/{detail_id}` (Admin)
- Vazifa: tafsilotni qisman yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy):
  - `product_id`, `name_uz`, `name_ru`, `name_eng`
- Qaytadi: `{ "ok": true }`

### `DELETE /product-details/{detail_id}` (Admin)
- Vazifa: tafsilotni o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.7 Categories API (`/categories`)

### `GET /categories` (Public)
- Vazifa: kategoriyalar ro'yxati.
- Qaytadi: `Category[]`.

### `GET /categories/{category_id}` (Public)
- Vazifa: bitta kategoriya.
- Qaytadi: `Category`.

### `POST /categories` (Admin)
- Vazifa: kategoriya yaratish.
- Content-Type: `multipart/form-data`
- Yuboriladi (kamida bittasi):
  - `name_uz`, `name_ru`, `name_eng`
- Qaytadi:
```json
{ "ok": true, "data": { } }
```

### `PATCH /categories/{category_id}` (Admin)
- Vazifa: kategoriyani yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy):
  - `name_uz`, `name_ru`, `name_eng`
- Qaytadi: `{ "ok": true, "data": { } }`

### `DELETE /categories/{category_id}` (Admin)
- Vazifa: kategoriyani o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.8 Collections API (`/collections`)

### `GET /collections` (Public)
- Vazifa: kolleksiyalar ro'yxati.
- Qaytadi: `Collection[]`.

### `GET /collections/{collection_id}` (Public)
- Vazifa: bitta kolleksiya.
- Qaytadi: `Collection`.

### `POST /collections` (Admin)
- Vazifa: kolleksiya yaratish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `name_uz`, `name_ru`, `name_eng`
- Qaytadi: `{ "ok": true, "data": { } }`

### `PATCH /collections/{collection_id}` (Admin)
- Vazifa: kolleksiyani yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy):
  - `name_uz`, `name_ru`, `name_eng`
- Qaytadi: `{ "ok": true, "data": { } }`

### `DELETE /collections/{collection_id}` (Admin)
- Vazifa: kolleksiyani o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.9 Color API (`/color`)

### `GET /color` (Public)
- Vazifa: ranglar ro'yxati.
- Qaytadi: `Color[]`.

### `GET /color/{color_id}` (Public)
- Vazifa: bitta rang.
- Qaytadi: `Color`.

### `POST /color` (Admin)
- Vazifa: rang yaratish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `color_code` (text, masalan `#FF0000` yoki `red-500`)
- Qaytadi: `{ "ok": true, "data": { } }`

### `PATCH /color/{color_id}` (Admin)
- Vazifa: rangni yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy):
  - `color_code`
- Qaytadi: `{ "ok": true, "data": { } }`

### `DELETE /color/{color_id}` (Admin)
- Vazifa: rangni o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.10 Size API (`/size`)

### `GET /size` (Public)
- Vazifa: o'lchamlar ro'yxati.
- Qaytadi: `Size[]`.

### `GET /size/{size_id}` (Public)
- Vazifa: bitta o'lcham.
- Qaytadi: `Size`.

### `POST /size` (Admin)
- Vazifa: o'lcham yaratish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `name` (str)
- Qaytadi: `{ "ok": true, "data": { } }`

### `PATCH /size/{size_id}` (Admin)
- Vazifa: o'lchamni yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `name` (str)
- Qaytadi: `{ "ok": true, "data": { } }`

### `DELETE /size/{size_id}` (Admin)
- Vazifa: o'lchamni o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.11 Banners API (`/banners`)

### `GET /banners` (Public)
- Vazifa: bannerlar ro'yxati.
- Qaytadi:
```json
{ "photos": [] }
```

### `POST /banners` (Admin)
- Vazifa: banner rasmi qo'shish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `photo` (file, required)
- Qaytadi: `{ "ok": true }`

### `DELETE /banners/{photo_id}` (Admin)
- Vazifa: bannerni o'chirish.
- Qaytadi: `{ "ok": true }`

---

## 4.12 Orders API (`/order`)

### `GET /order` (Staff)
- Vazifa: buyurtmalar ro'yxati.
- Yuboriladi: auth header.
- Qaytadi (`ok_response`): `data = Order[]`.

### `GET /order/search` (Staff)
- Vazifa: buyurtmalarni filter/qidiruv.
- Query:
  - `order_id` (int)
  - `status_q` (string)
  - `payment` (string)
  - `contact` (string)
  - `first_name` (string)
  - `date_from` (ISO datetime)
  - `date_to` (ISO datetime)
  - `limit` (default 200, max 1000)
- Qaytadi (`ok_response`): `data = Order[]`, `meta.count`.

### `GET /order/{order_id}` (Staff)
- Vazifa: bitta buyurtma + order itemlar.
- Qaytadi (`ok_response`): `data = Order`.

### `POST /order` (Public)
- Vazifa: yangi buyurtma yaratish.
- Content-Type: `application/json`
- `payment` qiymati: `click`, `payme`, `cash`
- Yuboriladi:
```json
{
  "first_name": "Ali",
  "last_name": "Valiyev",
  "country": "Uzbekistan",
  "address": "Chilonzor 10",
  "town_city": "Tashkent",
  "contact": "+998901234567",
  "postcode_zip": 100000,
  "payment": "cash",
  "items": [
    { "product_id": 1, "product_item_id": 10, "count": 2 }
  ],
  "email_address": "optional@mail.com",
  "state_county": "optional"
}
```
- Qaytadi (`ok_response`):
```json
{
  "ok": true,
  "data": {
    "order_id": 1,
    "status": "yangi",
    "order_items": []
  },
  "meta": {},
  "error": null
}
```

### `POST /order/{order_id}/confirm-payment` (Staff)
- Vazifa: to'lovni tasdiqlaydi, ombor sonini kamaytiradi, statusni yangilaydi.
- Yuboriladi:
  - `order_id` (path)
  - body (ixtiyoriy):
```json
{ "next_status": "to'landi" }
```
- Qaytadi:
  - agar allaqachon paid bo'lsa:
```json
{ "ok": true, "already_paid": true, "order_id": 1 }
```
  - odatda (`ok_response`): `data = { order_id, status }`

### `PATCH /order/{order_id}/status` (Staff)
- Vazifa: statusni qo'lda o'zgartirish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `new_status` (str, required)
- Qaytadi (`ok_response`): `data = { order_id, status }`

Ruxsat etilgan statuslar:
- `yangi`, `to'landi`, `jarayonda`, `tayyor`, `yetkazilmoqda`, `yetkazildi`, `bekor qilindi`

---

## 4.13 Payments API (`/payments`) - Public callback endpointlar

`X-Signature` header ishlatilishi mumkin (`.env` da secret bo'lsa majburiy).

### `POST /payments/click/prepare`
- Vazifa: Click to'lovidan oldin orderni tekshiradi.
- Yuboriladi:
```json
{ "order_id": 1 }
```
- Header (ixtiyoriy/konfiguratsiyaga bog'liq): `X-Signature`
- Qaytadi (`ok_response`): `data = { order_id, status }`

### `POST /payments/click/complete`
- Vazifa: Click to'lovini yakunlaydi (`paid`) va stock kamaytiradi.
- Yuboriladi:
```json
{ "order_id": 1, "transaction_id": "click_tx_1", "success": true }
```
- Qaytadi:
  - `success=false` bo'lsa (`ok_response`): `{ order_id, status, success: false }`
  - aks holda (`ok_response`): `{ ok, already_paid, order_id, status }`

### `POST /payments/payme/check`
- Vazifa: Payme uchun orderni tekshiradi.
- Yuboriladi:
```json
{ "order_id": 1, "account": "optional" }
```
- Qaytadi (`ok_response`): `{ order_id, status }`

### `POST /payments/payme/perform`
- Vazifa: Payme to'lovini yakunlaydi (`paid`) va stock kamaytiradi.
- Yuboriladi:
```json
{ "order_id": 1, "transaction_id": "payme_tx_1", "success": true }
```
- Qaytadi:
  - `success=false` bo'lsa (`ok_response`): `{ order_id, status, success: false }`
  - aks holda (`ok_response`): `{ ok, already_paid, order_id, status }`

---

## Telegram Bot (`/telegram`)

- Yangi buyurtma yaratilganda bot guruhga xabar yuboradi.
- Order status o'zgarganda (to'lov/status update/callback) bot guruhga status xabari yuboradi.
- Guruh xabaridagi **Qabul qildim** tugmasi bosilganda order `yangi -> jarayonda` bo'ladi (stock kamayadi) va email yuboriladi.

### `POST /telegram/set-webhook` (Admin)
- Bot webhook URLni Telegramga yuboradi (`TG_WEBHOOK_URL` va `TG_BOT_TOKEN` kerak).

### `POST /telegram/webhook` (Public, Telegram callback)
- Telegram update'larni qabul qiladi.
- `TG_WEBHOOK_SECRET` berilgan bo'lsa, header orqali tekshiradi.

Kerakli `.env`:
- `TG_BOT_TOKEN=...`
- `TG_GROUP_IDS=-1001234567890,-1009876543210`
- `TG_WEBHOOK_URL=https://your-domain.com/telegram/webhook`
- `TG_WEBHOOK_SECRET=optional-secret`

---

## 4.14 Panel API (`/panel`)

### `POST /panel/operators` (Super admin)
- Vazifa: admin/operator user yaratish.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `username` (str)
  - `operator_code` (str)
  - `status` (`admin` yoki `operator`, default `operator`)
  - `is_active` (bool, default `true`)
- Qaytadi:
```json
{ "ok": true, "user_id": 1, "username": "john", "status": "operator" }
```

### `GET /panel/users` (Admin)
- Vazifa: admin/operatorlar ro'yxati.
- Qaytadi: `AdminUser[]`.

### `GET /panel/me` (Staff)
- Vazifa: login bo'lgan user profili.
- Qaytadi: `AdminUser`.

### `PATCH /panel/users/{user_id}` (Admin)
- Vazifa: userni yangilash.
- Content-Type: `multipart/form-data`
- Yuboriladi (ixtiyoriy):
  - `username`
  - `operator_code` (yuborilsa password qayta hash qilinadi)
  - `is_active`
- Qaytadi: `{ "ok": true }`

---

## 4.15 Excel API (`/excel`)

### `GET /excel/products/template` (Admin)
- Vazifa: product import uchun `.xlsx` template yuklab beradi.
- Qaytadi: fayl stream (`products_import_template.xlsx`).

### `POST /excel/products/import` (Admin)
- Vazifa: excel orqali product create/update.
- Content-Type: `multipart/form-data`
- Yuboriladi:
  - `excel_file` (required, `.xlsx`/`.xls`)
- Kerakli ustunlar:
  - `category_id`, `collection_id`
  - `name_uz`, `name_ru`, `name_eng`
  - `description_uz`, `description_ru`, `description_eng`
  - `price`, `is_active`
  - `id` (ixtiyoriy; bo'lsa update)
- Qaytadi (`ok_response`):
```json
{
  "ok": true,
  "data": {
    "created": 10,
    "updated": 3,
    "errors": [
      { "row": 5, "error": "..." }
    ]
  },
  "meta": { "errors_count": 1 },
  "error": null
}
```

---

## 4.16 History API (`/history`) - Staff

### `GET /history/orders`
- Vazifa: buyurtmalar tarixini sana oralig'ida olish.
- Query:
  - `date_from` (ISO)
  - `date_to` (ISO)
  - `limit` (1..2000, default 200)
- Qaytadi (`ok_response`): `data = Order[]`, `meta.count`.

### `GET /history/products`
- Vazifa: product audit tarixi.
- Query:
  - `date_from` (ISO)
  - `date_to` (ISO)
  - `action` (masalan: `excel_create`, `excel_update`)
  - `limit` (1..2000)
- Qaytadi (`ok_response`): `data = AuditLog[]`, `meta.count`.

### `GET /history/logs`
- Vazifa: umumiy tizim loglari.
- Query:
  - `entity` (masalan: `product`, `order`, `payment`)
  - `date_from` (ISO)
  - `date_to` (ISO)
  - `limit` (1..3000, default 500)
- Qaytadi (`ok_response`): `data = AuditLog[]`, `meta.count`.

### `GET /history/stats/sales`
- Vazifa: sanadan-sanagacha sotuv statistikasi.
- Query:
  - `date_from` (ISO)
  - `date_to` (ISO)
- Qaytadi (`ok_response`):
```json
{
  "ok": true,
  "data": {
    "from": "2026-04-01",
    "to": "2026-04-30",
    "total_orders": 120,
    "paid_orders": 95,
    "sold_items_count": 240,
    "sales_amount": 125000000,
    "payment_breakdown": {
      "click": { "orders_count": 40, "items_count": 100, "amount": 50000000 },
      "payme": { "orders_count": 35, "items_count": 90, "amount": 45000000 },
      "cash": { "orders_count": 20, "items_count": 50, "amount": 30000000 }
    },
    "sales_by_clothing_type": {
      "erkak": { "sold_items": 120, "sales_amount": 70000000 },
      "ayol": { "sold_items": 90, "sales_amount": 55000000 }
    },
    "currency": "UZS"
  },
  "meta": {},
  "error": null
}
```
- Eslatma:
  - `total_orders` - intervaldagi jami buyurtma soni
  - `paid_orders` - sotuvga kirgan buyurtmalar (`to'landi`, `jarayonda`, `tayyor`, `yetkazilmoqda`, `yetkazildi`)
  - `sold_items_count` - sotilgan mahsulot birliklari yig'indisi
  - `sales_amount` - sotuv summasi (`OrderItem.total` yig'indisi)
  - `payment_breakdown` - to'lov turi bo'yicha kesim (`click`, `payme`, `cash`)

### `GET /history/stats/analytics-v2`
- Vazifa: kengaytirilgan analytics (top products, conversion, avg check, LTV, repeat sales, sales by day/week).
- Query:
  - `date_from` (ISO)
  - `date_to` (ISO)
  - `top_limit` (default 10, max 100)
- Qaytadi (`ok_response`) ichida quyidagilar bor:
  - `top_products` - eng ko'p sotilgan mahsulotlar (soni va revenue)
  - `conversion_by_status` - statuslar bo'yicha konversiya (`orders_count`, `rate`)
  - `average_check` - o'rtacha chek
  - `ltv` - customer LTV (`contact` bo'yicha)
  - `repeat_sales` - takroriy sotuv metrikasi
  - `sales_by_day` - kunlik sotuv
  - `sales_by_week` - haftalik sotuv

### `GET /history/stats/dashboard`
- Vazifa: admin dashboard uchun 1 ta endpointda asosiy KPI.
- Query:
  - `low_stock_threshold` (default 5)
  - `low_stock_limit` (default 10)
  - `top_limit` (default 10)
- Qaytadi (`ok_response`) ichida:
  - `today_sales` (`orders_count`, `sold_items`, `revenue`)
  - `week_sales` (`orders_count`, `sold_items`, `revenue`)
  - `new_orders` (status=`yangi`)
  - `low_stock` (kam qolgan variantlar)
  - `top_products` (eng ko'p sotilgan mahsulotlar)
  - `inventory_summary` (jami mahsulot/sku/stock/umumiy tovar qiymati)
  - `inventory_by_clothing_type` (`erkak`/`ayol` kesimida sklad qiymati)

### `GET /history/stats/inventory`
- Vazifa: mini sklad statistikasi (jami dona va umumiy tovar summasi).
- Qaytadi (`ok_response`) ichida:
  - `products_count`, `sku_count`, `total_stock`, `total_inventory_value`
  - `by_clothing_type.erkak|ayol` (`stock`, `inventory_value`)

---

## 5) Frontendga amaliy tavsiya (UZ)

- Public endpointlarda auth bermang.
- Admin/Staff endpointlarda har doim `Authorization: Basic base64(username:password)` yuboring.
- `POST/PATCH` katalog endpointlarida asosan `FormData` ishlating.
- Buyurtma yaratishda (`POST /order`) faqat `application/json` ishlating.
- Payment callbacklarda `X-Signature` (agar prod’da yoqilgan bo'lsa) to'g'ri imzo bilan yuborilsin.

---

## 6) Test

```bash
pytest tests/integration -q
```

---

## Telegram Bot (aiogram)

- Bot entrypoint: `bot.py` (ichida `bot_app.main` chaqiriladi)
- Modul arxitektura:
  - `bot_app/main.py` - run/polling start
  - `bot_app/core.py` - bot + dispatcher yig'ish
  - `bot_app/handlers/order_callbacks.py` - callback handlerlar
  - `bot_app/services/order_flow.py` - order status/stock biznes logikasi
- Docker compose ichida alohida servis: `bot`
- Vazifasi:
  - yangi buyurtma haqida guruhga xabar yuborish
  - order status o'zgarsa guruhga xabar yuborish
  - guruhdagi **Qabul qildim** tugmasi orqali `yangi -> jarayonda` statusga o'tkazish
  - shu paytda email xabari ham yuboriladi

Ishga tushirish:
- Docker: `docker compose up -d --build` (app + db + bot)
- Lokal bot: `py -3 bot.py`

---

## 7) Qo'shimcha

- OpenAPI client: `OPENAPI_CLIENT.md`
- Deploy checklist: `DEPLOY_CHECKLIST.md`
- Postman collection: `postman/Textile_shop.postman_collection.json`
