"""Base model compatibility alias."""

from app.database.base import Base, TimestampMixin, UUIDMixin

__all__ = ["Base", "UUIDMixin", "TimestampMixin"]
