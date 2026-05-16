# 🚀 Serverda ishga tushirish - Qisqa qo'llanma

## Sizda allaqachon bor:
- ✅ Domen: textile.okach-admin.uz
- ✅ SSL sertifikat

## 1️⃣ Serverga loyihani ko'chirish

```bash
# Local kompyuterdan serverga ko'chirish
scp -r C:/Users/stalk/FastAPIProject/Textile_shop user@textile.okach-admin.uz:/var/www/

# Yoki serverdagi git orqali
ssh user@textile.okach-admin.uz
cd /var/www
git clone https://github.com/your-repo/textile-shop.git
```

## 2️⃣ Serverdagi amallar

```bash
# Serverga kirish
ssh user@textile.okach-admin.uz

# Loyiha katalogiga o'tish
cd /var/www/textile-shop

# .env faylini sozlash
nano .env
# DB_HOST=db ga o'zgartiring (docker uchun)
# Parollarni o'zgartiring

# Deploy skriptini ishga tushirish
chmod +x deploy.sh
./deploy.sh
```

## 3️⃣ Nginx sozlash

```bash
# Nginx konfiguratsiyasini ko'chirish
sudo cp nginx-server.conf /etc/nginx/sites-available/textile-shop

# Symlink yaratish
sudo ln -sf /etc/nginx/sites-available/textile-shop /etc/nginx/sites-enabled/

# Eski konfiguratsiyani o'chirish (agar bor bo'lsa)
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx konfiguratsiyasini tekshirish
sudo nginx -t

# Nginx'ni qayta yuklash
sudo systemctl reload nginx
```

## 4️⃣ Tekshirish

```bash
# Container'lar ishlayotganini tekshirish
docker-compose ps

# Loglarni ko'rish
docker-compose logs -f app

# Health check
curl http://localhost:8000/system/health

# Brauzerda ochish
https://textile.okach-admin.uz/admin
https://textile.okach-admin.uz/docs
```

## 5️⃣ Muammolarni hal qilish

### Container ishlamayapti
```bash
docker-compose logs app
docker-compose restart app
```

### Database xatolik
```bash
docker-compose logs db
docker-compose restart db
```

### Nginx xatolik
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

## 📋 Foydali buyruqlar

```bash
# Container'larni qayta ishga tushirish
docker-compose restart

# Yangi kod deploy qilish
git pull
./deploy.sh

# Loglarni ko'rish
docker-compose logs -f

# Container'larni to'xtatish
docker-compose down

# Database backup
docker exec textile_db pg_dump -U postgres textile > backup.sql
```

## 🌐 URL'lar

- **Admin Panel**: https://textile.okach-admin.uz/admin
- **API Docs**: https://textile.okach-admin.uz/docs
- **Dashboard**: https://textile.okach-admin.uz/dashboard/statistics
- **Health Check**: https://textile.okach-admin.uz/system/health

## ⚠️ Muhim

1. `.env` faylida `DB_HOST=db` bo'lishi kerak (docker uchun)
2. SSL sertifikat yo'li to'g'ri bo'lishi kerak
3. Firewall 80 va 443 portlarni ochiq bo'lishi kerak
4. Docker va Docker Compose o'rnatilgan bo'lishi kerak

## 🔐 Xavfsizlik

- ✅ `.env` faylida kuchli parollar
- ✅ `SECRET_KEY` o'zgartirilgan
- ✅ Database paroli o'zgartirilgan
- ✅ SSL yoqilgan
- ✅ Firewall sozlangan
