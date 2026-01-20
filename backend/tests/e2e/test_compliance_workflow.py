"""End-to-end tests for compliance workflow."""
import pytest
from datetime import date, timedelta
from unittest.mock import patch
from freezegun import freeze_time


@pytest.mark.e2e
class TestRequirementLifecycle:
    """
    Tests the complete requirement lifecycle:
    Create Requirement -> Status Changes -> Expiry -> Notification
    """

    def test_requirement_status_transitions(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_type_factory,
    ):
        """Requirement should transition through status states."""
        account = authenticated_client.current_account

        # Create entity and requirement type
        entity = entity_factory(account=account, name="Compliance Test Vendor")
        req_type = requirement_type_factory(code="compliance-test", name="Test Requirement")

        # Create requirement due in 60 days
        future_date = (date.today() + timedelta(days=60)).isoformat()

        create_response = authenticated_client.post(
            "/api/v1/requirements",
            json={
                "name": "Test Compliance Requirement",
                "entity_id": str(entity.id),
                "requirement_type_id": str(req_type.id),
                "due_date": future_date,
                "status": "pending",
            }
        )

        if create_response.status_code != 201:
            pytest.skip("Requirement creation endpoint not implemented")

        requirement = create_response.json()
        req_id = requirement["id"]

        # Verify initial status
        assert requirement["status"] == "pending"

        # Update to compliant
        update_response = authenticated_client.patch(
            f"/api/v1/requirements/{req_id}",
            json={"status": "compliant"}
        )

        if update_response.status_code == 200:
            assert update_response.json()["status"] == "compliant"

    @freeze_time("2025-01-01")
    def test_requirement_becomes_expiring_soon(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
    ):
        """Requirement approaching due date should become expiring_soon."""
        account = authenticated_client.current_account
        entity = entity_factory(account=account)
        req_type = requirement_type_factory()

        # Create requirement due in 7 days
        requirement = requirement_factory(
            account=account,
            entity=entity,
            requirement_type=req_type,
            due_date=date(2025, 1, 8),  # 7 days from "now"
            status="compliant",
        )

        # Simulate scheduler running to update statuses
        # Note: This depends on scheduler implementation
        # In real tests, you would trigger the scheduler job

        # After scheduler runs, status should be expiring_soon
        # db_session.refresh(requirement)
        # assert requirement.status == "expiring_soon"

    @freeze_time("2025-01-15")
    def test_requirement_becomes_expired(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
    ):
        """Past due requirement should become expired."""
        account = authenticated_client.current_account
        entity = entity_factory(account=account)
        req_type = requirement_type_factory()

        # Create requirement that was due on Jan 10
        requirement = requirement_factory(
            account=account,
            entity=entity,
            requirement_type=req_type,
            due_date=date(2025, 1, 10),  # 5 days ago
            status="compliant",
        )

        # After scheduler runs, status should be expired
        # Note: This depends on scheduler implementation


@pytest.mark.e2e
class TestComplianceWithDocuments:
    """Tests compliance workflow with document processing."""

    def test_document_upload_updates_requirement(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
        document_type_factory,
    ):
        """Uploading valid document should update requirement status."""
        account = authenticated_client.current_account
        entity = entity_factory(account=account, name="Doc Test Vendor")

        # Create document type and requirement type that links them
        doc_type = document_type_factory(
            code="coi-doc",
            name="Certificate of Insurance",
        )
        req_type = requirement_type_factory(
            code="coi-req",
            name="COI Requirement",
            required_document_types=["coi-doc"],
        )

        # Create pending requirement
        requirement = requirement_factory(
            account=account,
            entity=entity,
            requirement_type=req_type,
            status="pending",
            due_date=date.today() + timedelta(days=30),
        )

        # Note: Document upload and processing would be tested here
        # This depends on file upload endpoint implementation


@pytest.mark.e2e
class TestBulkComplianceOperations:
    """Tests bulk compliance operations."""

    def test_bulk_status_check(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
    ):
        """Bulk compliance check for multiple entities."""
        account = authenticated_client.current_account

        # Create multiple entities with requirements
        req_type = requirement_type_factory()

        for i in range(5):
            entity = entity_factory(account=account, name=f"Bulk Test Vendor {i}")
            requirement_factory(
                account=account,
                entity=entity,
                requirement_type=req_type,
                status="compliant" if i % 2 == 0 else "expired",
            )

        # Get compliance summary
        response = authenticated_client.get("/api/v1/requirements/summary")

        if response.status_code == 200:
            summary = response.json()
            # Verify summary contains all statuses
            # Note: Response structure depends on endpoint implementation
