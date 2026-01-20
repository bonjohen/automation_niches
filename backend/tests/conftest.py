"""
Shared pytest fixtures for the SMB Compliance Automation Platform tests.

This module provides:
- Test database session with transaction rollback per test
- FastAPI TestClient with database override
- Authenticated client fixture with JWT token
- Factory registration for test data generation
"""
import os
import pytest
from datetime import datetime, timedelta
from typing import Generator, Any
from unittest.mock import MagicMock
import uuid

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-not-for-production")
os.environ.setdefault("CRM_SECRETS_KEY", "test-crm-secrets-key-32bytes!")

from app.models.base import Base
from app.models import (
    Account, User, Entity, EntityType,
    Requirement, RequirementType, Document, DocumentType,
    CRMSyncLog
)
from app.models.user import UserRole

# Note: get_db is imported inside fixtures to avoid early database connection


# Test database URL - use SQLite for fast tests, or override with PostgreSQL
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:"
)


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    if TEST_DATABASE_URL.startswith("sqlite"):
        # SQLite in-memory requires special config for multithreading
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(TEST_DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after test session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """
    Provide a database session with transaction rollback per test.

    Each test runs in its own transaction that is rolled back at the end,
    ensuring test isolation without the overhead of recreating tables.
    """
    connection = engine.connect()
    transaction = connection.begin()

    # Create session bound to the connection
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    # Begin a nested transaction (savepoint)
    nested = connection.begin_nested()

    # If the application code calls session.commit(), we need to
    # restart the savepoint
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if transaction.nested and not transaction._parent.nested:
            nested = connection.begin_nested()

    yield session

    # Rollback everything
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI TestClient with database override.
    """
    from main import app
    from app.config.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session is managed by db_session fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# =============================================================================
# Factory Fixtures - Pre-created test data
# =============================================================================

@pytest.fixture
def account_factory(db_session: Session):
    """Factory for creating test accounts."""
    def _create_account(
        name: str = "Test Company",
        slug: str = None,
        email: str = "test@example.com",
        is_active: bool = True,
        settings: dict = None,
        **kwargs
    ) -> Account:
        if slug is None:
            slug = f"test-company-{uuid.uuid4().hex[:8]}"

        account = Account(
            name=name,
            slug=slug,
            email=email,
            is_active=is_active,
            settings=settings or {},
            branding={},
            **kwargs
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        return account

    return _create_account


@pytest.fixture
def user_factory(db_session: Session, account_factory):
    """Factory for creating test users."""
    def _create_user(
        email: str = None,
        password: str = "testpassword123",
        first_name: str = "Test",
        last_name: str = "User",
        role: UserRole = UserRole.ADMIN,
        account: Account = None,
        is_active: bool = True,
        **kwargs
    ) -> User:
        if email is None:
            email = f"test-{uuid.uuid4().hex[:8]}@example.com"

        if account is None:
            account = account_factory()

        # Hash password (simple hash for testing)
        from hashlib import sha256
        hashed_password = sha256(password.encode()).hexdigest()

        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            account_id=account.id,
            is_active=is_active,
            email_verified=True,
            **kwargs
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
def entity_type_factory(db_session: Session):
    """Factory for creating entity types."""
    def _create_entity_type(
        code: str = None,
        name: str = "Vendor",
        description: str = "A vendor or supplier",
        niche_id: str = "coi_tracking",
        **kwargs
    ) -> EntityType:
        if code is None:
            code = f"vendor-{uuid.uuid4().hex[:8]}"

        entity_type = EntityType(
            code=code,
            name=name,
            description=description,
            niche_id=niche_id,
            field_schema={},
            **kwargs
        )
        db_session.add(entity_type)
        db_session.commit()
        db_session.refresh(entity_type)
        return entity_type

    return _create_entity_type


@pytest.fixture
def entity_factory(db_session: Session, account_factory, entity_type_factory):
    """Factory for creating entities."""
    def _create_entity(
        name: str = "Test Vendor LLC",
        email: str = "vendor@example.com",
        phone: str = "(555) 123-4567",
        address: str = "123 Test Street",
        status: str = "active",
        account: Account = None,
        entity_type: EntityType = None,
        external_id: str = None,
        external_source: str = None,
        custom_fields: dict = None,
        **kwargs
    ) -> Entity:
        if account is None:
            account = account_factory()
        if entity_type is None:
            entity_type = entity_type_factory()

        entity = Entity(
            name=name,
            email=email,
            phone=phone,
            address=address,
            status=status,
            account_id=account.id,
            entity_type_id=entity_type.id,
            external_id=external_id,
            external_source=external_source,
            custom_fields=custom_fields or {},
            tags=[],
            **kwargs
        )
        db_session.add(entity)
        db_session.commit()
        db_session.refresh(entity)
        return entity

    return _create_entity


@pytest.fixture
def requirement_type_factory(db_session: Session):
    """Factory for creating requirement types."""
    def _create_requirement_type(
        code: str = None,
        name: str = "COI Verification",
        description: str = "Verify certificate of insurance",
        frequency: str = "annually",
        default_priority: str = "medium",
        niche_id: str = "coi_tracking",
        **kwargs
    ) -> RequirementType:
        if code is None:
            code = f"coi-{uuid.uuid4().hex[:8]}"

        requirement_type = RequirementType(
            code=code,
            name=name,
            description=description,
            frequency=frequency,
            default_priority=default_priority,
            niche_id=niche_id,
            notification_rules={"days_before": [30, 14, 7, 1]},
            applicable_entity_types=["vendor"],
            required_document_types=["coi"],
            field_schema={},
            **kwargs
        )
        db_session.add(requirement_type)
        db_session.commit()
        db_session.refresh(requirement_type)
        return requirement_type

    return _create_requirement_type


@pytest.fixture
def requirement_factory(db_session: Session, account_factory, entity_factory, requirement_type_factory):
    """Factory for creating requirements."""
    from datetime import date

    def _create_requirement(
        name: str = "COI Verification 2024",
        description: str = "Annual COI verification",
        due_date: date = None,
        effective_date: date = None,
        status: str = "pending",
        priority: str = "medium",
        account: Account = None,
        entity: Entity = None,
        requirement_type: RequirementType = None,
        **kwargs
    ) -> Requirement:
        if due_date is None:
            due_date = date.today() + timedelta(days=30)
        if effective_date is None:
            effective_date = date.today()
        if account is None:
            account = account_factory()
        if entity is None:
            entity = entity_factory(account=account)
        if requirement_type is None:
            requirement_type = requirement_type_factory()

        requirement = Requirement(
            name=name,
            description=description,
            due_date=due_date,
            effective_date=effective_date,
            status=status,
            priority=priority,
            account_id=account.id,
            entity_id=entity.id,
            requirement_type_id=requirement_type.id,
            custom_fields={},
            **kwargs
        )
        db_session.add(requirement)
        db_session.commit()
        db_session.refresh(requirement)
        return requirement

    return _create_requirement


@pytest.fixture
def document_type_factory(db_session: Session):
    """Factory for creating document types."""
    def _create_document_type(
        code: str = None,
        name: str = "Certificate of Insurance",
        description: str = "Insurance certificate document",
        niche_id: str = "coi_tracking",
        **kwargs
    ) -> DocumentType:
        if code is None:
            code = f"coi-{uuid.uuid4().hex[:8]}"

        document_type = DocumentType(
            code=code,
            name=name,
            description=description,
            niche_id=niche_id,
            accepted_mime_types=["application/pdf", "image/png", "image/jpeg"],
            extraction_schema={
                "type": "object",
                "properties": {
                    "named_insured": {"type": "string"},
                    "policy_number": {"type": "string"},
                    "expiration_date": {"type": "string", "format": "date"},
                    "general_liability_limit": {"type": "number"},
                }
            },
            validation_rules={},
            **kwargs
        )
        db_session.add(document_type)
        db_session.commit()
        db_session.refresh(document_type)
        return document_type

    return _create_document_type


@pytest.fixture
def document_factory(db_session: Session, account_factory, entity_factory, document_type_factory):
    """Factory for creating documents."""
    def _create_document(
        filename: str = None,
        original_filename: str = "test_coi.pdf",
        mime_type: str = "application/pdf",
        file_size: int = 12345,
        storage_path: str = None,
        status: str = "uploaded",
        account: Account = None,
        entity: Entity = None,
        document_type: DocumentType = None,
        extracted_data: dict = None,
        **kwargs
    ) -> Document:
        if filename is None:
            filename = f"{uuid.uuid4().hex}.pdf"
        if storage_path is None:
            storage_path = f"/uploads/{filename}"
        if account is None:
            account = account_factory()
        if entity is None:
            entity = entity_factory(account=account)
        if document_type is None:
            document_type = document_type_factory()

        document = Document(
            filename=filename,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=storage_path,
            status=status,
            account_id=account.id,
            entity_id=entity.id,
            document_type_id=document_type.id,
            extracted_data=extracted_data or {},
            field_confidences={},
            document_metadata={},
            tags=[],
            **kwargs
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        return document

    return _create_document


@pytest.fixture
def crm_sync_log_factory(db_session: Session, account_factory, entity_factory):
    """Factory for creating CRM sync logs."""
    def _create_crm_sync_log(
        direction: str = "push",
        operation: str = "create",
        provider: str = "hubspot",
        status: str = "success",
        account: Account = None,
        entity: Entity = None,
        external_id: str = None,
        request_data: dict = None,
        response_data: dict = None,
        error_message: str = None,
        duration_ms: int = 150,
        **kwargs
    ) -> CRMSyncLog:
        if account is None:
            account = account_factory()

        sync_log = CRMSyncLog(
            account_id=account.id,
            entity_id=entity.id if entity else None,
            direction=direction,
            operation=operation,
            provider=provider,
            status=status,
            external_id=external_id,
            request_data=request_data or {},
            response_data=response_data or {},
            error_message=error_message,
            duration_ms=duration_ms,
            **kwargs
        )
        db_session.add(sync_log)
        db_session.commit()
        db_session.refresh(sync_log)
        return sync_log

    return _create_crm_sync_log


# =============================================================================
# Authenticated Client Fixture
# =============================================================================

@pytest.fixture
def authenticated_client(client: TestClient, user_factory, account_factory) -> TestClient:
    """
    Provide an authenticated TestClient with a valid JWT token.

    The client has a `current_user` attribute with the test user.
    """
    account = account_factory()
    user = user_factory(account=account, email="auth-test@example.com")

    # Create a JWT token for the user
    # This mimics what the actual auth system would do
    from datetime import datetime, timedelta
    import jwt

    secret_key = os.environ.get("SECRET_KEY", "test-secret-key")
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "account_id": str(user.account_id),
        "role": user.role.value,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    # Set the auth header
    client.headers["Authorization"] = f"Bearer {token}"

    # Attach user info for test assertions
    client.current_user = user
    client.current_account = account

    return client


# =============================================================================
# Mock Fixtures for External Services
# =============================================================================

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for AI extraction tests."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"named_insured": "Test Company", "policy_number": "POL-123"}'
                )
            )
        ]
    )
    return mock


@pytest.fixture
def mock_hubspot_api(requests_mock):
    """Mock HubSpot API responses."""
    # Base URL for HubSpot API
    base_url = "https://api.hubapi.com"

    # Account info (for test_connection)
    requests_mock.get(
        f"{base_url}/account-info/v3/details",
        json={"portalId": 12345678, "accountType": "STANDARD"}
    )

    # Companies endpoint
    requests_mock.get(
        f"{base_url}/crm/v3/objects/companies",
        json={
            "results": [
                {"id": "1", "properties": {"name": "Test Company", "domain": "test.com"}}
            ],
            "paging": {}
        }
    )

    # Create company
    requests_mock.post(
        f"{base_url}/crm/v3/objects/companies",
        json={"id": "new-123", "properties": {"name": "New Company"}},
        status_code=201
    )

    return requests_mock
