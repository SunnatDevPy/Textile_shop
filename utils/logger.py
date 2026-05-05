"""Structured logging utility for API."""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured logger with JSON output support."""

    def __init__(self, name: str = "textile_shop", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Format: timestamp | level | message | context
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _format_context(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Format context dictionary as string."""
        if not context:
            return ""
        parts = [f"{k}={v}" for k, v in context.items()]
        return " | " + " | ".join(parts)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.logger.info(message + self._format_context(context))

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.logger.warning(message + self._format_context(context))

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message."""
        self.logger.error(message + self._format_context(context), exc_info=exc_info)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.logger.debug(message + self._format_context(context))

    def log_request(self, method: str, path: str, status_code: int, duration_ms: float, user: Optional[str] = None):
        """Log HTTP request."""
        context = {
            "method": method,
            "path": path,
            "status": status_code,
            "duration_ms": f"{duration_ms:.2f}",
        }
        if user:
            context["user"] = user

        self.info("HTTP Request", context)

    def log_db_query(self, query_type: str, table: str, duration_ms: float, rows: Optional[int] = None):
        """Log database query."""
        context = {
            "query_type": query_type,
            "table": table,
            "duration_ms": f"{duration_ms:.2f}",
        }
        if rows is not None:
            context["rows"] = rows

        self.debug("DB Query", context)

    def log_cache_hit(self, key: str, hit: bool):
        """Log cache hit/miss."""
        self.debug(f"Cache {'HIT' if hit else 'MISS'}", {"key": key})

    def log_error_with_trace(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with full traceback."""
        self.error(f"Exception: {type(error).__name__}: {str(error)}", context, exc_info=True)


# Global logger instance with file logging
logger = StructuredLogger(log_file="logs/textile_shop.log")
