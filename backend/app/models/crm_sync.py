"""CRM Sync Log model for tracking synchronization operations."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin, JSONB, UUID

if TYPE_CHECKING:
    from .account import Account
    from .entity import Entity


class SyncDirection(str, Enum):
    """Direction of the sync operation."""
    PUSH = "push"  # Our platform -> CRM
    PULL = "pull"  # CRM -> Our platform


class SyncOperation(str, Enum):
    """Type of sync operation."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    COMPLIANCE_PUSH = "compliance_push"
    TEST_CONNECTION = "test_connection"


class SyncStatus(str, Enum):
    """Status of the sync operation."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class CRMSyncLog(Base, UUIDMixin, TimestampMixin):
    """
    Tracks CRM synchronization operations for debugging and audit.

    Each record represents a single sync attempt (create, update, delete)
    between our platform and an external CRM.
    """

    __tablename__ = "crm_sync_logs"

    # Account relationship (multi-tenant)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Entity relationship (optional - null for bulk operations or test connections)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Sync details
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="push or pull",
    )

    operation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="create, update, delete, compliance_push, test_connection",
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="hubspot, zapier, salesforce, etc.",
    )

    # External CRM reference
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="CRM record ID",
    )

    # Request/Response data for debugging
    request_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Data sent to CRM",
    )

    response_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Response from CRM",
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SyncStatus.PENDING.value,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Retry tracking
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Duration tracking (for performance monitoring)
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Duration of the sync operation in milliseconds",
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account")
    entity: Mapped[Optional["Entity"]] = relationship("Entity")

    def __repr__(self) -> str:
        return (
            f"<CRMSyncLog("
            f"id={self.id}, "
            f"provider='{self.provider}', "
            f"operation='{self.operation}', "
            f"status='{self.status}'"
            f")>"
        )

    def mark_success(self, response_data: Optional[dict] = None, duration_ms: Optional[int] = None):
        """Mark this sync operation as successful."""
        self.status = SyncStatus.SUCCESS.value
        if response_data:
            self.response_data = response_data
        if duration_ms:
            self.duration_ms = duration_ms

    def mark_failed(self, error_message: str, response_data: Optional[dict] = None):
        """Mark this sync operation as failed."""
        self.status = SyncStatus.FAILED.value
        self.error_message = error_message
        if response_data:
            self.response_data = response_data
