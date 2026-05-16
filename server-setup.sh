#!/bin/bash
# Server setup script - textile.okach-admin.uz

echo "🚀 Textile Shop - Server Setup"
echo "================================"

# 1. Nginx konfiguratsiya
echo "📝 Nginx konfiguratsiyasini o'rnatish..."

sudo tee /etc/nginx/sites-available/textile.okach-admin.uz > /dev/null <<'EOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name textile.okach-admin.uz;

    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name textile.okach-admin.uz;

    # SSL certificates (certbot will add these)
    # ssl_certificate /etc/letsencrypt/live/textile.okach-admin.uz/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/textile.okach-admin.uz/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logs
    access_log /var/log/nginx/textile_access.log;
    error_log /var/log/nginx/textile_error.log;

    # Frontend (React SPA) - Docker container port 3000
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Backend API - Docker container port 8000
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
    }

    # API docs
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

    # Health checks
    location /system/health {
        proxy_pass http://localhost:8000/system/health;
        access_log off;
    }

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
EOF

# 2. Enable site
echo "🔗 Saytni yoqish..."
sudo ln -sf /etc/nginx/sites-available/textile.okach-admin.uz /etc/nginx/sites-enabled/

# 3. Remove default if exists
sudo rm -f /etc/nginx/sites-enabled/default

# 4. Test nginx config
echo "✅ Nginx konfiguratsiyasini tekshirish..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx konfiguratsiya to'g'ri"

    # 5. Reload nginx
    echo "🔄 Nginx ni qayta yuklash..."
    sudo systemctl reload nginx

    echo ""
    echo "✅ Nginx sozlandi!"
    echo ""
    echo "📝 Keyingi qadam: SSL sertifikat o'rnatish"
    echo "   sudo certbot --nginx -d textile.okach-admin.uz"
    echo ""
else
    echo "❌ Nginx konfiguratsiyada xato!"
    exit 1
fi
EOF