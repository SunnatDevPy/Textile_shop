# 🎯 QUICK START GUIDE

## Tezkor Ishga Tushirish

### 1. Frontend Build (5 daqiqa)
```bash
cd D:\Textile_shop\frontend-react
npm install
npm run build
cd ..
```

### 2. Docker Deploy (2 daqiqa)
```bash
cd D:\Textile_shop
docker-compose up -d --build
```

### 3. Admin Panelga Kirish
```
URL: http://localhost:8000/admin/
yoki: https://textile.okach-admin.uz/admin/
```

### 4. Yangi Funksiyalarni Sinab Ko'rish

#### 📊 Statistika
1. Admin panelda "📊 Statistika" tabni oching
2. Bugungi/haftalik/oylik daromadni ko'ring
3. TOP mahsulotlarni ko'ring
4. Ombor holatini tekshiring

#### 📦 Ombor Harakatlari
1. "📦 Ombor" tabni oching
2. Kirim/chiqim/tuzatish harakatlarini ko'ring
3. Statistikani ko'ring

#### ⚠️ Ogohlantirishlar
1. "⚠️ Ogohlantirishlar" tabni oching
2. Kam qolgan mahsulotlarni ko'ring
3. Tugagan mahsulotlarni ko'ring

#### 🤖 Bot Sozlash
1. "🤖 Bot" tabni oching
2. Bot token kiriting (BotFather dan)
3. Group IDs kiriting (vergul bilan ajratilgan)
4. "Bot yoqilgan" checkboxni belgilang
5. Notification sozlamalarini tanlang
6. "Saqlash" tugmasini bosing
7. "Bot ulanishini test qilish" tugmasini bosing

#### 🔍 Qidiruv Test
1. "Mahsulotlar" tabga o'ting
2. Advanced search ishlatib ko'ring:
   - Rang bo'yicha filter
   - O'lcham bo'yicha filter
   - Narx oralig'i
   - Omborda mavjudligi
   - Sorting

---

## 🔧 Muammolarni Hal Qilish

### Frontend build xatosi
```bash
cd frontend-react
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Docker xatosi
```bash
docker-compose down
docker-compose up -d --build
```

### Database migration xatosi
```bash
# main.py da avtomatik migration mavjud
# Agar xato bo'lsa, loglarni ko'ring:
docker-compose logs -f api
```

---

## 📊 API Test (Swagger)

```
URL: http://localhost:8000/docs
yoki: https://textile.okach-admin.uz/docs
```

Yangi endpointlar:
- `/stock-movements/` - Ombor harakatlari
- `/dashboard/statistics` - Dashboard statistikasi
- `/alerts/low-stock` - Kam qolgan mahsulotlar
- `/bot-settings/` - Bot sozlamalari
- `/products/search/advanced` - Kengaytirilgan qidiruv

---

## ✅ Tayyor!

Barcha funksiyalar ishlaydi va production ga tayyor.

Savol yoki muammo bo'lsa:
- `logs/textile_shop.log` - Application logs
- `docker-compose logs -f api` - Container logs
- `/system/health` - Health check endpoint
