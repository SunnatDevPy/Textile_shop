# Production Deployment Guide

## ✅ PRODUCTION GA TAYYOR

Barcha kritik muammolar hal qilindi!

---

## 🎉 Bajarilgan ishlar:

### 1. ✅ Admin Parol Hash Utility
**Fayl:** `generate_admin_hash.py`

**Ishlatish:**
```bash
python generate_admin_hash.py
```
- Parol kiritasiz
- Bcrypt hash generatsiya qilinadi
- Hash ni `.env` ga qo'yasiz

### 2. ✅ Global Error Handling
**Fayl:** `main.py`

**Qo'shilgan:**
- Validation errors uchun handler
- HTTP exceptions uchun handler
- Global exception handler (internal errorlarni yashiradi)
- User-friendly xabar qaytaradi

### 3. ✅ Global Rate Limiting
**Fayl:** `utils/rate_limit.py`

**Sozlamalar:**
- 120 request/minute (default)
- 1200 request/hour
- IP-based tracking
- Health checks va static files skip qilinadi
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

### 4. ✅ File Logging
**Fayl:** `utils/logger.py`

**Xususiyatlar:**
- Console + file logging
- Log fayl: `logs/textile_shop.log`
- Structured format
- Automatic log directory creation

### 5. ✅ Database Indexes
**Fayllar:** `main.py`, `create_indexes.py`

**Yaratilgan indexlar:**
- Products: category_id, collection_id, is_active
- Orders: status, created_at
- Order items: order_id
- Product items: product_id

---

## 📦 DEPLOYMENT QADAMLARI

### 1. Admin Parol Sozlash

```bash
# 1. Hash generatsiya qilish
python generate_admin_hash.py

# 2. .env faylni yangilash
nano .env
# ADMIN_PASS=<generated_hash>
```

### 2. Environment Variables Tekshirish

```bash
# .env faylda quyidagilar to'ldirilgan bo'lishi kerak:
DB_NAME=textile
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=<your_password>

ADMIN_USERNAME=superadmin
ADMIN_PASS=<bcrypt_hash>
SECRET_KEY=<random_64_char_string>

# Payment (agar kerak bo'lsa)
CLICK_SECRET_KEY=
CLICK_MERCHANT_ID=
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=

# Telegram (agar kerak bo'lsa)
TG_BOT_TOKEN=
TG_GROUP_IDS=
```

### 3. Docker Build va Run

```bash
# Build
docker build -t textile-shop-api .

# Run
docker run -d \
  --name textile-shop \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/media:/app/media \
  -v $(pwd)/logs:/app/logs \
  textile-shop-api
```

### 4. Docker Compose (Tavsiya etiladi)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: textile
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: always

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
    env_file:
      - .env
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
    depends_on:
      - postgres
    restart: always

volumes:
  postgres_data:
```

```bash
# Ishga tushirish
docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f api
```

### 5. Nginx Configuration (Optional)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Static files
    location /media/ {
        alias /app/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Admin panel
    location /admin/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # API
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
}
```

---

## 🔍 MONITORING

### 1. Loglarni Ko'rish

```bash
# Real-time logs
tail -f logs/textile_shop.log

# Docker logs
docker logs -f textile-shop

# Docker Compose logs
docker-compose logs -f api
```

### 2. Health Check

```bash
# API health
curl http://localhost:8000/system/health

# Database ready
curl http://localhost:8000/system/ready

# API docs
curl http://localhost:8000/docs
```

### 3. Performance Monitoring

Har bir response da:
- `X-Response-Time` header (milliseconds)
- `X-RateLimit-Limit` header
- `X-RateLimit-Remaining` header

### 4. Log Format

```
2026-05-05 14:13:48 | INFO     | HTTP Request | method=GET | path=/products | status=200 | duration_ms=45.23
2026-05-05 14:13:50 | WARNING  | Slow request detected | method=GET | path=/orders | duration_ms=1234.56
2026-05-05 14:13:52 | ERROR    | Exception: ValueError: ... | path=/order | method=POST
```

---

## 🧪 TESTING

### 1. Admin Login Test

```bash
# Generate hash
python generate_admin_hash.py
# Password: test123

# Test login
curl -u superadmin:test123 http://localhost:8000/panel/me
```

### 2. Rate Limit Test

```bash
# Send 130 requests (limit: 120/min)
for i in {1..130}; do
  curl http://localhost:8000/products
done

# Should get 429 Too Many Requests after 120
```

### 3. Error Handling Test

```bash
# Invalid data
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Should return user-friendly error
```

### 4. Performance Test

```bash
# Check response time header
curl -I http://localhost:8000/products
# X-Response-Time: 45.23ms
```

---

## 📊 PRODUCTION CHECKLIST

- [x] Admin parol hash qilish utility
- [x] Global error handling
- [x] Rate limiting (120/min, 1200/hour)
- [x] File logging (logs/textile_shop.log)
- [x] Database indexes
- [x] Performance monitoring
- [x] Caching (categories 10 min)
- [x] Query optimization
- [x] Docker support
- [x] Health checks
- [ ] .env faylni to'ldirish
- [ ] Admin parol hash generatsiya
- [ ] SECRET_KEY generatsiya
- [ ] Database backup strategiyasi
- [ ] SSL certificate (production)

---

## 🚀 PRODUCTION READY!

API va admin panel production ga chiqarishga tayyor.

**Keyingi qadamlar:**
1. `.env` faylni to'ldiring
2. Admin parol hash qiling
3. Docker build qiling
4. Test qiling
5. Production serverga deploy qiling

**Qo'shimcha tavsiyalar:**
- Database backup har kuni
- Log rotation (logrotate)
- SSL certificate (Let's Encrypt)
- Monitoring (Sentry/DataDog)
- CDN for static files

---

**Savol va muammolar uchun:** `logs/textile_shop.log` faylini tekshiring
