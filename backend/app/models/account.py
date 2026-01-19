"""Account/Organization model for multi-tenancy."""
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .user import User
    from .entity import Entity
    from .requirement import Requirement
    from .document import Document
    from .notification import Notification


class Account(Base, UUIDMixin, TimestampMixin):
    """
    Account/Organization model representing a tenant in the multi-tenant system.

    Each account can have its own branding, users, and data completely isolated
    from other accounts.
    """

    __tablename__ = "accounts"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Contact info
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Branding/White-label configuration
    branding: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Branding config: logo_url, primary_color, secondary_color, etc."
    )

    # Niche configuration - which industry template this account uses
    niche_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="References the niche YAML config file (e.g., 'coi_tracking')"
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Subscription/billing info (for future use)
    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Settings and custom configuration
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Account-specific settings and preferences"
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    entities: Mapped[list["Entity"]] = relationship(
        "Entity",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    requirements: Mapped[list["Requirement"]] = relationship(
        "Requirement",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name='{self.name}', slug='{self.slug}')>"
