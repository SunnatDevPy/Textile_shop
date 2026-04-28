# Textile Shop (FastAPI)

Бэкенд интернет-магазина на `FastAPI` с `PostgreSQL`.

## Что есть в проекте

- API на `FastAPI` (документация: `/docs`)
- База данных `PostgreSQL`
- Docker-окружение через `docker-compose`

## Структура сервисов в Docker

- `app` — FastAPI приложение (`uvicorn`, порт `8000`)
- `db` — PostgreSQL (`5432` внутри сети docker, наружу проброшен `5431`)

## Переменные окружения

Файл: `.env`

Минимально важные переменные:

- `DB_NAME`
- `DB_USER`
- `DB_PASS`
- `DB_HOST`
- `DB_PORT`
- `SECRET_KEY`
- `ADMIN`, `ADMIN_USERNAME`, `ADMIN_PASS`

Пример для Docker Compose:

```env
DB_NAME=textile
DB_USER=postgres
DB_PASS=1
DB_HOST=db
DB_PORT=5432
SECRET_KEY=change_me_to_long_random_secret
ADMIN=123456789
ADMIN_USERNAME=admin
ADMIN_PASS=hashed_password
```

## Быстрый запуск через Docker

В корне проекта:

```bash
docker compose up -d --build
```

Проверка:

```bash
docker compose ps
docker compose logs -f app
```

API Docs:

- [http://localhost:8000/docs](http://localhost:8000/docs)

## Остановка

```bash
docker compose down
```

С удалением томов БД:

```bash
docker compose down -v
```

## Деплой на сервер

1. Установить Docker и Docker Compose на VPS
2. Скопировать проект на сервер
3. Подготовить `.env` (боевые значения)
4. Запустить:

```bash
docker compose up -d --build
```

5. Проверить логи `app`

Подробный чеклист: `DEPLOY_CHECKLIST.md`

## Переход на домен

1. Создать DNS `A` запись на IP сервера (например, `api.yourdomain.com`)
2. Настроить reverse proxy (Nginx/Traefik) на `app:8000`
3. Подключить SSL (Let's Encrypt)
4. Обновить CORS в `main.py`:
   - заменить `allow_origins=["*"]` на список своих доменов
5. Перевести frontend API URL на HTTPS-домен

## Безопасность

- Не храните реальные токены и пароли в git
- Используйте сложные значения `SECRET_KEY` и `DB_PASS`
- Ограничивайте доступ к БД (в проде обычно не пробрасывают порт БД наружу)

## Полезные команды

Пересборка и запуск:

```bash
docker compose up -d --build
```

Рестарт API:

```bash
docker compose restart app
```
