"""Performance monitoring middleware."""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logger import logger


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor API performance and log slow requests."""

    def __init__(self, app, slow_request_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Get user from request state if available
        user = getattr(request.state, "user", None)
        username = getattr(user, "username", None) if user else None

        # Log request
        logger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user=username
        )

        # Warn on slow requests
        if duration_ms > self.slow_request_threshold_ms:
            logger.warning(
                f"Slow request detected",
                {
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": f"{duration_ms:.2f}",
                    "threshold_ms": self.slow_request_threshold_ms
                }
            )

        # Add performance header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response
