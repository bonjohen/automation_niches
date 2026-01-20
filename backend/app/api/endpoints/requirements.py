"""Requirements management endpoints."""
from datetime import date, datetime
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.requirement import Requirement, RequirementType, RequirementStatus, RequirementPriority
from app.models.user import User
from app.api.endpoints.auth import get_current_active_user

router = APIRouter()


# Pydantic schemas
class RequirementTypeResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    frequency: Optional[str]
    default_priority: str
    notification_rules: dict[str, Any]
    applicable_entity_types: list[str]
    required_document_types: list[str]

    class Config:
        from_attributes = True


class RequirementCreate(BaseModel):
    entity_id: uuid.UUID
    requirement_type_id: uuid.UUID
    name: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    effective_date: Optional[date] = None
    priority: str = RequirementPriority.MEDIUM.value
    custom_fields: dict[str, Any] = {}
    notes: Optional[str] = None
    assignee_id: Optional[uuid.UUID] = None


class RequirementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    effective_date: Optional[date] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    assignee_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None


class RequirementResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    entity_id: uuid.UUID
    requirement_type_id: uuid.UUID
    name: str
    description: Optional[str]
    due_date: Optional[date]
    effective_date: Optional[date]
    completed_date: Optional[date]
    status: str
    priority: str
    document_id: Optional[uuid.UUID]
    custom_fields: dict[str, Any]
    notes: Optional[str]
    assignee_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementListResponse(BaseModel):
    items: list[RequirementResponse]
    total: int
    page: int
    page_size: int


class TaskSummary(BaseModel):
    """Summary of task statuses (renamed from ComplianceSummary)."""
    total: int
    current: int       # was compliant
    due_soon: int      # was expiring_soon
    expired: int
    pending: int


# Endpoints
@router.get("/types", response_model=list[RequirementTypeResponse])
async def list_requirement_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all available requirement types."""
    types = db.query(RequirementType).all()
    return types


@router.get("/summary", response_model=TaskSummary)
async def get_task_summary(
    entity_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get task summary statistics."""
    query = db.query(Requirement).filter(Requirement.account_id == current_user.account_id)

    if entity_id:
        query = query.filter(Requirement.entity_id == entity_id)

    total = query.count()
    current = query.filter(Requirement.status == RequirementStatus.CURRENT.value).count()
    due_soon = query.filter(Requirement.status == RequirementStatus.DUE_SOON.value).count()
    expired = query.filter(Requirement.status == RequirementStatus.EXPIRED.value).count()
    pending = query.filter(Requirement.status == RequirementStatus.PENDING.value).count()

    return TaskSummary(
        total=total,
        current=current,
        due_soon=due_soon,
        expired=expired,
        pending=pending,
    )


@router.get("", response_model=RequirementListResponse)
async def list_requirements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_id: Optional[uuid.UUID] = None,
    requirement_type_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List requirements with filtering and pagination."""
    query = db.query(Requirement).filter(Requirement.account_id == current_user.account_id)

    # Apply filters
    if entity_id:
        query = query.filter(Requirement.entity_id == entity_id)
    if requirement_type_id:
        query = query.filter(Requirement.requirement_type_id == requirement_type_id)
    if status:
        query = query.filter(Requirement.status == status)
    if priority:
        query = query.filter(Requirement.priority == priority)
    if due_before:
        query = query.filter(Requirement.due_date <= due_before)
    if due_after:
        query = query.filter(Requirement.due_date >= due_after)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Requirement.name.ilike(search_filter),
                Requirement.description.ilike(search_filter),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    requirements = query.order_by(Requirement.due_date.asc().nullslast()).offset(offset).limit(page_size).all()

    return RequirementListResponse(
        items=requirements,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    req_data: RequirementCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new requirement."""
    # Verify requirement type exists
    req_type = db.query(RequirementType).filter(RequirementType.id == req_data.requirement_type_id).first()
    if not req_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid requirement type",
        )

    requirement = Requirement(
        account_id=current_user.account_id,
        entity_id=req_data.entity_id,
        requirement_type_id=req_data.requirement_type_id,
        name=req_data.name,
        description=req_data.description,
        due_date=req_data.due_date,
        effective_date=req_data.effective_date,
        priority=req_data.priority,
        custom_fields=req_data.custom_fields,
        notes=req_data.notes,
        assignee_id=req_data.assignee_id,
        status=RequirementStatus.PENDING.value,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific requirement by ID."""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.account_id == current_user.account_id,
    ).first()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return requirement


@router.patch("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: uuid.UUID,
    req_data: RequirementUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a requirement."""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.account_id == current_user.account_id,
    ).first()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    # Update fields
    update_data = req_data.model_dump(exclude_unset=True)

    # Handle status change to completed (current)
    if "status" in update_data and update_data["status"] == RequirementStatus.CURRENT.value:
        if requirement.status != RequirementStatus.CURRENT.value:
            update_data["completed_date"] = date.today()

    for field, value in update_data.items():
        setattr(requirement, field, value)

    db.commit()
    db.refresh(requirement)

    return requirement


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a requirement."""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.account_id == current_user.account_id,
    ).first()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    db.delete(requirement)
    db.commit()


@router.post("/{requirement_id}/complete", response_model=RequirementResponse)
async def mark_requirement_complete(
    requirement_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark a requirement/task as complete (current)."""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.account_id == current_user.account_id,
    ).first()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    requirement.status = RequirementStatus.CURRENT.value
    requirement.completed_date = date.today()
    db.commit()
    db.refresh(requirement)

    return requirement
