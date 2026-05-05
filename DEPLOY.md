# 🚀 DEPLOYMENT GUIDE

## ✅ O'zgarishlar

### Frontend
- ✅ Nginx proxy sozlandi: `/api/*` → `http://app:8000/`
- ✅ Base URL o'zgartirildi: `window.location.origin` → `/api`
- ✅ Frontend endi backend bilan bir docker network ichida ishlaydi

### Docker Compose
- ✅ Frontend service qo'shildi (port 3000)
- ✅ Backend API (port 8000)
- ✅ PostgreSQL (port 5431)
- ✅ Telegram Bot

---

## 📦 ISHGA TUSHIRISH

```bash
cd D:\Textile_shop

# Barcha servislarni build va ishga tushirish
docker-compose up -d --build

# Loglarni kuzatish
docker-compose logs -f

# Faqat bitta servisni qayta build qilish
docker-compose up -d --build frontend
docker-compose up -d --build app
```

---

## 🔍 TEKSHIRISH

### Local (Development)
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs
- **Database:** localhost:5431
- **Health check:** http://localhost:8000/system/health

### Production (Server)
- **Sayt:** https://textile.okach-admin.uz
- **Admin Panel:** https://textile.okach-admin.uz (login page)
- **API Docs:** https://textile.okach-admin.uz/docs
- **Health check:** https://textile.okach-admin.uz/system/health

---

## ⚙️ NGINX KONFIGURATSIYA (Server)

Serverda Nginx sozlash:

```bash
# Nginx konfiguratsiyasini nusxalash
sudo cp nginx-server.conf /etc/nginx/sites-available/textile.okach-admin.uz

# Symlink yaratish
sudo ln -s /etc/nginx/sites-available/textile.okach-admin.uz /etc/nginx/sites-enabled/

# Konfiguratsiyani tekshirish
sudo nginx -t

# Nginx ni qayta yuklash
sudo systemctl reload nginx
```

**Konfiguratsiya tuzilishi:**
- `https://textile.okach-admin.uz/` → Frontend (port 3000)
- `https://textile.okach-admin.uz/api/` → Backend API (port 8000)
- `https://textile.okach-admin.uz/docs` → API Documentation
- `https://textile.okach-admin.uz/media/` → Media files

**SSL Sertifikat (Let's Encrypt):**
```bash
# Certbot o'rnatish
sudo apt install certbot python3-certbot-nginx

# SSL sertifikat olish
sudo certbot --nginx -d textile.okach-admin.uz

# Avtomatik yangilanish
sudo certbot renew --dry-run
```

---

## 🔐 .ENV FAYL

Serverda `.env` faylni tekshiring:

```env
# Database
DB_HOST=db
DB_PORT=5432
DB_NAME=textile
DB_USER=postgres
DB_PASSWORD=1

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password

# Telegram Bot (optional)
BOT_TOKEN=
GROUP_IDS=

# Payment (optional)
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=
CLICK_MERCHANT_ID=
CLICK_SECRET_KEY=
```

---

## 📊 YANGI FUNKSIYALAR

### 1. Dashboard Statistikasi
- **Endpoint:** `/dashboard/statistics`
- **Frontend:** "📊 Statistika" tab
- Bugun/Hafta/Oy daromad va buyurtmalar
- TOP mahsulotlar
- Ombor holati

### 2. Ombor Harakatlari
- **Endpoint:** `/stock-movements/`
- **Frontend:** "📦 Ombor" tab
- Kirim/Chiqim/Tuzatish
- Mahsulot tarixi
- Audit uchun

### 3. Kam Qoldiq Ogohlantirish
- **Endpoint:** `/alerts/low-stock`
- **Frontend:** "⚠️ Ogohlantirishlar" tab
- Kam qolgan mahsulotlar
- Tugagan mahsulotlar
- Minimal qoldiq sozlash

### 4. Bot Sozlamalari
- **Endpoint:** `/bot-settings/`
- **Frontend:** "🤖 Bot" tab
- Bot token sozlash
- Group ID avtomatik olish
- Notification sozlamalari

---

## 🐛 TROUBLESHOOTING

### Frontend API ga ulanmayapti
```bash
# Frontend containerini tekshirish
docker logs textile_frontend

# Nginx konfiguratsiyasini tekshirish
docker exec textile_frontend cat /etc/nginx/conf.d/default.conf
```

### Backend ishlamayapti
```bash
# Backend loglarini ko'rish
docker logs textile_app

# Database ulanishini tekshirish
docker exec textile_app python -c "from models import db; print('DB OK')"
```

### Database migration kerak
```bash
# Container ichida migration
docker exec textile_app python -c "from main import migrate_db; import asyncio; asyncio.run(migrate_db())"
```

---

## 🔄 YANGILASH

```bash
cd D:\Textile_shop

# Git pull (agar git ishlatilsa)
git pull

# Rebuild va restart
docker-compose down
docker-compose up -d --build

# Loglarni tekshirish
docker-compose logs -f
```

---

## ✅ PRODUCTION CHECKLIST

- [ ] `.env` fayl to'ldirilgan
- [ ] Admin parol o'zgartirilgan
- [ ] Database backup sozlangan
- [ ] SSL sertifikat o'rnatilgan (Let's Encrypt)
- [ ] Firewall sozlangan
- [ ] Monitoring sozlangan (optional)
- [ ] Bot token va Group ID sozlangan
- [ ] Payment credentials sozlangan

---

**Keyingi qadam:** Serverga deploy qilish va test! 🚀
