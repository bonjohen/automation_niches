"""Notification model - scheduled alerts and reminders."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin, JSONB, UUID

if TYPE_CHECKING:
    from .account import Account
    from .requirement import Requirement


class NotificationType(str, Enum):
    """Type of notification."""
    REMINDER = "reminder"           # Upcoming due date reminder
    OVERDUE = "overdue"            # Past due date alert
    EXPIRING = "expiring"          # About to expire
    STATUS_CHANGE = "status_change" # Status changed
    DOCUMENT_PROCESSED = "document_processed"  # Document extraction complete
    ESCALATION = "escalation"      # Escalated due to no action


class NotificationChannel(str, Enum):
    """Delivery channel for notification."""
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationStatus(str, Enum):
    """Status of notification delivery."""
    PENDING = "pending"      # Scheduled, not sent
    SENT = "sent"           # Successfully sent
    FAILED = "failed"       # Delivery failed
    CANCELLED = "cancelled"  # Cancelled (e.g., requirement completed)
    READ = "read"           # User acknowledged (in-app)


class Notification(Base, UUIDMixin, TimestampMixin):
    """
    Notification model - scheduled alerts and reminders.

    Notifications are generated based on requirement due dates and
    notification rules defined in the YAML config.
    """

    __tablename__ = "notifications"

    # Account relationship (multi-tenant)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Related requirement (optional - some notifications might be system-level)
    requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Recipient user
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification details
    notification_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        default=NotificationChannel.EMAIL.value,
        nullable=False,
    )

    # Content
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Template used (for tracking)
    template_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=NotificationStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Delivery tracking
    delivery_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # External service tracking (e.g., SendGrid message ID)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Additional context data
    context_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional data for template rendering"
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="notifications")
    requirement: Mapped[Optional["Requirement"]] = relationship(
        "Requirement",
        back_populates="notifications",
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type='{self.notification_type}', status='{self.status}')>"
