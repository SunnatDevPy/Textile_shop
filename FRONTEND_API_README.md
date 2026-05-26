# Textile Shop — frontend integratsiyasi (API qo‘llanmasi)

Bu hujjat frontend dasturchisi uchun: **bazaviy URL**, **autentifikatsiya**, **asosiy oqimlar** va **javob formatlari**.

> **To‘liq ro‘yxat va schema:** brauzerda `https://<server>/api/docs` (Swagger) yoki `https://<server>/api/openapi.json`.

---

## 1. Umumiy

| Parametr | Qiymat |
|----------|--------|
| API prefiks | **`/api`** (barcha routerlar shu ostida) |
| Media fayllar | **`/media/...`** (statik, auth yo‘q) |
| Swagger | **`GET /api/docs`** |
| ReDoc | **`GET /api/redoc`** |
| CORS | Loyihada **`allow_origins=["*"]`** — dev/demo uchun mos |

**Base URL misol:** `https://textile.okach-admin.uz`  
To‘liq endpoint: `https://textile.okach-admin.uz/api/products`

---

## 2. Autentifikatsiya (JWT yo‘q — faqat Basic Auth)

Ko‘p **admin/operator** marshrutlarida:

```http
Authorization: Basic base64(username:password)
```

**Ikki turdagi foydalanuvchi:**

1. **Super admin** — `.env` dagi `ADMIN_USERNAME` va **plain parol** (`ADMIN_PASS` esa **bcrypt hash**).  
   Kirish: `username` = `ADMIN_USERNAME`, `password` = siz belgilagan oddiy parol (server hash bilan solishtiradi).

2. **Operator / Admin (DB)** — `POST /api/panel/operators` orqali super admin yaratgan.  
   - `username` — yaratilgandagi login  
   - `password` — yaratishda yuborilgan **`operator_code`** (u parol sifatida bcrypt bilan saqlanadi)

**Kim nima qiladi (qisqa):**

| `Depends` | Kim kira oladi |
|-----------|----------------|
| `verify_admin_credentials` | Super admin **yoki** faol operator/admin (barchasi `AdminUser`/`SimpleNamespace`) |
| `require_admin` | Faqat **`status === admin`** (super admin `.env` orqali ham admin deb hisoblanadi) |
| `verify_super_admin_credentials` | Faqat **super admin** (`.env` login/parol) |

**401:** noto‘g‘ri login/parol. **403:** masalan operator `require_admin` bilan himoyalangan joyga urinsa.

---

## 3. Javob formatlari (muhim)

Backend **bir xil bo‘lmagan** javob berishi mumkin — har bir blokda qay etilgan.

### 3.1. `ok_response` (Ko‘pgina joylarda)

```json
{
  "ok": true,
  "data": { "...": "..." },
  "meta": {},
  "error": null
}
```

### 3.2. To‘g‘ridan JSON ro‘yxat / obyekt

Masalan **`GET /api/products`** (parametrsiz) — ba’zan **`Product[]`** to‘g‘ridan-qog‘oz array qaytaradi (wrapper yo‘q).  
Frontend: avval tekshirish `Array.isArray(res)` yoki Swagger’dan aniqlangan holda yozing.

### 3.3. FastAPI HTTP xatolari

Masalan **`422`** validatsiya, **`404`**, **`401`**:

```json
{ "detail": "Matn xabari yoki validation errors" }
```

### 3.4. Payme webhook (`POST /api/payme`)

JSON-RPC **2.0**; xato ham ko‘pincha **`HTTP 200`** + ichida **`error`** (Payme talabi).

---

## 4. Do‘kon / mijoz uchun (Basic auth kerak **emas**)

| Method | Yo‘l | Query / body | Javob (qisqa) |
|--------|------|--------------|----------------|
| GET | `/api/products` | `include_inactive`, `limit` | Mahsulotlar massivi |
| GET | `/api/products/search` | `search`, `category_id`, `include_inactive`, `limit` | `{ ok, data, meta }` |
| GET | `/api/products/search/advanced` | keng filterlar (Swagger) | `{ ok, data, meta }` |
| GET | `/api/products/category/{id}` | `include_inactive`, `limit` | Massiv |
| GET | `/api/products/{product_id}` | — | `{ product: {...} }` |
| GET | `/api/categories` | — | Kategoriya ro‘yxati |
| GET | `/api/collections` | — | Kolleksiya ro‘yxati |
| GET | `/api/color` , `/api/size` | — | Rang / o‘lcham |
| GET | `/api/banners` | — | Bannerlar |

**Buyurtma yaratish:**

| POST | Yo‘l | Body (JSON) | Javob |
|------|------|-------------|--------|
| ✅ | **`/api/order`** | Pastdagi sxema | **`{ ok, data, ... }`** — `data` ichida asosan **`order_id`**, **`total_sum`**, **`payment`**; agar **`payment === "payme"`** va sozlangan bo‘lsa: **`payment_url`**, **`amount_tiyin`**. |

**`CreateOrderPayload` (majburiy maydonlar):**

```json
{
  "first_name": "Ali",
  "last_name": "Valiyev",
  "country": "UZ",
  "address": "Manzil",
  "town_city": "Toshkent",
  "contact": "+998901234567",
  "postcode_zip": 100000,
  "payment": "cash",
  "items": [
    {
      "product_id": 1,
      "product_item_id": 1,
      "count": 2
    }
  ],
  "email_address": null,
  "gmail": null,
  "state_county": null
}
```

- **`payment`:** **`"cash"`** | **`"payme"`** | **`"click"`**  
- **`product_item_id`** — haqiqiy variant (rang/o‘lcham) ID si; frontend **variant tanlashni** berganda mos ID yuboradi.

**To‘lov havolalari (kabinet uchun):**

| GET | Yo‘l | Javob |
|-----|------|--------|
| | `/api/payment-url/{order_id}/payme` | `{ payment_url, order_id, amount, payment_system: "payme" }` |
| | `/api/payment-url/{order_id}/click` | `{ payment_url, order_id, amount, payment_system: "click" }` |
| | `/api/payment-url/{order_id}/payment-info` | Buyurtma + summa + (Payme bo‘lsa) `payment_url` |

**Click** uchun serverda **`PUBLIC_BASE_URL`** to‘ldirilgan bo‘lishi kerak (return URL).  
**Payme** uchun checkout: `.env` dagi `PAYME_ENDPOINT` (test: `https://checkout.test.paycom.uz`).

---

## 5. Admin / operator paneli (Basic auth **kerak**)

**Profil va foydalanuvchilar:**

| Method | Yo‘l | Eslatma |
|--------|------|---------|
| GET | `/api/panel/me` | Joriy user |
| GET | `/api/panel/users` | **Faqat admin** (`require_admin`) |
| POST | `/api/panel/operators` | **Faqat super admin** — `Form`: `username`, `operator_code`, `status`, `is_active` |
| PATCH | `/api/panel/users/{user_id}` | Admin — profil yangilash |

**Admin panel “bootstrap” (bitta so‘rovda ko‘p ma’lumot):**

| GET | `/api/panel/bootstrap` | **Admin** (`require_admin`) — mahsulotlar, kategoriyalar, items, photos, details (Swagger batafsil). |

**Buyurtmalar:**

| Method | Yo‘l | Auth |
|--------|------|------|
| GET | `/api/order` | Staff |
| GET | `/api/order/search` | Staff — query filterlar |
| GET | `/api/order/{order_id}` | Staff |
| GET | `/api/order/admin-table` | Staff — pagination |
| GET | `/api/order/admin-table/export.csv` | Staff |
| POST | `/api/order/{order_id}/confirm-payment` | Staff — naqd / tasdiqlash, stock va status |
| PATCH | `/api/order/{order_id}/status` | Staff — `Form`: `new_status` |

**Mahsulot CRUD (admin):**

| POST/PATCH/DELETE | `/api/products` , `/api/products/{id}` | **Faqat admin** — `require_admin` (photo uploadlar Swagger’da) |

**Kategoriya / kolleksiya CRUD** — qisman **admin** (`POST/PATCH/DELETE` kabi).

**Dashboard:**

| GET | `/api/dashboard/statistics` | Staff (tekshirish uchun Swagger) |
| GET | `/api/dashboard/sales-chart` | ... |
| GET | `/api/dashboard/top-products` | ... |
| GET | `/api/dashboard/orders-by-status` | ... |
| GET | `/api/dashboard/orders-by-payment` | ... |

**Boshqa modullar:** `/api/history/*`, `/api/excel/*`, `/api/stock-movements/*`, `/api/alerts/*`, `/api/bot-settings/*`, `/api/telegram/*` — barchasi Swagger’da; ko‘pchilik **staff/admin** bilan.

---

## 6. Tizim va dev

| GET | `/api/system/health` | Sog‘liq |
| GET | `/api/system/ready` | DB tayyorligi |
| GET | `/api/system/auth-mode` | Auth rejimi haqida |
| POST | `/api/system/dev/seed-fake` | **Super admin** — test ma’lumotlar |

---

## 7. To‘lov provayderlari (frontend to‘g‘ridan chaqirmaydi — kabinet sozlaydi)

| POST | `/api/payme` | Payme **JSON-RPC** (Basic: `Paycom:SECRET` yoki `MERCHANT_ID:SECRET` — backend ularni qabul qiladi) |
| POST | `/api/click/prepare`, `/api/click/complete` | Click rasmiy format |

**Eslatma:** `POST /api/payments/...` marshrutlari **deprecated** (Swagger’da belgilangan); asosiy oqim **`/api/payme`** va **`/api/click/*`**.

---

## 8. Rate limit

Javob sarlavhalarida masalan: `X-RateLimit-Limit`, `X-RateLimit-Remaining`. Cheklov `.env` da **`RATE_LIMIT_PER_MINUTE`** (default 120).

---

## 9. `.env` — demo / lokal (parollar haqida)

`.env` repoga **kiritilmaydi**; **`.env.example`** dan nusxa oling.

| O‘zgaruvchi | Vazifasi | Demo eslatma |
|-------------|-----------|---------------|
| `ADMIN_USERNAME`, `ADMIN_PASS` | Super admin | `ADMIN_PASS` — **faqat bcrypt hash** (oddiy matn **emas**). Lokal uchun `deploy.sh` yoki bcrypt generator bilan yarating. |
| `SECRET_KEY` | Session / ichki sir | Ixtiyoriy uzun tasodifiy qator |
| `DB_*` | PostgreSQL | Docker’da `DB_HOST=db`, `DB_PORT=5432` |
| `PUBLIC_BASE_URL` | Click/Payme qaytish URL | **`https://sizning-domen.uz`** |
| `PAYME_MERCHANT_ID`, `PAYME_SECRET_KEY`, `PAYME_ENDPOINT` | Payme | Test: checkout `checkout.test.paycom.uz`; kalit sandbox kabinet bilan mos |
| `CLICK_*` | Click | Service ID, merchant_id, secret, … |
| `TG_*`, `SMTP_*` | Bildirishnomalar | Ixtiyoriy |

**Operator kirishi:** Super admin **`POST /api/panel/operators`** da `username` + `operator_code` beradi; operator ilovada **`operator_code`** ni parol deb ishlatadi.

---

## 10. Frontend uchun qisqa checklist

1. **Baza URL** + **`/api`** prefiksi  
2. **Do‘kon:** `products`, `categories`, `collections` → **`POST /api/order`**  
3. **Payme/Click:** `data.order_id` yoki javobdan `order_id`, keyin **`GET /api/payment-url/{id}/payme`** yoki **`.../click`**, javob **`payment_url`** ga `window.location`  
4. **Admin:** **`Authorization: Basic`** + Swagger’dan forma/content-type tekshirish (ba’zi `multipart/form-data`)  
5. **Xatolik:** `detail` va `422` uchun `errors` massivi

Savol-backend nomuvofiqliklarni kamaytirish uchun har doim **`/api/docs`** bilan tekshirish tavsiya etiladi.
