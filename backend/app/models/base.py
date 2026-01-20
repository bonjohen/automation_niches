"""Base model with common fields for all entities."""
import os
from datetime import datetime
from typing import Any
import uuid as uuid_module

from sqlalchemy import DateTime, func, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB as PostgresJSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, CHAR


# Use JSON for SQLite (tests), JSONB for PostgreSQL (production)
_use_sqlite = os.environ.get("ENVIRONMENT") == "test"
_json_type = JSON if _use_sqlite else PostgresJSONB


class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type for SQLite.

    Uses CHAR(36) for SQLite, stores as a string.
    Accepts as_uuid parameter for PostgreSQL compatibility but ignores it.
    """
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid=True, **kwargs):
        # Accept as_uuid for PostgreSQL compatibility, but ignore it
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid_module.UUID):
            return str(value)
        else:
            return str(uuid_module.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid_module.UUID(value)


# Export these so models can use compatible types
JSONB = _json_type  # Will be JSON for tests, JSONB for production
UUID = SQLiteUUID if _use_sqlite else PostgresUUID


class Base(DeclarativeBase):
    """Base class for all database models."""

    type_annotation_map = {
        dict[str, Any]: _json_type,
        list[str]: _json_type,
        list[float]: _json_type,
    }


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin that adds a UUID primary key."""

    id: Mapped[uuid_module.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid_module.uuid4,
    )
