#!/bin/bash
# Serverga yangilangan faylni yuklash va qayta ishga tushirish

echo "📦 Textile Shop - Server Update Script"
echo "======================================="

# Serverga ulanish ma'lumotlari (o'zgartiring)
SERVER_USER="your_user"
SERVER_HOST="textile.okach-admin.uz"
SERVER_PATH="/var/www/textile_shop"

echo ""
echo "1️⃣ Faylni serverga yuklash..."
scp D:/Textile_shop/fast_routers/bot_settings.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/fast_routers/

echo ""
echo "2️⃣ Serverda Docker rebuild..."
ssh ${SERVER_USER}@${SERVER_HOST} << 'EOF'
cd /var/www/textile_shop
docker-compose up -d --build app bot
docker-compose logs -f app --tail 20
EOF

echo ""
echo "✅ Yangilash tugadi!"
