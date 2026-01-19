"""Notification management endpoints."""
from datetime import datetime
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.notification import Notification, NotificationStatus, NotificationType, NotificationChannel
from app.models.user import User
from app.api.endpoints.auth import get_current_active_user

router = APIRouter()


# Pydantic schemas
class NotificationResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    requirement_id: Optional[uuid.UUID]
    recipient_id: uuid.UUID
    notification_type: str
    channel: str
    subject: str
    body: str
    scheduled_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    unread_count: int


class NotificationCreate(BaseModel):
    requirement_id: Optional[uuid.UUID] = None
    recipient_id: uuid.UUID
    notification_type: str = NotificationType.REMINDER.value
    channel: str = NotificationChannel.EMAIL.value
    subject: str
    body: str
    scheduled_at: datetime
    context_data: dict[str, Any] = {}


# Endpoints
@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List notifications for the current user."""
    query = db.query(Notification).filter(
        Notification.account_id == current_user.account_id,
        Notification.recipient_id == current_user.id,
    )

    # Apply filters
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    if status:
        query = query.filter(Notification.status == status)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    # Get unread count
    unread_count = db.query(Notification).filter(
        Notification.account_id == current_user.account_id,
        Notification.recipient_id == current_user.id,
        Notification.read_at.is_(None),
    ).count()

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    notifications = query.order_by(Notification.scheduled_at.desc()).offset(offset).limit(page_size).all()

    return NotificationListResponse(
        items=notifications,
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific notification by ID."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.account_id == current_user.account_id,
        Notification.recipient_id == current_user.id,
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.account_id == current_user.account_id,
        Notification.recipient_id == current_user.id,
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        notification.status = NotificationStatus.READ.value
        db.commit()
        db.refresh(notification)

    return notification


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    db.query(Notification).filter(
        Notification.account_id == current_user.account_id,
        Notification.recipient_id == current_user.id,
        Notification.read_at.is_(None),
    ).update({
        "read_at": datetime.utcnow(),
        "status": NotificationStatus.READ.value,
    })
    db.commit()


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.account_id == current_user.account_id,
        Notification.recipient_id == current_user.id,
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    db.delete(notification)
    db.commit()


# Admin endpoints (for scheduling notifications)
@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new notification (admin only)."""
    # TODO: Add admin role check

    notification = Notification(
        account_id=current_user.account_id,
        requirement_id=notification_data.requirement_id,
        recipient_id=notification_data.recipient_id,
        notification_type=notification_data.notification_type,
        channel=notification_data.channel,
        subject=notification_data.subject,
        body=notification_data.body,
        scheduled_at=notification_data.scheduled_at,
        context_data=notification_data.context_data,
        status=NotificationStatus.PENDING.value,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification
