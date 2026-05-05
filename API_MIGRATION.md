# API Migration Guide - `/api` Prefix

## O'zgarishlar

### 1. Barcha API endpointlar `/api` prefix bilan ishlaydi

**Eski URL'lar:**
```
GET  /products
POST /order
GET  /dashboard/statistics
GET  /docs
```

**Yangi URL'lar:**
```
GET  /api/products
POST /api/order
GET  /api/dashboard/statistics
GET  /api/docs
```

### 2. Frontend root pathda

**Eski:**
- Frontend: `/admin`
- API: `/products`, `/order`, etc.

**Yangi:**
- Frontend: `/` (root)
- API: `/api/products`, `/api/order`, etc.

---

## URL Mapping

| Endpoint Type | Old URL | New URL |
|--------------|---------|---------|
| Products | `/products` | `/api/products` |
| Orders | `/order` | `/api/order` |
| Categories | `/categories` | `/api/categories` |
| Collections | `/collections` | `/api/collections` |
| Colors | `/colors` | `/api/colors` |
| Sizes | `/sizes` | `/api/sizes` |
| Dashboard | `/dashboard/statistics` | `/api/dashboard/statistics` |
| Stock Movements | `/stock-movements` | `/api/stock-movements` |
| Admin Users | `/admin-users` | `/api/admin-users` |
| Payments | `/payments` | `/api/payments` |
| Payme | `/payme` | `/api/payme` |
| Click | `/click` | `/api/click` |
| Telegram | `/telegram` | `/api/telegram` |
| System | `/system/health` | `/api/system/health` |
| API Docs | `/docs` | `/api/docs` |
| ReDoc | `/redoc` | `/api/redoc` |
| OpenAPI JSON | `/openapi.json` | `/api/openapi.json` |
| Media Files | `/media/` | `/media/` (o'zgarmadi) |
| Frontend | `/admin` | `/` (root) |

---

## Frontend o'zgarishlari

Agar frontend kodida API chaqiruvlar bo'lsa, ularni yangilash kerak:

**JavaScript/React:**
```javascript
// Eski
fetch('/products')
fetch('/order', { method: 'POST', ... })

// Yangi
fetch('/api/products')
fetch('/api/order', { method: 'POST', ... })
```

**Axios:**
```javascript
// Eski
axios.get('/products')
axios.post('/order', data)

// Yangi
axios.get('/api/products')
axios.post('/api/order', data)

// Yoki base URL sozlash
const api = axios.create({
  baseURL: '/api'
});

api.get('/products')  // /api/products ga boradi
api.post('/order', data)  // /api/order ga boradi
```

---

## Testing

### Local Development

```bash
# Backend ishga tushirish
uvicorn main:app --reload

# Test qilish
curl http://localhost:8000/api/products
curl http://localhost:8000/api/system/health
curl http://localhost:8000/api/docs  # Swagger UI

# Frontend
curl http://localhost:8000/  # React SPA
```

### Production (Docker)

```bash
# Container'larni qayta build qilish
docker-compose down
docker-compose up -d --build

# Test qilish
curl https://textile.okach-admin.uz/api/products
curl https://textile.okach-admin.uz/api/docs
curl https://textile.okach-admin.uz/  # Frontend
```

---

## Nginx sozlash

Yangi `nginx-server.conf` fayli allaqachon yangilangan. Serverda qo'llash:

```bash
# Nginx konfiguratsiyasini yangilash
sudo cp nginx-server.conf /etc/nginx/sites-available/textile-shop

# Nginx'ni test qilish
sudo nginx -t

# Nginx'ni qayta yuklash
sudo systemctl reload nginx
```

---

## Muhim eslatmalar

1. ✅ **Media files** `/media/` pathda qoladi (o'zgarmaydi)
2. ✅ **Frontend** endi root pathda (`/`)
3. ✅ **Barcha API** `/api` prefix bilan
4. ✅ **API Documentation** `/api/docs` da
5. ⚠️ **Frontend kodini yangilash** kerak (agar API chaqiruvlar bo'lsa)
6. ⚠️ **Payme/Click webhook URL'larini** yangilash kerak payment provider'da

---

## Payme/Click Webhook URL'lari

Payment provider'larda webhook URL'larini yangilash kerak:

**Eski:**
```
https://textile.okach-admin.uz/payme
https://textile.okach-admin.uz/click
```

**Yangi:**
```
https://textile.okach-admin.uz/api/payme
https://textile.okach-admin.uz/api/click
```

---

## Rollback (agar kerak bo'lsa)

Agar muammo bo'lsa, eski versiyaga qaytish:

```bash
# Git orqali
git checkout HEAD~1 main.py nginx-server.conf

# Yoki qo'lda
# main.py da barcha `prefix="/api"` ni o'chirish
# nginx-server.conf eski versiyasini qaytarish
```
