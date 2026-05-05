# 🏭 Textile Fabrika uchun Qo'shimcha Funksiyalar

## 📊 HOZIRGI HOLAT

Sizda mavjud:
- ✅ Mahsulotlar (kategoriya, kolleksiya, rang, o'lcham)
- ✅ Buyurtmalar
- ✅ Ombor (product_items - total_count)
- ✅ To'lov (Click/Payme)
- ✅ Admin panel

---

## 🎯 TAVSIYA ETILADIGAN FUNKSIYALAR

### 1. 📦 OMBOR BOSHQARUVI (Muhim!)

**Hozir:** Faqat `total_count` mavjud

**Qo'shish kerak:**

#### a) Ombor Harakatlari (Stock Movements)
```sql
CREATE TABLE stock_movements (
    id SERIAL PRIMARY KEY,
    product_item_id INTEGER REFERENCES product_items(id),
    movement_type VARCHAR(20), -- 'in' (kirim), 'out' (chiqim), 'adjustment' (tuzatish)
    quantity INTEGER,
    reason VARCHAR(50), -- 'purchase', 'sale', 'return', 'damage', 'correction'
    reference_id INTEGER, -- order_id yoki purchase_id
    notes TEXT,
    created_by INTEGER REFERENCES admin_users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Foyda:**
- Ombor tarixini ko'rish
- Kim, qachon, nima qilgan
- Audit trail

#### b) Minimal Qoldiq Ogohlantirish
```python
# models/products_model.py
class ProductItems:
    min_stock_level: int = 10  # Minimal qoldiq
    
    @property
    def is_low_stock(self):
        return self.total_count <= self.min_stock_level
```

**Foyda:**
- Mahsulot tugashidan oldin ogohlantirish
- Avtomatik buyurtma berish uchun signal

#### c) Ombor Lokatsiyasi
```sql
ALTER TABLE product_items ADD COLUMN warehouse_location VARCHAR(50);
-- Masalan: "A-12-3" (Sklad A, Qator 12, Javon 3)
```

---

### 2. 📈 STATISTIKA VA HISOBOTLAR

#### a) Dashboard Statistikasi
```python
# fast_routers/statistics.py

@router.get('/statistics/dashboard')
async def dashboard_stats():
    return {
        # Bugungi statistika
        'today': {
            'orders_count': ...,
            'revenue': ...,
            'new_customers': ...
        },
        
        # Haftalik
        'week': {
            'orders_count': ...,
            'revenue': ...,
            'top_products': [...]
        },
        
        # Oylik
        'month': {
            'orders_count': ...,
            'revenue': ...,
            'growth_percent': ...
        },
        
        # Ombor holati
        'inventory': {
            'low_stock_items': [...],
            'out_of_stock_items': [...],
            'total_value': ...
        }
    }
```

#### b) Sotuvlar Hisoboti
```python
@router.get('/reports/sales')
async def sales_report(
    date_from: str,
    date_to: str,
    group_by: str = 'day'  # day, week, month
):
    # Kunlik/haftalik/oylik sotuvlar grafigi
    # Excel export
```

#### c) Eng Ko'p Sotiladigan Mahsulotlar
```python
@router.get('/reports/top-products')
async def top_products(
    period: str = 'month',  # week, month, year
    limit: int = 10
):
    # TOP 10 mahsulotlar
    # Qaysi rang/o'lcham ko'proq sotilgan
```

#### d) Mijozlar Hisoboti
```python
@router.get('/reports/customers')
async def customers_report():
    # Eng ko'p buyurtma bergan mijozlar
    # Yangi vs qaytgan mijozlar
    # O'rtacha buyurtma summasi
```

---

### 3. 🏷️ CHEGIRMALAR VA AKSIYALAR

```sql
CREATE TABLE promotions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    discount_type VARCHAR(20), -- 'percent', 'fixed'
    discount_value INTEGER,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    -- Qaysi mahsulotlarga
    applies_to VARCHAR(20), -- 'all', 'category', 'product', 'collection'
    category_id INTEGER,
    product_id INTEGER,
    collection_id INTEGER,
    
    -- Minimal summa
    min_order_amount INTEGER,
    
    -- Promo kod
    promo_code VARCHAR(50) UNIQUE,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Foyda:**
- Sezonli chegirmalar
- Promo kodlar
- "2 ta ol, 1 ta bepul" kabi aksiyalar

---

### 4. 👥 MIJOZLAR BAZASI (CRM)

```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    
    -- Statistika
    total_orders INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    last_order_date TIMESTAMP,
    
    -- Loyallik
    loyalty_points INTEGER DEFAULT 0,
    customer_tier VARCHAR(20), -- 'bronze', 'silver', 'gold'
    
    -- Marketing
    email_subscribed BOOLEAN DEFAULT false,
    sms_subscribed BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Orders jadvaliga customer_id qo'shish
ALTER TABLE orders ADD COLUMN customer_id INTEGER REFERENCES customers(id);
```

**Foyda:**
- Mijozlar tarixi
- Loyallik dasturi
- Marketing kampaniyalari
- Qayta buyurtma berish oson

---

### 5. 📱 TELEGRAM BOT YAXSHILASH

Hozir: Faqat yangi buyurtma haqida xabar

**Qo'shish kerak:**

```python
# Telegram bot commands:

/stats - Bugungi statistika
/orders - Yangi buyurtmalar
/lowstock - Kam qolgan mahsulotlar
/revenue - Bugungi daromad

# Inline buttons:
- Buyurtmani tasdiqlash
- Statusni o'zgartirish
- Mijozga xabar yuborish
```

---

### 6. 🔔 NOTIFIKATSIYALAR

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50), -- 'low_stock', 'new_order', 'payment_received'
    title VARCHAR(255),
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    user_id INTEGER REFERENCES admin_users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Admin panelda:**
- Bell icon bilan yangi notifikatsiyalar
- Real-time updates (WebSocket yoki polling)

---

### 7. 📸 MAHSULOT GALEREYASI

Hozir: Faqat bitta rasm (`product_photos`)

**Yaxshilash:**
```python
# Bir mahsulotga ko'p rasm
# Asosiy rasm + qo'shimcha rasmlar
# Rang bo'yicha turli rasmlar
```

---

### 8. 🚚 YETKAZIB BERISH

```sql
CREATE TABLE delivery_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100), -- "Toshkent shahri", "Samarqand"
    delivery_cost INTEGER,
    delivery_days INTEGER, -- Necha kunda yetkaziladi
    is_active BOOLEAN DEFAULT true
);

ALTER TABLE orders ADD COLUMN delivery_zone_id INTEGER;
ALTER TABLE orders ADD COLUMN delivery_cost INTEGER;
ALTER TABLE orders ADD COLUMN tracking_number VARCHAR(100);
```

---

### 9. 📊 EXCEL IMPORT/EXPORT

**Hozir:** Faqat export mavjud

**Qo'shish:**
```python
# Mahsulotlarni Excel orqali import qilish
# Template yuklab olish
# Bulk operations (ko'p mahsulotni bir vaqtda qo'shish)
```

---

### 10. 🔍 QIDIRUV YAXSHILASH

```python
# Full-text search
# Filters:
- Narx oralig'i
- Rang
- O'lcham
- Kategoriya
- Kolleksiya
- Mavjudligi (in stock / out of stock)

# Sorting:
- Narx (arzon -> qimmat)
- Yangi mahsulotlar
- Mashhur mahsulotlar
```

---

## 🎯 PRIORITET BO'YICHA

### 🔴 YUQORI PRIORITET (1-2 hafta)

1. **Ombor harakatlari** - Audit uchun juda muhim
2. **Dashboard statistikasi** - Biznes ko'rsatkichlari
3. **Minimal qoldiq ogohlantirish** - Mahsulot tugamasligi uchun
4. **Telegram bot yaxshilash** - Tezkor boshqaruv

### 🟡 O'RTA PRIORITET (2-4 hafta)

5. **Mijozlar bazasi (CRM)** - Marketing uchun
6. **Hisobotlar** - Tahlil qilish uchun
7. **Chegirmalar** - Sotuvni oshirish
8. **Notifikatsiyalar** - Admin uchun qulay

### 🟢 PAST PRIORITET (keyinroq)

9. **Yetkazib berish** - Agar kerak bo'lsa
10. **Excel import** - Bulk operations uchun
11. **Mahsulot galereyasi** - Ko'proq rasmlar
12. **Qidiruv yaxshilash** - UX yaxshilash

---

## 💰 VAQT VA NARX BAHOLASH

| Funksiya | Vaqt | Murakkablik |
|----------|------|-------------|
| Ombor harakatlari | 2-3 kun | O'rta |
| Dashboard statistika | 3-4 kun | O'rta |
| Minimal qoldiq | 1 kun | Oson |
| Telegram bot | 2-3 kun | O'rta |
| CRM | 4-5 kun | Qiyin |
| Hisobotlar | 3-4 kun | O'rta |
| Chegirmalar | 3-4 kun | O'rta |
| Notifikatsiyalar | 2-3 kun | O'rta |

**Jami (Yuqori prioritet):** ~2 hafta

---

## 🚀 KEYINGI QADAM

Qaysi funksiyani birinchi qo'shishni xohlaysiz?

**Tavsiya:** Ombor harakatlari + Dashboard statistika bilan boshlash
