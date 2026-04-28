import hashlib
import hmac
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from config import conf

_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def verify_hmac_signature(payload: str, signature: str, secret: str) -> bool:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def enforce_rate_limit(request: Request, scope: str = "global") -> None:
    limit = conf.RATE_LIMIT_PER_MINUTE
    now = time.time()
    window_start = now - 60
    key = f"{scope}:{request.client.host if request.client else 'unknown'}"
    q = _RATE_BUCKETS[key]
    while q and q[0] < window_start:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )
    q.append(now)


def enforce_ip_whitelist(request: Request) -> None:
    whitelist = [ip.strip() for ip in conf.PAYMENT_CALLBACK_IP_WHITELIST.split(",") if ip.strip()]
    if not whitelist:
        return
    ip = request.client.host if request.client else None
    if not ip or ip not in whitelist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP is not allowed",
        )
