# Production Deployment Checklist

## ❌ HOZIR PRODUCTION GA CHIQARISHGA TAYYOR EMAS

Quyidagi muhim muammolar hal qilinishi kerak:

---

## 🔴 KRITIK MUAMMOLAR (Majburiy)

### 1. Security Xavflari

#### a) CORS - Hamma domenga ochiq
```python
# main.py - line 120-125
allow_origins=["*"]  # ❌ XAVFli!
```
**Yechim:**
```python
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

#### b) Admin parol bcrypt hash emas
```python
# .env.example - line 14
ADMIN_PASS=<bcrypt_hash_here>  # ❌ Hali hash qilinmagan
```
**Yechim:**
```bash
python check_bcrypt_password.py
# Yangi hash yarating va .env ga qo'ying
```

#### c) SECRET_KEY weak
```python
# .env.example - line 15
SECRET_KEY=<random_secret_key>  # ❌ Default qiymat
```
**Yechim:**
```python
import secrets
print(secrets.token_urlsafe(64))
# Natijani .env ga qo'ying
```

### 2. Database Connection Pool

```python
# config.py
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```
**Muammo:** Production load uchun kichik bo'lishi mumkin

**Tavsiya:**
- POOL_SIZE: 50-100
- MAX_OVERFLOW: 50-100
- Monitoring qo'shing

### 3. Rate Limiting

```python
# Faqat order yaratish uchun mavjud
RATE_LIMIT_PER_MINUTE=120
```
**Muammo:** Barcha endpointlar himoyasiz

**Yechim:** Global rate limiting qo'shing

### 4. Error Handling

```python
# main.py - middleware
except Exception as e:
    logger.error_with_trace(e, ...)
    raise  # ❌ User ga internal error ko'rinadi
```
**Yechim:** Custom error handler qo'shing

---

## 🟡 MUHIM YAXSHILANISHLAR (Tavsiya etiladi)

### 5. Frontend Build

```dockerfile
# Dockerfile - frontend build mavjud ✅
FROM node:24-alpine AS frontend_builder
```
**Yaxshi:** Multi-stage build ishlatilgan

**Qo'shimcha:** 
- Build vaqtida environment variables
- Production optimizatsiya

### 6. Static Files

```python
# main.py
app.mount("/media", StaticFiles(directory='media'))
```
**Muammo:** Production da Nginx/CDN ishlatish kerak

**Yechim:** 
- Nginx static files uchun
- S3/CloudFlare CDN

### 7. Database Migrations

```python
# main.py - lifespan
await db.execute(text("ALTER TABLE..."))
```
**Muammo:** Manual migration, versioning yo'q

**Yechim:** Alembic ishlatish

### 8. Monitoring va Logging

```python
# utils/logger.py - console logging
handler = logging.StreamHandler(sys.stdout)
```
**Muammo:** Faqat console, persistence yo'q

**Yechim:**
- File logging
- Sentry/DataDog
- Prometheus metrics

### 9. Health Checks

```python
# fast_routers/system.py
@system_router.get('/system/health')
@system_router.get('/system/ready')
```
**Yaxshi:** Health checks mavjud ✅

**Qo'shimcha:** Database connection check

### 10. Environment Variables

```bash
# .env.example
SMTP_ENABLED=false
TG_BOT_TOKEN=
```
**Muammo:** Ko'p bo'sh qiymatlar

**Tekshirish kerak:**
- Payment credentials (Click/Payme)
- SMTP sozlamalari
- Telegram bot

---

## 🟢 YAXSHI TOMONLAR

✅ Docker support  
✅ Multi-stage build  
✅ Connection pooling  
✅ Structured logging  
✅ Performance monitoring  
✅ Caching mexanizmi  
✅ Database query optimizatsiyasi  
✅ Admin panel tayyor  
✅ API documentation (Swagger)  
✅ Health checks  

---

## 📋 PRODUCTION DEPLOYMENT QADAMLARI

### 1. Security Fix (1-2 soat)

```bash
# 1. CORS sozlash
# main.py da allow_origins o'zgartiring

# 2. Admin parol hash qilish
python check_bcrypt_password.py
# Natijani .env ga qo'ying

# 3. SECRET_KEY generatsiya
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Natijani .env ga qo'ying

# 4. Payment credentials
# Click va Payme dan olingan keylarni qo'ying
```

### 2. Error Handling (1 soat)

```python
# main.py ga qo'shing
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error_with_trace(exc, {"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### 3. Rate Limiting (30 daqiqa)

```python
# Global rate limiting qo'shing
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### 4. Database Indexes (15 daqiqa)

```sql
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_collection ON products(collection_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);
```

### 5. Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Static files
    location /media/ {
        alias /app/media/;
        expires 30d;
    }

    # API
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6. Docker Compose Production

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
    depends_on:
      - postgres
    restart: always

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: textile
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./media:/app/media
    depends_on:
      - api
    restart: always

volumes:
  postgres_data:
```

---

## ⏱️ VAQT BAHOLASH

| Task | Vaqt | Prioritet |
|------|------|-----------|
| Security fixes | 2 soat | 🔴 Kritik |
| Error handling | 1 soat | 🔴 Kritik |
| Rate limiting | 30 min | 🔴 Kritik |
| Database indexes | 15 min | 🟡 Muhim |
| Nginx setup | 1 soat | 🟡 Muhim |
| Monitoring setup | 2 soat | 🟢 Tavsiya |
| **JAMI** | **~7 soat** | |

---

## 🎯 XULOSA

**Hozirgi holat:** 70% tayyor

**Qolgan ishlar:**
1. ✅ API va admin panel funksional
2. ✅ Optimizatsiya qilingan
3. ❌ Security xavflari mavjud
4. ❌ Production sozlamalari yo'q
5. ❌ Monitoring to'liq emas

**Tavsiya:** 
- Minimal 1 kun (7-8 soat) qo'shimcha ish kerak
- Security muammolarini hal qilmasdan production ga chiqarmang
- Staging environment da test qiling

**Keyingi qadam:** Security fixlarni amalga oshirish?
