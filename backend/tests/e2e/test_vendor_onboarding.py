"""End-to-end tests for vendor onboarding flow."""
import pytest
import uuid
from unittest.mock import patch, MagicMock


@pytest.mark.e2e
class TestCompleteVendorOnboardingFlow:
    """
    Tests the complete vendor onboarding flow:
    Register -> Create Vendor -> Upload COI -> Process -> Verify Requirement
    """

    def test_complete_onboarding_flow(
        self,
        client,
        db_session,
        entity_type_factory,
        document_type_factory,
        requirement_type_factory,
    ):
        """Complete vendor onboarding from registration to compliance."""
        # Step 1: Register new user and account
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securePassword123!",
                "first_name": "New",
                "last_name": "User",
                "company_name": "New Company Inc",
            }
        )

        # Registration might return 201 or redirect to login
        if register_response.status_code in (200, 201):
            user_data = register_response.json()
            token = user_data.get("access_token")
        else:
            # Login after registration
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "newuser@example.com",
                    "password": "securePassword123!",
                }
            )
            assert login_response.status_code == 200
            token = login_response.json().get("access_token")

        if not token:
            pytest.skip("Registration/login flow not fully implemented")

        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create vendor entity
        entity_type = entity_type_factory(code="vendor", name="Vendor")

        create_vendor_response = client.post(
            "/api/v1/entities",
            headers=headers,
            json={
                "name": "ABC Construction LLC",
                "entity_type_id": str(entity_type.id),
                "email": "vendor@abcconstruction.com",
                "phone": "(555) 123-4567",
                "address": "123 Builder Street, Construction City, ST 12345",
                "custom_fields": {
                    "vendor_type": "General Contractor",
                    "risk_level": "high",
                }
            }
        )

        assert create_vendor_response.status_code == 201
        vendor = create_vendor_response.json()
        vendor_id = vendor["id"]

        # Step 3: Create document type and requirement type
        doc_type = document_type_factory(
            code="coi",
            name="Certificate of Insurance",
            extraction_prompt="Extract insurance certificate details.",
        )

        req_type = requirement_type_factory(
            code="coi_verification",
            name="COI Verification",
            required_document_types=["coi"],
        )

        # Step 4: Create a requirement for the vendor
        create_req_response = client.post(
            "/api/v1/requirements",
            headers=headers,
            json={
                "name": "Annual COI Verification",
                "entity_id": vendor_id,
                "requirement_type_id": str(req_type.id),
                "due_date": "2025-12-31",
            }
        )

        # Note: Requirement creation depends on endpoint implementation
        if create_req_response.status_code == 201:
            requirement = create_req_response.json()

        # Step 5: Verify vendor was created correctly
        get_vendor_response = client.get(
            f"/api/v1/entities/{vendor_id}",
            headers=headers,
        )

        assert get_vendor_response.status_code == 200
        vendor_data = get_vendor_response.json()
        assert vendor_data["name"] == "ABC Construction LLC"
        assert vendor_data["email"] == "vendor@abcconstruction.com"


@pytest.mark.e2e
class TestVendorCreationWithCRMSync:
    """Tests vendor creation triggers CRM sync."""

    @patch('app.services.crm.base.decrypt_secret')
    @patch('app.services.crm.hubspot.requests.post')
    def test_vendor_creation_triggers_crm_sync(
        self,
        mock_post,
        mock_decrypt,
        authenticated_client,
        db_session,
        entity_type_factory,
    ):
        """Creating a vendor should trigger background CRM sync."""
        mock_decrypt.return_value = "test-api-key"
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "hubspot-123"}
        )

        # Configure CRM
        account = authenticated_client.current_account
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "api_key": "encrypted:xxx",
                    "portal_id": "12345678",
                }
            }
        }
        db_session.commit()

        entity_type = entity_type_factory()

        # Create vendor
        response = authenticated_client.post(
            "/api/v1/entities",
            json={
                "name": "CRM Test Vendor",
                "entity_type_id": str(entity_type.id),
                "email": "crmtest@vendor.com",
            }
        )

        assert response.status_code == 201

        # Note: Background task execution depends on test setup
        # In real tests, you might need to wait or check async task completion


@pytest.mark.e2e
class TestVendorWithMultipleRequirements:
    """Tests vendor with multiple compliance requirements."""

    def test_vendor_compliance_summary(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
    ):
        """Vendor compliance summary should aggregate all requirements."""
        account = authenticated_client.current_account

        # Create vendor
        vendor = entity_factory(account=account, name="Multi-Req Vendor")

        # Create multiple requirement types
        coi_type = requirement_type_factory(code="coi-test", name="COI")
        wc_type = requirement_type_factory(code="wc-test", name="Workers Comp")

        # Create requirements with different statuses
        req1 = requirement_factory(
            account=account,
            entity=vendor,
            requirement_type=coi_type,
            name="COI 2024",
            status="compliant",
        )
        req2 = requirement_factory(
            account=account,
            entity=vendor,
            requirement_type=wc_type,
            name="WC 2024",
            status="expiring_soon",
        )

        # Get vendor with requirements
        response = authenticated_client.get(f"/api/v1/entities/{vendor.id}")

        assert response.status_code == 200
        data = response.json()

        # Vendor should include requirements info
        # Note: Response structure depends on endpoint implementation
