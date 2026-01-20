"""Application settings loaded from environment variables."""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "SMB Compliance Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database - use SQLite for tests if ENVIRONMENT is "test"
    database_url: str = (
        "sqlite:///:memory:"
        if os.environ.get("ENVIRONMENT") == "test"
        else "postgresql://postgres:postgres@localhost:5432/compliance_db"
    )
    database_echo: bool = False

    # Authentication
    secret_key: str = "change-me-in-production-use-a-real-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # External Auth (optional)
    auth_provider: Optional[str] = None  # "firebase" or "auth0"
    firebase_project_id: Optional[str] = None
    auth0_domain: Optional[str] = None
    auth0_api_audience: Optional[str] = None

    # Cloud Storage
    storage_backend: str = "local"  # "local", "s3", or "gcs"
    storage_bucket: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    gcs_project_id: Optional[str] = None
    local_storage_path: str = "./storage"

    # AI/LLM
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    extraction_confidence_threshold: float = 0.8

    # OCR
    tesseract_path: Optional[str] = None
    use_google_vision: bool = False
    google_vision_api_key: Optional[str] = None

    # Email
    email_provider: str = "console"  # "console", "sendgrid", "mailgun"
    sendgrid_api_key: Optional[str] = None
    mailgun_api_key: Optional[str] = None
    mailgun_domain: Optional[str] = None
    email_from_address: str = "noreply@compliance.local"
    email_from_name: str = "Compliance Platform"

    # Redis (for Celery and caching)
    redis_url: str = "redis://localhost:6379/0"

    # Niche Configuration
    niches_config_path: str = "./configs/niches"

    # CRM Integration
    integration_secrets_key: Optional[str] = None  # Key for encrypting API keys in DB
    api_base_url: str = "http://localhost:8000"  # Base URL for webhook URLs

    # HubSpot OAuth (optional, for OAuth flow instead of API keys)
    hubspot_client_id: Optional[str] = None
    hubspot_client_secret: Optional[str] = None
    hubspot_oauth_redirect_uri: str = "http://localhost:8000/api/v1/integrations/hubspot/oauth/callback"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
