"""API routes initialization."""
from fastapi import APIRouter

from .endpoints import entities, requirements, documents, notifications, auth, integrations

router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(entities.router, prefix="/entities", tags=["Entities"])
router.include_router(requirements.router, prefix="/requirements", tags=["Requirements"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])


@router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "SMB Compliance Platform API",
        "endpoints": {
            "auth": "/auth",
            "entities": "/entities",
            "requirements": "/requirements",
            "documents": "/documents",
            "notifications": "/notifications",
            "integrations": "/integrations",
        }
    }
