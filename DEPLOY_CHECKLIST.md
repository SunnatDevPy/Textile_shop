# Deploy checklist (server + domain)

## 1) What to prepare on server

- [ ] Domain name (for example: `api.yourdomain.com`)
- [ ] VPS with Docker and Docker Compose installed
- [ ] Open ports: `80`, `443` (and optionally `22` for SSH)
- [ ] SSL certificate (Let's Encrypt)

## 2) What to change in this project before deploy

### File: `.env`

Change these values:

- [ ] `DB_HOST=db` (for docker-compose network)
- [ ] `DB_PORT=5432` (inside docker network)
- [ ] `DB_NAME=<your_prod_db_name>`
- [ ] `DB_USER=<your_prod_db_user>`
- [ ] `DB_PASS=<your_prod_db_password>`
- [ ] `SECRET_KEY=<long_random_secret>`
- [ ] `BOT_TOKEN=<your_real_bot_token_if_used>`

Important:
- [ ] Do not commit real secrets to git
- [ ] Keep `.env` only on server (or use `.env.prod`)

## 3) First run on server

From project directory:

```bash
docker compose up -d --build
```

Check:

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f bot
```

## 4) Domain setup (when moving from IP to domain)

### DNS (domain provider panel)

- [ ] Create `A` record: `api.yourdomain.com` -> `<SERVER_PUBLIC_IP>`
- [ ] Wait for DNS propagation

### Reverse proxy (Nginx or Traefik)

You should route:
- [ ] `https://api.yourdomain.com` -> `http://app:8000` (or `127.0.0.1:8000`)

For this project, app runs on:
- internal: `8000`
- external (current compose): `8000:8000`

## 5) What to update in app code for domain

### File: `main.py`

Current CORS is open for all origins (`allow_origins=["*"]`).
For production with domain, change to explicit list:

- [ ] `allow_origins=["https://yourdomain.com", "https://www.yourdomain.com"]`

Also update preflight response if needed:
- [ ] In `preflight_handler`, set `Access-Control-Allow-Origin` to your domain (not `*`) when using credentials.

## 6) SSL reminder

- [ ] Configure HTTPS (Let's Encrypt)
- [ ] Force redirect HTTP -> HTTPS
- [ ] Use only `https://...` in frontend API URL

## 7) Database safety reminders

- [ ] Use strong DB password
- [ ] Keep persistent volume (`postgres_data`)
- [ ] Configure backups (daily dump)

Example backup command:

```bash
docker exec -t textile_db pg_dump -U postgres textile > backup_$(date +%F).sql
```

## 8) Quick post-deploy checks

- [ ] `https://api.yourdomain.com/docs` opens
- [ ] Main API endpoints return `200`
- [ ] File uploads work (`/media`)
- [ ] Bot/webhook integrations (if used) are reachable via HTTPS
- [ ] Telegram bot responds to `/start`

## 9) Telegram bot reminders

- [ ] Keep `BOT_TOKEN` only in server `.env`
- [ ] Run bot in separate service (`bot`) via docker-compose
- [ ] Check bot logs after deploy:

```bash
docker compose logs -f bot
```

If you use polling (current project), domain is not required for bot to work.  
If you switch to webhook in future:
- [ ] Add HTTPS domain for webhook URL
- [ ] Configure webhook endpoint in FastAPI/Nginx
- [ ] Open and secure `443` port

---

## Short "what to change when domain appears"

1. DNS `A` record -> server IP  
2. Reverse proxy config (`api.yourdomain.com` -> app:8000)  
3. SSL certificate for domain  
4. `main.py` CORS: replace `*` with real domains  
5. Frontend API base URL: change from IP/local to domain  
