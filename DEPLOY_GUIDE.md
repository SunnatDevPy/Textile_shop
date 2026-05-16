# Textile Shop - Server Deploy Guide

## Serverda ishga tushirish bo'yicha to'liq qo'llanma

### 1. Server tayyorlash

```bash
# Servergа SSH orqali kirish
ssh user@your-server.com

# Kerakli paketlarni o'rnatish
sudo apt update
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git

# Docker'ni ishga tushirish
sudo systemctl start docker
sudo systemctl enable docker

# Foydalanuvchini docker guruhiga qo'shish
sudo usermod -aG docker $USER
```

### 2. Loyihani serverga ko'chirish

```bash
# Loyiha katalogini yaratish
sudo mkdir -p /var/www/textile-shop
sudo chown $USER:$USER /var/www/textile-shop
cd /var/www/textile-shop

# Git orqali loyihani clone qilish (yoki scp/rsync bilan ko'chirish)
git clone https://github.com/your-repo/textile-shop.git .

# Yoki local'dan serverga ko'chirish (local kompyuterdan):
# rsync -avz --exclude='.venv' --exclude='node_modules' \
#   C:/Users/stalk/FastAPIProject/Textile_shop/ \
#   user@your-server.com:/var/www/textile-shop/
```

### 3. Environment o'zgaruvchilarini sozlash

```bash
cd /var/www/textile-shop

# .env faylini yaratish
nano .env
```

**.env fayl mazmuni:**
```env
# Database
DB_NAME=textile
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASS=your_strong_password_here

# Admin
ADMIN_USERNAME=admin
ADMIN_PASS=$2b$12$3ek5PJI26NPXkSBM1D26He/T0E4mUwOsaugF2JkflbGSKVVeojwsy
SECRET_KEY=your_secret_key_here_change_this

# Payment systems
CLICK_SECRET_KEY=your_click_secret
CLICK_MERCHANT_ID=your_merchant_id
CLICK_SERVICE_ID=your_service_id
PAYME_MERCHANT_ID=your_payme_merchant_id
PAYME_SECRET_KEY=your_payme_secret

# Telegram Bot
TG_BOT_TOKEN=your_bot_token
TG_GROUP_IDS=your_group_ids
TG_WEBHOOK_URL=https://your-domain.com/telegram/webhook
TG_WEBHOOK_SECRET=your_webhook_secret

# Rate limiting
RATE_LIMIT_PER_MINUTE=120

# SMTP (optional)
SMTP_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 4. Docker bilan ishga tushirish

```bash
cd /var/www/textile-shop

# Docker image'larni build qilish va ishga tushirish
sudo docker-compose up -d --build

# Loglarni ko'rish
sudo docker-compose logs -f

# Statusni tekshirish
sudo docker-compose ps
```

**Natija:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Database: localhost:5431

### 5. Nginx konfiguratsiyasi

```bash
# Nginx konfiguratsiya faylini yaratish
sudo nano /etc/nginx/sites-available/textile-shop
```

**Nginx konfiguratsiya (SSL bilan):**
```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL sertifikatlar
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL sozlamalari
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Client max body size (file upload uchun)
    client_max_body_size 50M;

    # Frontend (Admin Panel) - React SPA
    location /admin {
        proxy_pass http://localhost:8000/admin;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }

    # Media files
    location /media/ {
        proxy_pass http://localhost:8000/media/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Health check
    location /system/health {
        proxy_pass http://localhost:8000/system/health;
        proxy_http_version 1.1;
        access_log off;
    }

    # Dashboard endpoints
    location /dashboard/ {
        proxy_pass http://localhost:8000/dashboard/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Telegram webhook
    location /telegram/ {
        proxy_pass http://localhost:8000/telegram/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Payment callbacks (Payme, Click)
    location /payme/ {
        proxy_pass http://localhost:8000/payme/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /click/ {
        proxy_pass http://localhost:8000/click/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript 
               application/xml image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logs
    access_log /var/log/nginx/textile-shop-access.log;
    error_log /var/log/nginx/textile-shop-error.log;
}
```

### 6. Nginx'ni yoqish

```bash
# Konfiguratsiyani yoqish
sudo ln -s /etc/nginx/sites-available/textile-shop /etc/nginx/sites-enabled/

# Nginx konfiguratsiyasini tekshirish
sudo nginx -t

# Nginx'ni qayta yuklash
sudo systemctl reload nginx
```

### 7. SSL sertifikat o'rnatish (Let's Encrypt)

```bash
# Certbot bilan SSL sertifikat olish
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Avtomatik yangilanishni tekshirish
sudo certbot renew --dry-run
```

### 8. Firewall sozlash

```bash
# UFW firewall'ni yoqish
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Statusni tekshirish
sudo ufw status
```

### 9. Foydali buyruqlar

```bash
# Docker container'larni ko'rish
sudo docker-compose ps

# Loglarni ko'rish
sudo docker-compose logs -f app
sudo docker-compose logs -f frontend
sudo docker-compose logs -f bot

# Container'ni qayta ishga tushirish
sudo docker-compose restart app

# Container'larni to'xtatish
sudo docker-compose down

# Container'larni o'chirish va qayta build qilish
sudo docker-compose down
sudo docker-compose up -d --build

# Database backup
sudo docker exec textile_db pg_dump -U postgres textile > backup_$(date +%Y%m%d).sql

# Database restore
sudo docker exec -i textile_db psql -U postgres textile < backup_20260506.sql
```

### 10. Monitoring va Logs

```bash
# Nginx loglarini ko'rish
sudo tail -f /var/log/nginx/textile-shop-access.log
sudo tail -f /var/log/nginx/textile-shop-error.log

# Docker loglarini ko'rish
sudo docker-compose logs -f --tail=100

# Disk space tekshirish
df -h

# Memory usage
free -h

# Docker disk usage
sudo docker system df
```

### 11. Yangilanishlar

```bash
cd /var/www/textile-shop

# Yangi kodni olish
git pull origin main

# Container'larni qayta build qilish
sudo docker-compose down
sudo docker-compose up -d --build

# Nginx'ni reload qilish
sudo systemctl reload nginx
```

## Muhim URL'lar

- **Admin Panel**: https://your-domain.com/admin
- **API Docs**: https://your-domain.com/docs
- **Health Check**: https://your-domain.com/system/health
- **Dashboard**: https://your-domain.com/dashboard/statistics

## Xavfsizlik

1. ✅ `.env` faylida kuchli parollar ishlatish
2. ✅ `SECRET_KEY`ni o'zgartirish
3. ✅ Database parolini o'zgartirish
4. ✅ SSL sertifikat o'rnatish
5. ✅ Firewall sozlash
6. ✅ Regular backup qilish
7. ✅ Docker container'larni yangilab turish

## Muammolarni hal qilish

### Container ishlamayapti
```bash
sudo docker-compose logs app
sudo docker-compose restart app
```

### Database ulanmayapti
```bash
sudo docker-compose logs db
sudo docker exec -it textile_db psql -U postgres -d textile
```

### Nginx xatolik beradi
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### SSL muammolari
```bash
sudo certbot certificates
sudo certbot renew --force-renewal
```

## Qo'shimcha

- Barcha parollarni `.env` faylida saqlang
- Regular backup oling
- Loglarni monitoring qiling
- SSL sertifikatni 90 kundan keyin yangilang (avtomatik)
