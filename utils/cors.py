"""CORS yordamchilari (frontend dev + production)."""

import re

from fastapi import Request

from config import conf

_VERCEL_ORIGIN_RE = re.compile(r"^https://.+\.vercel\.app$", re.IGNORECASE)


def _cors_allow_vercel() -> bool:
    return bool(getattr(conf, "CORS_ALLOW_VERCEL", True))


def cors_allowed_origins() -> list[str]:
    raw = (conf.CORS_ORIGINS or "").strip()
    if not raw or raw == "*":
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://textile.okach-admin.uz",
            "https://unversal-admin.vercel.app",
            "https://khivacode.vercel.app",
        ]
    return [part.strip() for part in raw.split(",") if part.strip()]


def cors_origin_regex() -> str | None:
    """Vercel preview/prod domenlari: *.vercel.app"""
    if not _cors_allow_vercel():
        return None
    return r"https://.*\.vercel\.app"


def is_origin_allowed(origin: str | None) -> bool:
    if not origin:
        return False
    if origin in cors_allowed_origins():
        return True
    if _cors_allow_vercel() and _VERCEL_ORIGIN_RE.match(origin):
        return True
    return False


def cors_headers_for_request(request: Request) -> dict[str, str]:
    """Javobga qo'shiladigan CORS sarlavhalari (xato handlerlari uchun ham)."""
    origin = request.headers.get("origin")
    if not is_origin_allowed(origin):
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }
