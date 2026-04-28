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
- Admin login (`/login`, `/refresh`)
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
- `https://api.sizningdomen.uz`

## 2) Kontent turlari

- Ko'p create/update endpointlar `Form Data` qabul qiladi.
- Rasm yuklash endpointlarida `multipart/form-data` ishlating.
- Buyurtma endpointi (`POST /order`) esa `JSON` qabul qiladi.

## 3) Auth (juda muhim)

Loyihada 2 xil auth bor:

1. **HTTP Basic**  
   Admin bilan himoyalangan CRUD endpointlar uchun ishlatiladi (`verify_admin_credentials`).
   Frontendda `Authorization: Basic base64(username:password)` yuboriladi.

2. **JWT**  
   `/login` orqali token olish mumkin (`application/x-www-form-urlencoded`).
   Token bo'lgan endpointlarda `Authorization: Bearer <token>` yuboriladi.

Eslatma: hozirgi admin CRUD endpointlarining ko'pi `HTTP Basic` bilan himoyalangan.

## 4) Frontend uchun eng kerakli endpointlar

### Public endpointlar

- `GET /products` - barcha mahsulotlar
- `GET /products/{product_id}` - bitta mahsulot
- `GET /products/search?search=...&category_id=...` - qidiruv/filter
- `GET /products/category/{category_id}` - kategoriya bo'yicha
- `GET /banners/` - bannerlar
- `GET /categories` - kategoriyalar
- `GET /collections/` - kolleksiyalar
- `GET /color/` - ranglar
- `GET /size/` - o'lchamlar
- `GET /product-photos?product_id=...`
- `GET /product-items?product_id=...`
- `GET /product-details?product_id=...`

### Buyurtma

- `POST /order` - buyurtma yaratish (JSON)
- `GET /order` - buyurtmalar ro'yxati
- `GET /order/{order_id}` - buyurtma detali
- `POST /order/{order_id}/confirm-payment` - to'lov tasdig'i va stock kamaytirish
- `PATCH /order/{order_id}/status` - status o'zgartirish (admin/basic auth)

### Admin CRUD (Basic auth talab qiladi)

- `POST/PATCH/DELETE /products...`
- `POST/PATCH/DELETE /product-photos...`
- `POST/PATCH/DELETE /product-items...`
- `POST/PATCH/DELETE /product-details...`
- `POST/PATCH/DELETE /categories...`
- `POST/PATCH/DELETE /collections...`
- `POST/PATCH/DELETE /color...`
- `POST/PATCH/DELETE /size...`
- `POST/DELETE /banners...` (foydalanuvchi statusiga ham qaraydi)

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

### 3) Login va Bearer token olish

```js
const body = new URLSearchParams();
body.append("username", "admin");
body.append("password", "1111");

const res = await fetch("http://localhost:8000/login", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body,
});

const token = await res.json();
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
