"""CRM Integration endpoints."""
from datetime import datetime
from typing import Any, Optional
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import get_settings
from app.models.account import Account
from app.models.entity import Entity
from app.models.user import User
from app.models.crm_sync import CRMSyncLog, SyncDirection, SyncOperation, SyncStatus
from app.api.endpoints.auth import get_current_active_user
from app.services.crm import (
    CRMService,
    get_crm_service,
    encrypt_secret,
    decrypt_secret,
)
from app.services.crm.encryption import redact_secret
from app.services.crm.zapier import ZapierWebhookConnector

router = APIRouter()
settings = get_settings()


# ----- Pydantic Schemas -----

class HubSpotSettings(BaseModel):
    """HubSpot-specific settings."""
    api_key: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    portal_id: Optional[str] = None
    object_type: str = "companies"


class ZapierSettings(BaseModel):
    """Zapier-specific settings."""
    webhook_url_entity_created: Optional[str] = None
    webhook_url_entity_updated: Optional[str] = None
    webhook_url_compliance_changed: Optional[str] = None
    webhook_secret: Optional[str] = None


class FieldMapping(BaseModel):
    """Field mapping configuration."""
    name: str = "name"
    email: str = "email"
    phone: str = "phone"
    address: str = "address"
    # Custom field mappings as additional key-value pairs


class CRMSettingsUpdate(BaseModel):
    """Request body for updating CRM settings."""
    provider: Optional[str] = Field(None, pattern="^(hubspot|zapier|none)$")
    enabled: Optional[bool] = None
    sync_direction: Optional[str] = Field(None, pattern="^(push_only|pull_only|bidirectional)$")
    hubspot: Optional[HubSpotSettings] = None
    zapier: Optional[ZapierSettings] = None
    field_mapping: Optional[dict[str, str]] = None


class CRMSettingsResponse(BaseModel):
    """Response body for CRM settings (with secrets redacted)."""
    provider: Optional[str] = None
    enabled: bool = False
    sync_direction: str = "push_only"
    hubspot: Optional[dict[str, Any]] = None
    zapier: Optional[dict[str, Any]] = None
    field_mapping: dict[str, str] = {}
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""
    success: bool
    message: str
    provider: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class SyncResult(BaseModel):
    """Result of a sync operation."""
    success: bool
    synced_count: int = 0
    failed_count: int = 0
    errors: list[str] = []


class SyncLogResponse(BaseModel):
    """Single sync log entry."""
    id: uuid.UUID
    entity_id: Optional[uuid.UUID]
    direction: str
    operation: str
    provider: str
    external_id: Optional[str]
    status: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class SyncLogListResponse(BaseModel):
    """Paginated list of sync logs."""
    items: list[SyncLogResponse]
    total: int
    page: int
    page_size: int


class WebhookPayload(BaseModel):
    """Incoming webhook payload."""
    event: Optional[str] = None
    external_id: Optional[str] = None
    data: Optional[dict[str, Any]] = None


# ----- Helper Functions -----

def get_account(db: Session, account_id: uuid.UUID) -> Account:
    """Get account by ID or raise 404."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


def log_sync_operation(
    db: Session,
    account_id: uuid.UUID,
    entity_id: Optional[uuid.UUID],
    direction: str,
    operation: str,
    provider: str,
    request_data: dict,
    response_data: dict,
    status: str,
    error_message: Optional[str] = None,
    external_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> CRMSyncLog:
    """Create a sync log entry."""
    log = CRMSyncLog(
        account_id=account_id,
        entity_id=entity_id,
        direction=direction,
        operation=operation,
        provider=provider,
        request_data=request_data,
        response_data=response_data,
        status=status,
        error_message=error_message,
        external_id=external_id,
        duration_ms=duration_ms,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ----- Settings Endpoints -----

@router.get("/settings", response_model=CRMSettingsResponse)
async def get_integration_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get CRM integration settings for the current account."""
    account = get_account(db, current_user.account_id)
    crm_config = (account.settings or {}).get("crm", {})

    # Redact sensitive data
    response = CRMSettingsResponse(
        provider=crm_config.get("provider"),
        enabled=crm_config.get("enabled", False),
        sync_direction=crm_config.get("sync_direction", "push_only"),
        field_mapping=crm_config.get("field_mapping", {}),
        last_sync_at=crm_config.get("last_sync_at"),
        last_sync_status=crm_config.get("last_sync_status"),
    )

    # Include HubSpot settings with redacted secrets
    if crm_config.get("hubspot"):
        hs = crm_config["hubspot"]
        response.hubspot = {
            "api_key": redact_secret(hs.get("api_key", "")) if hs.get("api_key") else None,
            "oauth_token": "••••••••" if hs.get("oauth_token") else None,
            "portal_id": hs.get("portal_id"),
            "object_type": hs.get("object_type", "companies"),
            "has_credentials": bool(hs.get("api_key") or hs.get("oauth_token")),
        }

    # Include Zapier settings with redacted secrets
    if crm_config.get("zapier"):
        zap = crm_config["zapier"]
        response.zapier = {
            "webhook_url_entity_created": zap.get("webhook_url_entity_created"),
            "webhook_url_entity_updated": zap.get("webhook_url_entity_updated"),
            "webhook_url_compliance_changed": zap.get("webhook_url_compliance_changed"),
            "webhook_secret": redact_secret(zap.get("webhook_secret", "")) if zap.get("webhook_secret") else None,
            "inbound_webhook_url": f"{settings.api_base_url}/api/v1/integrations/webhooks/zapier/{current_user.account_id}",
        }

    return response


@router.put("/settings", response_model=CRMSettingsResponse)
async def update_integration_settings(
    settings_update: CRMSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update CRM integration settings."""
    account = get_account(db, current_user.account_id)

    # Get current settings or initialize
    current_settings = account.settings or {}
    crm_config = current_settings.get("crm", {})

    # Update top-level fields
    if settings_update.provider is not None:
        crm_config["provider"] = settings_update.provider if settings_update.provider != "none" else None
    if settings_update.enabled is not None:
        crm_config["enabled"] = settings_update.enabled
    if settings_update.sync_direction is not None:
        crm_config["sync_direction"] = settings_update.sync_direction
    if settings_update.field_mapping is not None:
        crm_config["field_mapping"] = settings_update.field_mapping

    # Update HubSpot settings
    if settings_update.hubspot:
        hs = crm_config.get("hubspot", {})
        hs_update = settings_update.hubspot

        if hs_update.api_key is not None:
            # Only update if a new value is provided (not a redacted string)
            if not hs_update.api_key.startswith("••"):
                hs["api_key"] = encrypt_secret(hs_update.api_key) if hs_update.api_key else ""
        if hs_update.oauth_token is not None:
            if not hs_update.oauth_token.startswith("••"):
                hs["oauth_token"] = encrypt_secret(hs_update.oauth_token) if hs_update.oauth_token else ""
        if hs_update.portal_id is not None:
            hs["portal_id"] = hs_update.portal_id
        if hs_update.object_type is not None:
            hs["object_type"] = hs_update.object_type

        crm_config["hubspot"] = hs

    # Update Zapier settings
    if settings_update.zapier:
        zap = crm_config.get("zapier", {})
        zap_update = settings_update.zapier

        if zap_update.webhook_url_entity_created is not None:
            zap["webhook_url_entity_created"] = zap_update.webhook_url_entity_created
        if zap_update.webhook_url_entity_updated is not None:
            zap["webhook_url_entity_updated"] = zap_update.webhook_url_entity_updated
        if zap_update.webhook_url_compliance_changed is not None:
            zap["webhook_url_compliance_changed"] = zap_update.webhook_url_compliance_changed
        if zap_update.webhook_secret is not None:
            if not zap_update.webhook_secret.startswith("••"):
                zap["webhook_secret"] = encrypt_secret(zap_update.webhook_secret) if zap_update.webhook_secret else ""

        crm_config["zapier"] = zap

    # Save settings
    current_settings["crm"] = crm_config
    account.settings = current_settings
    db.commit()
    db.refresh(account)

    # Return updated settings via get endpoint
    return await get_integration_settings(current_user, db)


@router.post("/test-connection", response_model=ConnectionTestResult)
async def test_crm_connection(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Test the CRM connection with current settings."""
    account = get_account(db, current_user.account_id)
    crm_service = get_crm_service(account)

    if not crm_service.provider:
        raise HTTPException(
            status_code=400,
            detail="No CRM provider configured",
        )

    connector = crm_service.connector
    if not connector:
        raise HTTPException(
            status_code=400,
            detail="CRM connector could not be initialized. Check credentials.",
        )

    # Test connection
    start_time = time.time()
    result = connector.test_connection()
    duration_ms = int((time.time() - start_time) * 1000)

    # Log the test
    log_sync_operation(
        db=db,
        account_id=account.id,
        entity_id=None,
        direction=SyncDirection.PUSH.value,
        operation=SyncOperation.TEST_CONNECTION.value,
        provider=connector.provider_name,
        request_data={},
        response_data=result,
        status=SyncStatus.SUCCESS.value if result.get("success") else SyncStatus.FAILED.value,
        error_message=result.get("message") if not result.get("success") else None,
        duration_ms=duration_ms,
    )

    return ConnectionTestResult(
        success=result.get("success", False),
        message=result.get("message", "Unknown result"),
        provider=connector.provider_name,
        details=result,
    )


# ----- Sync Endpoints -----

@router.post("/sync/push", response_model=SyncResult)
async def push_to_crm(
    entity_ids: Optional[list[uuid.UUID]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Push entities to CRM."""
    account = get_account(db, current_user.account_id)
    crm_service = get_crm_service(account)

    if not crm_service.is_configured():
        raise HTTPException(status_code=400, detail="CRM not configured")

    # Get entities to sync
    query = db.query(Entity).filter(Entity.account_id == account.id)
    if entity_ids:
        query = query.filter(Entity.id.in_(entity_ids))

    entities = query.all()

    synced = 0
    failed = 0
    errors = []

    for entity in entities:
        start_time = time.time()
        result = crm_service.sync_entity(entity)
        duration_ms = int((time.time() - start_time) * 1000)

        if result.get("success"):
            synced += 1
            # Update external_id if created
            if result.get("external_id") and not entity.external_id:
                entity.external_id = result["external_id"]
                entity.external_source = crm_service.provider
                db.commit()

            log_sync_operation(
                db=db,
                account_id=account.id,
                entity_id=entity.id,
                direction=SyncDirection.PUSH.value,
                operation=result.get("operation", SyncOperation.UPDATE.value),
                provider=crm_service.provider,
                request_data=crm_service.map_entity_to_crm(entity),
                response_data=result,
                status=SyncStatus.SUCCESS.value,
                external_id=entity.external_id,
                duration_ms=duration_ms,
            )
        else:
            failed += 1
            error_msg = result.get("error", "Unknown error")
            errors.append(f"{entity.name}: {error_msg}")

            log_sync_operation(
                db=db,
                account_id=account.id,
                entity_id=entity.id,
                direction=SyncDirection.PUSH.value,
                operation=result.get("operation", SyncOperation.UPDATE.value),
                provider=crm_service.provider,
                request_data=crm_service.map_entity_to_crm(entity),
                response_data=result,
                status=SyncStatus.FAILED.value,
                error_message=error_msg,
                duration_ms=duration_ms,
            )

    # Update last sync timestamp
    crm_config = account.settings.get("crm", {})
    crm_config["last_sync_at"] = datetime.utcnow().isoformat()
    crm_config["last_sync_status"] = "success" if failed == 0 else "partial" if synced > 0 else "failed"
    account.settings["crm"] = crm_config
    db.commit()

    return SyncResult(
        success=failed == 0,
        synced_count=synced,
        failed_count=failed,
        errors=errors[:10],  # Limit errors returned
    )


@router.post("/sync/entity/{entity_id}", response_model=SyncResult)
async def sync_single_entity(
    entity_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Sync a single entity to CRM."""
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.account_id == current_user.account_id,
    ).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    account = get_account(db, current_user.account_id)
    crm_service = get_crm_service(account)

    if not crm_service.is_configured():
        raise HTTPException(status_code=400, detail="CRM not configured")

    start_time = time.time()
    result = crm_service.sync_entity(entity)
    duration_ms = int((time.time() - start_time) * 1000)

    if result.get("success"):
        if result.get("external_id") and not entity.external_id:
            entity.external_id = result["external_id"]
            entity.external_source = crm_service.provider
            db.commit()

        log_sync_operation(
            db=db,
            account_id=account.id,
            entity_id=entity.id,
            direction=SyncDirection.PUSH.value,
            operation=result.get("operation", SyncOperation.UPDATE.value),
            provider=crm_service.provider,
            request_data=crm_service.map_entity_to_crm(entity),
            response_data=result,
            status=SyncStatus.SUCCESS.value,
            external_id=entity.external_id,
            duration_ms=duration_ms,
        )

        return SyncResult(success=True, synced_count=1)

    error_msg = result.get("error", "Unknown error")
    log_sync_operation(
        db=db,
        account_id=account.id,
        entity_id=entity.id,
        direction=SyncDirection.PUSH.value,
        operation=result.get("operation", SyncOperation.UPDATE.value),
        provider=crm_service.provider,
        request_data=crm_service.map_entity_to_crm(entity),
        response_data=result,
        status=SyncStatus.FAILED.value,
        error_message=error_msg,
        duration_ms=duration_ms,
    )

    return SyncResult(success=False, failed_count=1, errors=[error_msg])


# ----- Sync Log Endpoints -----

@router.get("/sync-logs", response_model=SyncLogListResponse)
async def get_sync_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get CRM sync history."""
    query = db.query(CRMSyncLog).filter(CRMSyncLog.account_id == current_user.account_id)

    if status:
        query = query.filter(CRMSyncLog.status == status)
    if provider:
        query = query.filter(CRMSyncLog.provider == provider)

    total = query.count()
    logs = (
        query.order_by(desc(CRMSyncLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return SyncLogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
    )


# ----- Webhook Endpoints -----

@router.post("/webhooks/hubspot")
async def hubspot_webhook_receiver(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive HubSpot webhooks for contact/company updates.

    Note: HubSpot webhooks require app-level configuration and are
    typically used with OAuth apps, not private apps with API keys.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # HubSpot sends an array of events
    events = payload if isinstance(payload, list) else [payload]

    for event in events:
        # Extract relevant data
        portal_id = event.get("portalId")
        object_type = event.get("subscriptionType", "").split(".")[0]  # e.g., "company.propertyChange"
        object_id = event.get("objectId")
        change_source = event.get("changeSource")

        # Skip changes we made (to avoid loops)
        if change_source == "INTEGRATION":
            continue

        # Find account by portal_id
        # Note: This requires iterating accounts which isn't ideal for scale
        # In production, consider a portal_id lookup table
        accounts = db.query(Account).filter(
            Account.settings["crm"]["hubspot"]["portal_id"].astext == str(portal_id)
        ).all()

        for account in accounts:
            # Find matching entity by external_id
            entity = db.query(Entity).filter(
                Entity.account_id == account.id,
                Entity.external_id == str(object_id),
                Entity.external_source == "hubspot",
            ).first()

            if entity:
                # Log the webhook receipt
                log_sync_operation(
                    db=db,
                    account_id=account.id,
                    entity_id=entity.id,
                    direction=SyncDirection.PULL.value,
                    operation="webhook_received",
                    provider="hubspot",
                    request_data=event,
                    response_data={"received": True},
                    status=SyncStatus.SUCCESS.value,
                )

    return {"status": "received", "event_count": len(events)}


@router.post("/webhooks/zapier/{account_id}")
async def zapier_webhook_receiver(
    account_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive Zapier webhooks for CRM updates.

    This endpoint allows Zapier to send updates back to our platform
    when records are created/updated in the external CRM.
    """
    # Get account
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get Zapier config
    crm_config = (account.settings or {}).get("crm", {})
    zapier_config = crm_config.get("zapier", {})

    # Verify signature if secret is configured
    webhook_secret = zapier_config.get("webhook_secret")
    if webhook_secret:
        from app.services.crm.encryption import decrypt_secret
        secret = decrypt_secret(webhook_secret)

        signature = request.headers.get("X-Webhook-Signature", "")
        body = await request.body()

        if not ZapierWebhookConnector.verify_webhook_signature(body, signature, secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event")
    external_id = payload.get("external_id")
    data = payload.get("data", {})

    # Handle different event types
    if event_type == "contact.created" and external_id:
        # A new contact was created in CRM, link it to our entity if we can match
        # Match by email is common
        email = data.get("email")
        if email:
            entity = db.query(Entity).filter(
                Entity.account_id == account_id,
                Entity.email == email,
                Entity.external_id.is_(None),
            ).first()

            if entity:
                entity.external_id = external_id
                entity.external_source = "zapier"
                db.commit()

                log_sync_operation(
                    db=db,
                    account_id=account_id,
                    entity_id=entity.id,
                    direction=SyncDirection.PULL.value,
                    operation="link_external_id",
                    provider="zapier",
                    request_data=payload,
                    response_data={"linked": True, "external_id": external_id},
                    status=SyncStatus.SUCCESS.value,
                    external_id=external_id,
                )

    elif event_type == "contact.updated" and external_id:
        # Update existing entity
        entity = db.query(Entity).filter(
            Entity.account_id == account_id,
            Entity.external_id == external_id,
        ).first()

        if entity:
            # Apply updates (basic fields only for safety)
            if data.get("name"):
                entity.name = data["name"]
            if data.get("email"):
                entity.email = data["email"]
            if data.get("phone"):
                entity.phone = data["phone"]
            if data.get("address"):
                entity.address = data["address"]

            db.commit()

            log_sync_operation(
                db=db,
                account_id=account_id,
                entity_id=entity.id,
                direction=SyncDirection.PULL.value,
                operation=SyncOperation.UPDATE.value,
                provider="zapier",
                request_data=payload,
                response_data={"updated": True},
                status=SyncStatus.SUCCESS.value,
                external_id=external_id,
            )

    # Log the webhook even if no action taken
    log_sync_operation(
        db=db,
        account_id=account_id,
        entity_id=None,
        direction=SyncDirection.PULL.value,
        operation="webhook_received",
        provider="zapier",
        request_data=payload,
        response_data={"received": True, "event": event_type},
        status=SyncStatus.SUCCESS.value,
    )

    return {"status": "received", "event": event_type}


# ----- HubSpot OAuth Endpoints (placeholder) -----

@router.get("/hubspot/oauth/authorize")
async def hubspot_oauth_start(
    current_user: User = Depends(get_current_active_user),
):
    """
    Initiate HubSpot OAuth flow.

    Redirects user to HubSpot authorization page.
    """
    client_id = getattr(settings, 'hubspot_client_id', None)
    redirect_uri = getattr(settings, 'hubspot_oauth_redirect_uri', None)

    if not client_id:
        raise HTTPException(
            status_code=501,
            detail="HubSpot OAuth not configured. Use API key authentication instead.",
        )

    # Build authorization URL
    scopes = "crm.objects.companies.read crm.objects.companies.write crm.objects.contacts.read crm.objects.contacts.write"
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes}"
        f"&state={current_user.account_id}"
    )

    return {"url": auth_url}


@router.get("/hubspot/oauth/callback")
async def hubspot_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Handle HubSpot OAuth callback.

    Exchanges authorization code for access token.
    """
    client_id = getattr(settings, 'hubspot_client_id', None)
    client_secret = getattr(settings, 'hubspot_client_secret', None)
    redirect_uri = getattr(settings, 'hubspot_oauth_redirect_uri', None)

    if not client_id or not client_secret:
        raise HTTPException(status_code=501, detail="HubSpot OAuth not configured")

    import requests

    # Exchange code for token
    response = requests.post(
        "https://api.hubapi.com/oauth/v1/token",
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")

    token_data = response.json()

    # Get account from state (account_id)
    try:
        account_id = uuid.UUID(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Store tokens
    current_settings = account.settings or {}
    crm_config = current_settings.get("crm", {})
    hubspot_config = crm_config.get("hubspot", {})

    hubspot_config["oauth_token"] = encrypt_secret(token_data.get("access_token", ""))
    hubspot_config["oauth_refresh_token"] = encrypt_secret(token_data.get("refresh_token", ""))
    hubspot_config["oauth_expires_at"] = datetime.utcnow().isoformat()

    crm_config["hubspot"] = hubspot_config
    crm_config["provider"] = "hubspot"
    crm_config["enabled"] = True
    current_settings["crm"] = crm_config

    account.settings = current_settings
    db.commit()

    # Return success page or redirect
    return {"success": True, "message": "HubSpot connected successfully"}
