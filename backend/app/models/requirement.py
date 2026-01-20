"""Requirement model - compliance tasks with due dates and status tracking."""
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, Text, Integer

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin, JSONB, UUID

if TYPE_CHECKING:
    from .account import Account
    from .entity import Entity
    from .document import Document
    from .notification import Notification


class RequirementStatus(str, Enum):
    """Status of a requirement."""
    PENDING = "pending"           # Not yet started
    IN_PROGRESS = "in_progress"   # Work in progress
    COMPLIANT = "compliant"       # Meets requirements
    EXPIRING_SOON = "expiring_soon"  # Due date approaching
    EXPIRED = "expired"           # Past due date
    NON_COMPLIANT = "non_compliant"  # Failed/rejected
    WAIVED = "waived"            # Exempted


class RequirementPriority(str, Enum):
    """Priority level of a requirement."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementType(Base, UUIDMixin, TimestampMixin):
    """
    Requirement type lookup table - populated from YAML config.

    Examples: COI Verification, Vehicle Registration, Lease Renewal, etc.
    """

    __tablename__ = "requirement_types"

    # Type identifier (from YAML)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Frequency settings
    frequency: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Frequency: once, daily, weekly, monthly, quarterly, annually"
    )

    # Default priority
    default_priority: Mapped[str] = mapped_column(
        String(20),
        default=RequirementPriority.MEDIUM.value,
        nullable=False,
    )

    # Notification rules (from YAML)
    notification_rules: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="When to send reminders: days_before, escalation rules, etc."
    )

    # Which entity types this requirement applies to
    applicable_entity_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Which document types satisfy this requirement
    required_document_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Custom field schema for this requirement type
    field_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Which niche this type belongs to
    niche_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    requirements: Mapped[list["Requirement"]] = relationship(
        "Requirement",
        back_populates="requirement_type",
    )

    def __repr__(self) -> str:
        return f"<RequirementType(code='{self.code}', name='{self.name}')>"


class Requirement(Base, UUIDMixin, TimestampMixin):
    """
    Requirement model - a specific compliance task tied to an entity.

    Requirements have due dates, statuses, and can be linked to documents
    that prove compliance.
    """

    __tablename__ = "requirements"

    # Account relationship (multi-tenant)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Entity this requirement is for
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Type relationship
    requirement_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirement_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status and priority
    status: Mapped[str] = mapped_column(
        String(20),
        default=RequirementStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=RequirementPriority.MEDIUM.value,
        nullable=False,
    )

    # Document that satisfies this requirement
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Custom fields based on requirement type
    custom_fields: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Notes and comments
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Assignee (user responsible)
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="requirements")
    entity: Mapped["Entity"] = relationship("Entity", back_populates="requirements")
    requirement_type: Mapped["RequirementType"] = relationship(
        "RequirementType",
        back_populates="requirements",
    )
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        foreign_keys=[document_id],
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="requirement",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Requirement(id={self.id}, name='{self.name}', status='{self.status}')>"
