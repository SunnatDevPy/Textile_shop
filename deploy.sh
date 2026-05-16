#!/bin/bash

# Textile Shop - Quick Deploy Script
# Bu skript loyihani serverda tez ishga tushirish uchun

set -e

echo "=========================================="
echo "Textile Shop - Deploy Script"
echo "=========================================="

# 1. Docker va Docker Compose mavjudligini tekshirish
if ! command -v docker &> /dev/null; then
    echo "❌ Docker o'rnatilmagan. O'rnatish uchun:"
    echo "sudo apt install -y docker.io docker-compose"
    exit 1
fi

# 2. .env faylini tekshirish
if [ ! -f .env ]; then
    echo "❌ .env fayli topilmadi!"
    echo "Iltimos, .env.example'dan nusxa oling va to'ldiring:"
    echo "cp .env.example .env"
    echo "nano .env"
    exit 1
fi

# 3. Docker container'larni to'xtatish
echo "🛑 Eski container'larni to'xtatish..."
docker-compose down

# 4. Frontend build qilish
echo "🔨 Frontend build qilish..."
cd frontend-react
if [ ! -d "node_modules" ]; then
    echo "📦 npm install..."
    npm install
fi
npm run build
cd ..

# 5. Docker image'larni build qilish
echo "🐳 Docker image'larni build qilish..."
docker-compose build

# 6. Container'larni ishga tushirish
echo "🚀 Container'larni ishga tushirish..."
docker-compose up -d

# 7. Statusni tekshirish
echo ""
echo "✅ Deploy tugadi!"
echo ""
echo "Container'lar holati:"
docker-compose ps

echo ""
echo "=========================================="
echo "Foydali URL'lar:"
echo "=========================================="
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Admin Panel: http://localhost:8000/admin"
echo "Health Check: http://localhost:8000/system/health"
echo ""
echo "Loglarni ko'rish:"
echo "docker-compose logs -f"
echo ""
echo "Nginx konfiguratsiyasini o'rnatish:"
echo "sudo cp nginx-server.conf /etc/nginx/sites-available/textile-shop"
echo "sudo ln -s /etc/nginx/sites-available/textile-shop /etc/nginx/sites-enabled/"
echo "sudo nginx -t"
echo "sudo systemctl reload nginx"
echo "=========================================="
