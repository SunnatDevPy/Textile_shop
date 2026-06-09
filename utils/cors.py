"""CORS yordamchilari (frontend dev + production)."""

from fastapi import Request

from config import conf


def cors_allowed_origins() -> list[str]:
    raw = (conf.CORS_ORIGINS or "").strip()
    if not raw or raw == "*":
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://textile.okach-admin.uz",
            "https://unversal-admin.vercel.app",
        ]
    return [part.strip() for part in raw.split(",") if part.strip()]


def cors_headers_for_request(request: Request) -> dict[str, str]:
    """Javobga qo'shiladigan CORS sarlavhalari (xato handlerlari uchun ham)."""
    origin = request.headers.get("origin")
    if not origin or origin not in cors_allowed_origins():
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }
