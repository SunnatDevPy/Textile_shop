FROM node:24-alpine AS frontend_builder

WORKDIR /ui
COPY frontend-react/package*.json ./frontend-react/
WORKDIR /ui/frontend-react
RUN npm ci
COPY frontend-react/ ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend_builder /ui/frontend-react/dist ./frontend-react/dist

RUN mkdir -p /app/media

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
