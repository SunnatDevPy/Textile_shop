"""Global rate limiting middleware."""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette import status


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 120,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Storage: {ip: [(timestamp, count_minute, count_hour)]}
        self.request_counts: Dict[str, list] = defaultdict(list)

        # Cleanup interval
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check X-Forwarded-For header (for proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leak."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = now - 3600  # 1 hour ago
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                (ts, count_m, count_h)
                for ts, count_m, count_h in self.request_counts[ip]
                if ts > cutoff_time
            ]
            if not self.request_counts[ip]:
                del self.request_counts[ip]

        self.last_cleanup = now

    def _check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """Check if request should be rate limited."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600

        # Count requests in last minute and hour
        requests_last_minute = sum(
            1 for ts, _, _ in self.request_counts[ip]
            if ts > minute_ago
        )
        requests_last_hour = sum(
            1 for ts, _, _ in self.request_counts[ip]
            if ts > hour_ago
        )

        # Check limits
        if requests_last_minute >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"

        if requests_last_hour >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"

        return True, ""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/system/health", "/system/ready"] or \
           request.url.path.startswith("/media/") or \
           request.url.path.startswith("/admin/"):
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Cleanup old entries periodically
        self._cleanup_old_entries()

        # Check rate limit
        allowed, message = self._check_rate_limit(client_ip)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message
            )

        # Record this request
        now = time.time()
        self.request_counts[client_ip].append((now, 0, 0))

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        minute_ago = now - 60
        requests_last_minute = sum(
            1 for ts, _, _ in self.request_counts[client_ip]
            if ts > minute_ago
        )

        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - requests_last_minute)
        )

        return response
