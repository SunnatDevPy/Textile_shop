from typing import Any, Optional


def ok_response(data: Any = None, meta: Optional[dict] = None) -> dict:
    return {
        "ok": True,
        "data": data,
        "meta": meta or {},
        "error": None,
    }


def error_response(message: str, code: str = "bad_request", meta: Optional[dict] = None) -> dict:
    return {
        "ok": False,
        "data": None,
        "meta": meta or {},
        "error": {
            "code": code,
            "message": message,
        },
    }
