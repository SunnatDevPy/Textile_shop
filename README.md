# Textile Shop API (FastAPI)

Ushbu loyiha `Textile Shop` uchun backend API hisoblanadi.  
Backend `FastAPI + PostgreSQL` asosida yozilgan va frontend bilan REST API orqali ishlaydi.

## Nimalar bor

- Mahsulotlar (`products`) CRUD
- Mahsulot ichki bo'limlari:
  - `product-photos`
  - `product-items` (variantlar: rang, o'lcham, soni)
  - `product-details`
- Kategoriyalar:
  - `categories`
  - `collections`
  - `color`
  - `size`
- Bannerlar (`banners`)
- Buyurtmalar (`order`)
- To'lov integratsiyasi (`/payments/...`) — Click va Payme callbacklari
- Excel import (`/excel/products/import`) — product create/update
- Tarix va loglar (`/history/...`) — product/order/log history
- Operator/Admin boshqaruvi (`/panel/...`)
- Frontend bootstrap (`/frontend/bootstrap`)
- Tizim tekshiruv endpointlari (`/system/health`, `/system/ready`)
- Swagger hujjat: `/docs`

## Texnologiyalar

- `FastAPI`
- `SQLAlchemy (async)`
- `PostgreSQL`
- `Pydantic v2`
- `Docker / Docker Compose`

## Tez ishga tushirish (Docker)

### 1) `.env` tayyorlash

Loyihada `.env` bo'lishi kerak.

Minimal kerakli qiymatlar:

```env
DB_NAME=textile
DB_USER=postgres
DB_PASS=1
DB_HOST=db
DB_PORT=5432
SECRET_KEY=change_me
ADMIN_USERNAME=admin
ADMIN_PASS=$2b$12$your_bcrypt_hash
ADMIN=123456789
```

`ADMIN_PASS` oddiy matn emas, `bcrypt` hash bo'lishi shart.

### 2) Konteynerlarni ko'tarish

```bash
docker compose up -d --build
```

### 3) Tekshirish

```bash
docker compose ps
docker compose logs -f app
```

Swagger:
- [http://localhost:8000/docs](http://localhost:8000/docs)

## Frontend dasturchi uchun ulanish yo'riqnomasi

## 1) Base URL

Lokal:
- `http://localhost:8000`

Prod:
- `https://textile.okach-admin.uz/`

## 2) Kontent turlari

- Ko'p create/update endpointlar `Form Data` qabul qiladi.
- Rasm yuklash endpointlarida `multipart/form-data` ishlating.
- Buyurtma endpointi (`POST /order`) esa `JSON` qabul qiladi.

## 3) Auth (juda muhim)

Loyihada **faqat HTTP Basic Auth** bor (JWT o'chirilgan).

- Header:
  - `Authorization: Basic base64(username:password)`
- Login ma'lumotlari:
  - `super admin` (`.env` dagi `ADMIN_USERNAME` / `ADMIN_PASS`) — operator/admin yaratadi
  - `admin/operator` — DB dagi `AdminUser` orqali kiradi (`username + operator_code`)

### Rollar

- `super admin`:
  - `POST /panel/operators` orqali user yaratadi
- `admin`:
  - katalogni boshqaradi (create/edit/delete)
  - operatorlarni ko'radi/tahrirlaydi
  - buyurtmalarni boshqaradi
- `operator`:
  - buyurtmalarni ko'radi va statusni boshqaradi
  - katalogda delete (va hozirgi sozlamada create/edit ham) qilmaydi

## 4) Frontend uchun eng kerakli endpointlar

### Public endpointlar

- `GET /products` - barcha mahsulotlar
- `GET /products/{product_id}` - bitta mahsulot
- `GET /products/search?search=...&category_id=...` - qidiruv/filter
- `GET /products/search/advanced?...` - kengaytirilgan qidiruv/filter (`collection_id`, `is_active`, `min_price`, `max_price`)
- `GET /products/category/{category_id}` - kategoriya bo'yicha
- `GET /banners/` - bannerlar
- `GET /categories` - kategoriyalar
- `GET /collections/` - kolleksiyalar
- `GET /color/` - ranglar
- `GET /size/` - o'lchamlar
- `GET /product-photos?product_id=...`
- `GET /product-items?product_id=...`
- `GET /product-details?product_id=...`
- `GET /frontend/bootstrap` - frontend uchun bir so'rovda asosiy ma'lumotlar

### Buyurtma

- `POST /order` - buyurtma yaratish (JSON)
- `GET /order` - buyurtmalar ro'yxati (operator/admin)
- `GET /order/search?...` - buyurtma qidirish (`status`, `payment`, `contact`, `date_from`, `date_to`)
- `GET /order/{order_id}` - buyurtma detali (operator/admin)
- `POST /order/{order_id}/confirm-payment` - to'lov tasdig'i va stock kamaytirish (operator/admin)
- `PATCH /order/{order_id}/status` - status o'zgartirish (operator/admin)

### Click va Payme (dokument topshirish oldidan test API)

- `POST /payments/click/prepare` - Click uchun orderni tekshirish
- `POST /payments/click/complete` - Click to'lovini yakunlash (`to'landi` + stock kamaytirish)
- `POST /payments/payme/check` - Payme uchun orderni tekshirish
- `POST /payments/payme/perform` - Payme to'lovini yakunlash (`to'landi` + stock kamaytirish)

Eslatma:
- Bu endpointlar callback/workflow uchun tayyorlangan.
- Real prodga chiqishda Click/Payme imzo (signature) tekshiruvi qo'shilishi kerak.

### Excel orqali product import/create

- `GET /excel/products/template` (admin)
  - excel import uchun tayyor shablon faylni yuklab beradi
- `POST /excel/products/import` (admin)
- `multipart/form-data` orqali `.xlsx` yuboriladi
- Kerakli ustunlar:
  - `id` (ixtiyoriy, bo'lsa update qiladi)
  - `category_id`
  - `collection_id`
  - `name_uz`, `name_ru`, `name_eng`
  - `description_uz`, `description_ru`, `description_eng`
  - `price`
  - `is_active`

Natija:
- nechta `created`
- nechta `updated`
- xatolar ro'yxati (`row`, `error`)

### Tarix API (history)

- `GET /history/orders?date_from=...&date_to=...`
  - buyurtmalar tarixi (sanadan-sanagacha)
- `GET /history/products?date_from=...&date_to=...&action=...`
  - product o'zgarish tarixi (audit log asosida)
- `GET /history/logs?entity=...&date_from=...&date_to=...`
  - tizim loglari tarixi

### Buyurtma statuslari

- `yangi`
- `to'landi`
- `jarayonda`
- `tayyor`
- `yetkazilmoqda`
- `yetkazildi`
- `bekor qilindi`

Muhim:
- `yangi -> to'landi` yoki `yangi -> jarayonda` bo'lsa, ombordagi son avtomatik kamayadi.
- `confirm-payment` ham stockni kamaytiradi (takror chaqirsa qayta kamaytirmaydi).

### Admin endpointlar (Basic auth talab qiladi)

- `POST/PATCH/DELETE /products...`
- `POST/PATCH/DELETE /product-photos...`
- `POST/PATCH/DELETE /product-items...`
- `POST/PATCH/DELETE /product-details...`
- `POST/PATCH/DELETE /categories...`
- `POST/PATCH/DELETE /collections...`
- `POST/PATCH/DELETE /color...`
- `POST/PATCH/DELETE /size...`
- `POST/DELETE /banners...`
- `POST /panel/operators` (faqat super admin)
- `GET /panel/users`, `PATCH /panel/users/{user_id}` (admin)
- `GET /panel/me` (admin/operator)

## Frontenddan so'rov namunalari

### 1) Public mahsulotlar

```js
const res = await fetch("http://localhost:8000/products");
const data = await res.json();
```

### 2) Basic auth bilan create (misol)

```js
const username = "admin";
const password = "1111";
const basic = btoa(`${username}:${password}`);

const form = new FormData();
form.append("name_uz", "Yangi kategoriya");
form.append("name_ru", "Новая категория");
form.append("name_eng", "New category");

const res = await fetch("http://localhost:8000/categories", {
  method: "POST",
  headers: {
    Authorization: `Basic ${basic}`,
  },
  body: form,
});
```

### 3) Frontend bootstrap (bir so'rovda)

```js
const res = await fetch("http://localhost:8000/frontend/bootstrap");
const data = await res.json();
```

### 4) Click callback misol

```js
await fetch("http://localhost:8000/payments/click/complete", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    order_id: 123,
    transaction_id: "click_tx_001",
    success: true
  })
});
```

### 5) Excel import misol

```js
const form = new FormData();
form.append("excel_file", fileInput.files[0]);

await fetch("https://textile.okach-admin.uz/excel/products/import", {
  method: "POST",
  headers: {
    Authorization: `Basic ${basic}`,
  },
  body: form,
});
```

## Muhim texnik eslatmalar

- `main.py` ichida CORS hozircha `*` ochiq turibdi. Prod uchun domenlar bilan cheklang.
- `media/` papka statik rasm fayllar uchun ishlatiladi (`/media` orqali ochiladi).
- App ishga tushganda jadvallar `create_all()` bilan avtomatik yaratiladi.

## Ishlab chiqish va deploy

### Lokal ishga tushirish

```bash
docker compose up -d --build
```

### To'xtatish

```bash
docker compose down
```

### API ni qayta yuklash

```bash
docker compose restart app
```

### Serverga deploy

1. Kodni serverga yuklang
2. `.env` ni prod qiymatlar bilan to'ldiring
3. `docker compose up -d --build`
4. Nginx orqali domen + SSL ulang

Qo'shimcha: `DEPLOY_CHECKLIST.md`

## Frontend integratsiya checklist

- [ ] `BASE_URL` ni to'g'ri qo'ydim
- [ ] Public endpointlar ishlayapti
- [ ] Basic auth bilan admin endpointlar ishlayapti
- [ ] FormData yuboriladigan joylar FormData bilan ketayapti
- [ ] Rasm upload `multipart/form-data` bilan ishlayapti
- [ ] `POST /order` JSON bilan ishlayapti
- [ ] Prodga chiqqanda CORS domenlar bilan cheklangan
