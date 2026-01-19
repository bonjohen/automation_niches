"""Entity model - generic object that can represent Vendors, Vehicles, Properties, etc."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .account import Account
    from .requirement import Requirement
    from .document import Document


class EntityStatus(str, Enum):
    """Status of an entity."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"


class EntityType(Base, UUIDMixin, TimestampMixin):
    """
    Entity type lookup table - populated from YAML config.

    Examples: Vendor, Vehicle, Property, Contract, Employee, etc.
    """

    __tablename__ = "entity_types"

    # Type identifier (from YAML)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Icon for UI display
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Custom field schema for this entity type (from YAML)
    field_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="JSON Schema defining custom fields for this entity type"
    )

    # Which niche this type belongs to
    niche_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    entities: Mapped[list["Entity"]] = relationship(
        "Entity",
        back_populates="entity_type",
    )

    def __repr__(self) -> str:
        return f"<EntityType(code='{self.code}', name='{self.name}')>"


class Entity(Base, UUIDMixin, TimestampMixin):
    """
    Generic entity model that can represent any trackable object.

    The actual type (Vendor, Vehicle, Property, etc.) is determined by entity_type.
    Custom fields specific to the type are stored in the custom_fields JSONB column.
    """

    __tablename__ = "entities"

    # Account relationship (multi-tenant)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Type relationship
    entity_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Basic fields common to all entities
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact information (optional, depends on entity type)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[EntityStatus] = mapped_column(
        String(20),
        default=EntityStatus.ACTIVE.value,
        nullable=False,
    )

    # Custom fields based on entity type (flexible JSONB storage)
    custom_fields: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Type-specific custom fields defined by YAML config"
    )

    # External references (CRM integration)
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="ID from external CRM system"
    )
    external_source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Source CRM system (hubspot, salesforce, etc.)"
    )

    # Tags for filtering/grouping
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="entities")
    entity_type: Mapped["EntityType"] = relationship("EntityType", back_populates="entities")
    requirements: Mapped[list["Requirement"]] = relationship(
        "Requirement",
        back_populates="entity",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="entity",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Entity(id={self.id}, name='{self.name}', type={self.entity_type_id})>"
