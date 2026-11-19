"""Structured logging configuration for OpenReview AI.

Provides standard JSON logging in production and colored human-readable logs
in development, with context/correlation ID propagation.
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict

SENSITIVE_PATTERNS = [
    (re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.]{10,})", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"gh[pousr]_[a-zA-Z0-9]{30,}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"password=([^\s&]+)", re.IGNORECASE), "password=[REDACTED]"),
    (re.compile(r'"password":\s*"([^"]+)"', re.IGNORECASE), '"password": "[REDACTED]"'),
]


def scrub_sensitive_text(text: str) -> str:
    """Masks authorization tokens, API keys, and passwords from log strings."""
    if not text:
        return text
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects with sensitive data scrubbing."""

    def format(self, record: logging.LogRecord) -> str:
        msg = scrub_sensitive_text(record.getMessage())
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "module": record.module,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            exc_str = scrub_sensitive_text(self.formatException(record.exc_info))
            log_data["exception"] = exc_str

        # Include custom extra fields if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = getattr(record, "request_id")
        if hasattr(record, "user_id"):
            log_data["user_id"] = getattr(record, "user_id")

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter with ANSI color codes for local terminal development."""

    LEVEL_COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        time_str = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        req_part = ""
        if hasattr(record, "request_id") and getattr(record, "request_id"):
            req_part = f" [{getattr(record, 'request_id')}]"

        header = f"{self.DIM}{time_str}{self.RESET} {color}{record.levelname:<8}{self.RESET} {self.BOLD}{record.name}{self.RESET}{req_part}"
        msg = f"{header}: {record.getMessage()}"

        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)

        return msg


def setup_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Configures the root logger and standard library logging handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(handler)

    # Set external libraries to warning to avoid log spam
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance with the given name."""
    return logging.getLogger(name)
