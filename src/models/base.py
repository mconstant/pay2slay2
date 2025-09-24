from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=None, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=None, onupdate=func.now(), server_default=func.now())
