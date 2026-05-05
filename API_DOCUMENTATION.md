# Textile Shop API - Frontend Documentation

**Base URL:** `http://your-domain.com` yoki `http://localhost:8000`

**API versiyasi:** 1.0.0

---

## 📋 Mundarija

1. [Autentifikatsiya](#autentifikatsiya)
2. [Mahsulotlar (Products)](#mahsulotlar-products)
3. [Kategoriyalar (Categories)](#kategoriyalar-categories)
4. [Kolleksiyalar (Collections)](#kolleksiyalar-collections)
5. [Ranglar (Colors)](#ranglar-colors)
6. [O'lchamlar (Sizes)](#olchamlar-sizes)
7. [Mahsulot Rasmlari (Product Photos)](#mahsulot-rasmlari-product-photos)
8. [Mahsulot Variantlari (Product Items)](#mahsulot-variantlari-product-items)
9. [Mahsulot Tafsilotlari (Product Details)](#mahsulot-tafsilotlari-product-details)
10. [Buyurtmalar (Orders)](#buyurtmalar-orders)
11. [To'lov URL'lari (Payment URLs)](#tolov-urllari-payment-urls)
12. [Bannerlar (Main Photos)](#bannerlar-main-photos)

---

## 🔐 Autentifikatsiya

Admin endpointlari uchun **Basic Auth** ishlatiladi.

### Header format:
```
Authorization: Basic base64(username:password)
```

**Misol:**
```javascript
const username = 'admin';
const password = 'password123';
const token = btoa(`${username}:${password}`);

headers: {
  'Authorization': `Basic ${token}`
}
```

---

## 📦 Mahsulotlar (Products)

### 1. Barcha mahsulotlarni olish
**GET** `/products`

**Query parametrlar:**
- `include_inactive` (boolean, optional) - Faol bo'lmagan mahsulotlarni ham ko'rsatish

**Javob:**
```json
[
  {
    "id": 1,
    "category_id": 1,
    "collection_id": 1,
    "name_uz": "Ko'ylak",
    "name_ru": "Рубашка",
    "name_eng": "Shirt",
    "description_uz": "Erkaklar uchun ko'ylak",
    "description_ru": "Рубашка для мужчин",
    "description_eng": "Shirt for men",
    "price": 150000,
    "is_active": true,
    "clothing_type": "erkak",
    "category": { ... },
    "collection": { ... },
    "product_items": [ ... ],
    "product_photos": { ... },
    "product_details": [ ... ]
  }
]
```

---

### 2. Mahsulotlarni qidirish
**GET** `/products/search`

**Query parametrlar:**
- `search` (string, optional) - Mahsulot nomi bo'yicha qidirish
- `category_id` (integer, optional) - Kategoriya ID
- `include_inactive` (boolean, optional) - Faol bo'lmagan mahsulotlarni ham ko'rsatish

**Javob:**
```json
{
  "ok": true,
  "data": [ ... ],
  "meta": {
    "count": 10
  }
}
```

---

### 3. Kengaytirilgan qidiruv
**GET** `/products/search/advanced`

**Query parametrlar:**
- `search` (string, optional) - Mahsulot nomi (uz/ru/eng)
- `category_id` (integer, optional) - Kategoriya ID
- `collection_id` (integer, optional) - Kolleksiya ID
- `is_active` (boolean, optional) - Faollik holati
- `min_price` (integer, optional) - Minimal narx
- `max_price` (integer, optional) - Maksimal narx
- `clothing_type` (string, optional) - Kiyim turi: `erkak`, `ayol`, `unisex`
- `limit` (integer, optional, default: 100) - Natijalar soni (max: 500)

**Javob:**
```json
{
  "ok": true,
  "data": [ ... ],
  "meta": {
    "count": 5
  }
}
```

---

### 4. Kategoriya bo'yicha mahsulotlar
**GET** `/products/category/{category_id}`

**Path parametrlar:**
- `category_id` (integer, required) - Kategoriya ID

**Query parametrlar:**
- `include_inactive` (boolean, optional)

**Javob:** Mahsulotlar ro'yxati

---

### 5. Bitta mahsulotni olish
**GET** `/products/{product_id}`

**Path parametrlar:**
- `product_id` (integer, required) - Mahsulot ID

**Javob:**
```json
{
  "product": {
    "id": 1,
    "name_uz": "Ko'ylak",
    "price": 150000,
    ...
  }
}
```

---

### 6. Mahsulot yaratish (Admin)
**POST** `/products`

**Headers:**
- `Authorization: Basic ...` (required)
- `Content-Type: multipart/form-data`

**Form data:**
- `category_id` (integer, required)
- `collection_id` (integer, required)
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)
- `description_uz` (string, required)
- `description_ru` (string, required)
- `description_eng` (string, required)
- `price` (integer, required)
- `is_active` (boolean, optional, default: true)
- `clothing_type` (string, optional, default: "erkak") - `erkak` yoki `ayol`
- `photo` (file, optional) - Rasm fayli

**Javob:**
```json
{
  "ok": true,
  "id": 123
}
```

---

### 7. Mahsulotni yangilash (Admin)
**PATCH** `/products/{product_id}`

**Headers:**
- `Authorization: Basic ...` (required)
- `Content-Type: multipart/form-data`

**Form data:** (barcha maydonlar optional)
- `category_id` (integer)
- `collection_id` (integer)
- `name_uz` (string)
- `name_ru` (string)
- `name_eng` (string)
- `description_uz` (string)
- `description_ru` (string)
- `description_eng` (string)
- `price` (integer)
- `is_active` (boolean)
- `clothing_type` (string)
- `photo` (file)

**Javob:**
```json
{
  "ok": true
}
```

---

### 8. Mahsulotni o'chirish (Admin)
**DELETE** `/products/{product_id}`

**Headers:**
- `Authorization: Basic ...` (required)

**Javob:**
```json
{
  "ok": true
}
```

---

## 📂 Kategoriyalar (Categories)

### 1. Barcha kategoriyalarni olish
**GET** `/categories`

**Javob:**
```json
[
  {
    "id": 1,
    "name_uz": "Ko'ylaklar",
    "name_ru": "Рубашки",
    "name_eng": "Shirts",
    "products": [ ... ]
  }
]
```

---

### 2. Bitta kategoriyani olish
**GET** `/categories/{category_id}`

**Javob:**
```json
{
  "id": 1,
  "name_uz": "Ko'ylaklar",
  "name_ru": "Рубашки",
  "name_eng": "Shirts"
}
```

---

### 3. Kategoriya yaratish (Admin)
**POST** `/categories`

**Headers:**
- `Authorization: Basic ...` (required)
- `Content-Type: multipart/form-data`

**Form data:**
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)

**Javob:**
```json
{
  "ok": true,
  "data": { ... }
}
```

---

### 4. Kategoriyani yangilash (Admin)
**PATCH** `/categories/{category_id}`

**Form data:** (barcha maydonlar optional)
- `name_uz` (string)
- `name_ru` (string)
- `name_eng` (string)

---

### 5. Kategoriyani o'chirish (Admin)
**DELETE** `/categories/{category_id}`

---

## 🎨 Kolleksiyalar (Collections)

### 1. Barcha kolleksiyalarni olish
**GET** `/collections`

**Javob:**
```json
[
  {
    "id": 1,
    "name_uz": "Yozgi kolleksiya",
    "name_ru": "Летняя коллекция",
    "name_eng": "Summer collection",
    "products": [ ... ]
  }
]
```

---

### 2. Bitta kolleksiyani olish
**GET** `/collections/{collection_id}`

---

### 3. Kolleksiya yaratish (Admin)
**POST** `/collections`

**Form data:**
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)

---

### 4. Kolleksiyani yangilash (Admin)
**PATCH** `/collections/{collection_id}`

---

### 5. Kolleksiyani o'chirish (Admin)
**DELETE** `/collections/{collection_id}`

---

## 🎨 Ranglar (Colors)

### 1. Barcha ranglarni olish
**GET** `/color`

**Javob:**
```json
[
  {
    "id": 1,
    "color_code": "#FF0000"
  },
  {
    "id": 2,
    "color_code": "#0000FF"
  }
]
```

---

### 2. Bitta rangni olish
**GET** `/color/{color_id}`

---

### 3. Rang yaratish (Admin)
**POST** `/color`

**Form data:**
- `color_code` (string, required) - Hex format: `#RRGGBB`

**Javob:**
```json
{
  "ok": true,
  "data": {
    "id": 1,
    "color_code": "#FF0000"
  }
}
```

---

### 4. Rangni yangilash (Admin)
**PATCH** `/color/{color_id}`

**Form data:**
- `color_code` (string)

---

### 5. Rangni o'chirish (Admin)
**DELETE** `/color/{color_id}`

---

## 📏 O'lchamlar (Sizes)

### 1. Barcha o'lchamlarni olish
**GET** `/size`

**Javob:**
```json
[
  {
    "id": 1,
    "name": "S"
  },
  {
    "id": 2,
    "name": "M"
  },
  {
    "id": 3,
    "name": "L"
  }
]
```

---

### 2. Bitta o'lchamni olish
**GET** `/size/{size_id}`

---

### 3. O'lcham yaratish (Admin)
**POST** `/size`

**Form data:**
- `name` (string, required) - Masalan: "S", "M", "L", "XL", "42", "44"

---

### 4. O'lchamni yangilash (Admin)
**PATCH** `/size/{size_id}`

---

### 5. O'lchamni o'chirish (Admin)
**DELETE** `/size/{size_id}`

---

## 🖼️ Mahsulot Rasmlari (Product Photos)

### 1. Barcha rasmlarni olish
**GET** `/product-photos`

**Query parametrlar:**
- `product_id` (integer, optional) - Bitta mahsulotning rasmlarini olish

**Javob:**
```json
[
  {
    "id": 1,
    "product_id": 1,
    "photo": {
      "path": "/media/products/photo1.jpg",
      "url": "http://domain.com/media/products/photo1.jpg"
    }
  }
]
```

---

### 2. Bitta rasmni olish
**GET** `/product-photos/{photo_id}`

---

### 3. Rasm qo'shish (Admin)
**POST** `/product-photos`

**Form data:**
- `product_id` (integer, required)
- `photo` (file, required) - Rasm fayli

**Javob:**
```json
{
  "ok": true,
  "id": 123
}
```

---

### 4. Rasmni yangilash (Admin)
**PATCH** `/product-photos/{photo_id}`

**Form data:**
- `product_id` (integer, optional)
- `photo` (file, optional)

---

### 5. Rasmni o'chirish (Admin)
**DELETE** `/product-photos/{photo_id}`

---

## 🔢 Mahsulot Variantlari (Product Items)

Mahsulot variantlari - bu mahsulotning rang, o'lcham va ombordagi soni.

### 1. Barcha variantlarni olish
**GET** `/product-items`

**Javob:**
```json
[
  {
    "id": 1,
    "product_id": 1,
    "color_id": 1,
    "size_id": 2,
    "total_count": 50
  }
]
```

---

### 2. Mahsulot bo'yicha variantlar
**GET** `/product-items/product/{product_id}`

**Javob:** Bitta mahsulotning barcha variantlari

---

### 3. Bitta variantni olish
**GET** `/product-items/{item_id}`

---

### 4. Variant yaratish (Admin)
**POST** `/product-items`

**Form data:**
- `product_id` (integer, required)
- `color_id` (integer, required)
- `size_id` (integer, required)
- `total_count` (integer, required) - Ombordagi soni

**Javob:**
```json
{
  "ok": true,
  "id": 123
}
```

---

### 5. Variantni yangilash (Admin)
**PATCH** `/product-items/{item_id}`

**Form data:** (barcha maydonlar optional)
- `product_id` (integer)
- `color_id` (integer)
- `size_id` (integer)
- `total_count` (integer)

---

### 6. Variantni o'chirish (Admin)
**DELETE** `/product-items/{item_id}`

---

## 📝 Mahsulot Tafsilotlari (Product Details)

Mahsulot haqida qo'shimcha ma'lumotlar (masalan: material, ishlab chiqaruvchi, parvarish qilish yo'riqnomasi).

### 1. Barcha tafsilotlarni olish
**GET** `/product-details`

---

### 2. Mahsulot bo'yicha tafsilotlar
**GET** `/product-details/product/{product_id}`

**Javob:**
```json
[
  {
    "id": 1,
    "product_id": 1,
    "name_uz": "Material: 100% paxta",
    "name_ru": "Материал: 100% хлопок",
    "name_eng": "Material: 100% cotton"
  }
]
```

---

### 3. Bitta tafsilotni olish
**GET** `/product-details/{detail_id}`

---

### 4. Tafsilot yaratish (Admin)
**POST** `/product-details`

**Form data:**
- `product_id` (integer, required)
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)

---

### 5. Tafsilotni yangilash (Admin)
**PATCH** `/product-details/{detail_id}`

---

### 6. Tafsilotni o'chirish (Admin)
**DELETE** `/product-details/{detail_id}`

---

## 🛒 Buyurtmalar (Orders)

### 1. Buyurtma yaratish
**POST** `/order`

**Headers:**
- `Content-Type: application/json`

**Request body:**
```json
{
  "first_name": "Alisher",
  "last_name": "Valiyev",
  "country": "Uzbekistan",
  "address": "Toshkent sh., Chilonzor tumani, 12-mavze",
  "town_city": "Toshkent",
  "contact": "+998901234567",
  "postcode_zip": 100000,
  "payment": "click",
  "email_address": "alisher@example.com",
  "state_county": "Toshkent viloyati",
  "items": [
    {
      "product_id": 1,
      "product_item_id": 5,
      "count": 2
    },
    {
      "product_id": 3,
      "product_item_id": 12,
      "count": 1
    }
  ]
}
```

**Maydonlar:**
- `first_name` (string, required) - Ism
- `last_name` (string, required) - Familiya
- `country` (string, required) - Mamlakat
- `address` (string, required) - Manzil
- `town_city` (string, required) - Shahar
- `contact` (string, required) - Telefon raqami
- `postcode_zip` (integer, required) - Pochta indeksi
- `payment` (string, required) - To'lov turi: `click`, `payme`, `cash`
- `items` (array, required) - Mahsulotlar ro'yxati
  - `product_id` (integer) - Mahsulot ID
  - `product_item_id` (integer) - Variant ID (rang+o'lcham)
  - `count` (integer) - Soni
- `email_address` (string, optional) - Email
- `state_county` (string, optional) - Viloyat/tuman

**Javob:**
```json
{
  "ok": true,
  "data": {
    "order_id": 123,
    "status": "yangi",
    "order_items": [ ... ]
  }
}
```

**Statuslar:**
- `yangi` - Yangi buyurtma
- `to'landi` - To'lov qabul qilindi
- `jarayonda` - Tayyorlanmoqda
- `tayyor` - Tayyor
- `yetkazilmoqda` - Yetkazilmoqda
- `yetkazildi` - Yetkazildi
- `bekor qilindi` - Bekor qilindi
- `vozvrat` - Qaytarildi

---

### 2. Buyurtma ma'lumotlarini olish (Admin/Operator)
**GET** `/order/{order_id}`

**Headers:**
- `Authorization: Basic ...` (required)

**Javob:**
```json
{
  "ok": true,
  "data": {
    "id": 123,
    "first_name": "Alisher",
    "last_name": "Valiyev",
    "contact": "+998901234567",
    "address": "...",
    "status": "yangi",
    "payment": "click",
    "created_at": "2026-05-05T10:30:00",
    "order_items": [
      {
        "id": 1,
        "product_id": 1,
        "product_item_id": 5,
        "count": 2,
        "price": 150000,
        "total": 300000,
        "product": { ... }
      }
    ]
  }
}
```

---

### 3. Buyurtmalarni qidirish (Admin/Operator)
**GET** `/order/search`

**Headers:**
- `Authorization: Basic ...` (required)

**Query parametrlar:**
- `order_id` (integer, optional) - Buyurtma ID
- `status_q` (string, optional) - Status
- `payment` (string, optional) - To'lov turi
- `contact` (string, optional) - Telefon raqami
- `first_name` (string, optional) - Ism
- `date_from` (string, optional) - Boshlanish sanasi (ISO format: `2026-05-01`)
- `date_to` (string, optional) - Tugash sanasi
- `limit` (integer, optional, default: 200, max: 1000)

**Javob:**
```json
{
  "ok": true,
  "data": [ ... ],
  "meta": {
    "count": 15
  }
}
```

---

### 4. To'lovni tasdiqlash (Admin/Operator)
**POST** `/order/{order_id}/confirm-payment`

**Headers:**
- `Authorization: Basic ...` (required)
- `Content-Type: application/json`

**Request body (optional):**
```json
{
  "next_status": "jarayonda"
}
```

**Javob:**
```json
{
  "ok": true,
  "data": {
    "order_id": 123,
    "status": "to'landi"
  }
}
```

**Eslatma:** Bu endpoint to'lovni tasdiqlaydi va ombor qoldig'ini avtomatik kamaytiradi.

---

### 5. Buyurtma statusini o'zgartirish (Admin/Operator)
**PATCH** `/order/{order_id}/status`

**Headers:**
- `Authorization: Basic ...` (required)
- `Content-Type: multipart/form-data`

**Form data:**
- `new_status` (string, required) - Yangi status

**Javob:**
```json
{
  "ok": true,
  "data": {
    "order_id": 123,
    "status": "yetkazilmoqda"
  }
}
```

---

## 💳 To'lov URL'lari (Payment URLs)

### 1. Payme to'lov URL'ini olish
**GET** `/payment-url/{order_id}/payme`

**Javob:**
```json
{
  "payment_url": "https://checkout.paycom.uz/...",
  "order_id": 123,
  "amount": 30000000,
  "payment_system": "payme"
}
```

**Eslatma:** `amount` tiyin (kopeykalarda). 1 so'm = 100 tiyin.

---

### 2. Click to'lov URL'ini olish
**GET** `/payment-url/{order_id}/click`

**Javob:**
```json
{
  "payment_url": "https://my.click.uz/services/pay?...",
  "order_id": 123,
  "amount": 300000,
  "payment_system": "click"
}
```

**Eslatma:** `amount` so'mda.

---

### 3. Buyurtma to'lov ma'lumotlari
**GET** `/payment-url/{order_id}/payment-info`

**Javob:**
```json
{
  "order_id": 123,
  "status": "yangi",
  "payment_method": "click",
  "total_amount": 300000,
  "items": [
    {
      "product_id": 1,
      "product_name": "Ko'ylak",
      "quantity": 2,
      "price": 150000,
      "total": 300000
    }
  ],
  "customer": {
    "first_name": "Alisher",
    "last_name": "Valiyev",
    "contact": "+998901234567",
    "email": "alisher@example.com"
  }
}
```

---

## 🎯 Bannerlar (Main Photos)

### 1. Barcha bannerlarni olish
**GET** `/banners`

**Javob:**
```json
{
  "photos": [
    {
      "id": 1,
      "photo": {
        "path": "/media/banners/banner1.jpg",
        "url": "http://domain.com/media/banners/banner1.jpg"
      }
    }
  ]
}
```

---

### 2. Banner qo'shish (Admin)
**POST** `/banners`

**Headers:**
- `Authorization: Basic ...` (required)
- `Content-Type: multipart/form-data`

**Form data:**
- `photo` (file, required) - Rasm fayli

**Javob:**
```json
{
  "ok": true
}
```

---

### 3. Bannerni o'chirish (Admin)
**DELETE** `/banners/{photo_id}`

**Headers:**
- `Authorization: Basic ...` (required)

**Javob:**
```json
{
  "ok": true
}
```

---

## 📊 Umumiy ma'lumotlar

### Response formatlari

**Muvaffaqiyatli javob:**
```json
{
  "ok": true,
  "data": { ... },
  "meta": { ... }
}
```

**Xatolik javobi:**
```json
{
  "detail": "Xatolik tavsifi"
}
```

### HTTP Status kodlari

- `200` - Muvaffaqiyatli
- `201` - Yaratildi
- `400` - Noto'g'ri so'rov
- `401` - Autentifikatsiya talab qilinadi
- `403` - Ruxsat yo'q
- `404` - Topilmadi
- `409` - Konflikt (masalan: omborda mahsulot yetarli emas)
- `500` - Server xatoligi

---

## 🔄 To'lov jarayoni (Payment Flow)

### 1. Buyurtma yaratish
```
POST /order
```

### 2. To'lov URL'ini olish
```
GET /payment-url/{order_id}/payme
yoki
GET /payment-url/{order_id}/click
```

### 3. Foydalanuvchini to'lov sahifasiga yo'naltirish
```javascript
window.location.href = payment_url;
```

### 4. To'lov tizimi callback yuboradi
```
POST /payme (Payme uchun)
POST /click/prepare va /click/complete (Click uchun)
```

### 5. To'lovni tasdiqlash (Admin/Operator)
```
POST /order/{order_id}/confirm-payment
```

---

## 💡 Misollar

### JavaScript (Fetch API)

**Mahsulotlarni olish:**
```javascript
fetch('http://localhost:8000/products')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Buyurtma yaratish:**
```javascript
const orderData = {
  first_name: "Alisher",
  last_name: "Valiyev",
  country: "Uzbekistan",
  address: "Toshkent sh., Chilonzor",
  town_city: "Toshkent",
  contact: "+998901234567",
  postcode_zip: 100000,
  payment: "click",
  items: [
    {
      product_id: 1,
      product_item_id: 5,
      count: 2
    }
  ]
};

fetch('http://localhost:8000/order', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(orderData)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

**Admin autentifikatsiya bilan:**
```javascript
const username = 'admin';
const password = 'password123';
const token = btoa(`${username}:${password}`);

fetch('http://localhost:8000/products', {
  method: 'POST',
  headers: {
    'Authorization': `Basic ${token}`,
    'Content-Type': 'multipart/form-data'
  },
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### Axios

**Mahsulotlarni olish:**
```javascript
import axios from 'axios';

axios.get('http://localhost:8000/products')
  .then(response => console.log(response.data));
```

**Admin autentifikatsiya:**
```javascript
const auth = {
  username: 'admin',
  password: 'password123'
};

axios.post('http://localhost:8000/products', formData, {
  auth: auth,
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})
  .then(response => console.log(response.data));
```

---

## 🚀 Qo'shimcha ma'lumotlar

### CORS
API barcha originlarga ruxsat beradi (`Access-Control-Allow-Origin: *`).

### Rate Limiting
Buyurtma yaratish uchun: 120 so'rov/daqiqa (default).

### Media fayllar
Barcha rasm fayllar `/media/` papkasida saqlanadi va URL orqali ochiq.

**Misol:**
```
http://localhost:8000/media/products/photo1.jpg
```

### Swagger dokumentatsiya
API hujjatlarini interaktiv ko'rish uchun:
```
http://localhost:8000/docs
```

---

**Savol va takliflar uchun:** [GitHub Issues](https://github.com/your-repo/issues)
