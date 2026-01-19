"""Entity management endpoints."""
from datetime import datetime
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.entity import Entity, EntityType, EntityStatus
from app.models.user import User
from app.api.endpoints.auth import get_current_active_user

router = APIRouter()


# Pydantic schemas
class EntityTypeResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    field_schema: dict[str, Any]

    class Config:
        from_attributes = True


class EntityCreate(BaseModel):
    entity_type_id: uuid.UUID
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    custom_fields: dict[str, Any] = {}
    tags: list[str] = []


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None


class EntityResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    entity_type_id: uuid.UUID
    name: str
    description: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    status: str
    custom_fields: dict[str, Any]
    tags: list[str]
    external_id: Optional[str]
    external_source: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntityListResponse(BaseModel):
    items: list[EntityResponse]
    total: int
    page: int
    page_size: int


# Endpoints
@router.get("/types", response_model=list[EntityTypeResponse])
async def list_entity_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all available entity types."""
    types = db.query(EntityType).all()
    return types


@router.get("", response_model=EntityListResponse)
async def list_entities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List entities with filtering and pagination."""
    query = db.query(Entity).filter(Entity.account_id == current_user.account_id)

    # Apply filters
    if entity_type_id:
        query = query.filter(Entity.entity_type_id == entity_type_id)
    if status:
        query = query.filter(Entity.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Entity.name.ilike(search_filter),
                Entity.email.ilike(search_filter),
                Entity.description.ilike(search_filter),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    entities = query.order_by(Entity.name).offset(offset).limit(page_size).all()

    return EntityListResponse(
        items=entities,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_data: EntityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new entity."""
    # Verify entity type exists
    entity_type = db.query(EntityType).filter(EntityType.id == entity_data.entity_type_id).first()
    if not entity_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid entity type",
        )

    entity = Entity(
        account_id=current_user.account_id,
        entity_type_id=entity_data.entity_type_id,
        name=entity_data.name,
        description=entity_data.description,
        email=entity_data.email,
        phone=entity_data.phone,
        address=entity_data.address,
        custom_fields=entity_data.custom_fields,
        tags=entity_data.tags,
        status=EntityStatus.ACTIVE.value,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)

    return entity


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific entity by ID."""
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.account_id == current_user.account_id,
    ).first()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )

    return entity


@router.patch("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: uuid.UUID,
    entity_data: EntityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update an entity."""
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.account_id == current_user.account_id,
    ).first()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )

    # Update fields
    update_data = entity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)

    db.commit()
    db.refresh(entity)

    return entity


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an entity."""
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.account_id == current_user.account_id,
    ).first()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )

    db.delete(entity)
    db.commit()
