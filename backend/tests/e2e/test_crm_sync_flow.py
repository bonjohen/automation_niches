"""End-to-end tests for CRM sync flow."""
import pytest
from unittest.mock import patch, MagicMock
import responses


@pytest.mark.e2e
class TestHubSpotSyncFlow:
    """
    Tests the complete HubSpot CRM sync flow:
    Configure HubSpot -> Create Entity -> Verify Sync -> Update -> Verify Update
    """

    @responses.activate
    def test_hubspot_complete_sync_flow(
        self,
        authenticated_client,
        db_session,
        entity_type_factory,
    ):
        """Complete HubSpot sync flow from configuration to entity sync."""
        account = authenticated_client.current_account

        # Step 1: Configure HubSpot integration
        config_response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "api_key": "test-hubspot-api-key",
                    "portal_id": "12345678",
                    "object_type": "companies",
                }
            }
        )

        assert config_response.status_code == 200

        # Step 2: Mock HubSpot API for connection test
        responses.add(
            responses.GET,
            "https://api.hubapi.com/account-info/v3/details",
            json={"portalId": 12345678},
            status=200,
        )

        # Step 3: Test connection
        with patch('app.services.crm.base.decrypt_secret', return_value="test-hubspot-api-key"):
            test_response = authenticated_client.post("/api/v1/integrations/test-connection")

        assert test_response.status_code == 200
        assert test_response.json()["success"] is True

        # Step 4: Create entity
        entity_type = entity_type_factory()

        # Mock HubSpot create company endpoint
        responses.add(
            responses.POST,
            "https://api.hubapi.com/crm/v3/objects/companies",
            json={"id": "hubspot-company-123"},
            status=201,
        )

        with patch('app.services.crm.base.decrypt_secret', return_value="test-hubspot-api-key"):
            create_response = authenticated_client.post(
                "/api/v1/entities",
                json={
                    "name": "HubSpot Test Vendor",
                    "entity_type_id": str(entity_type.id),
                    "email": "hubspot-test@vendor.com",
                }
            )

        assert create_response.status_code == 201
        entity_id = create_response.json()["id"]

        # Step 5: Manually trigger sync (since background tasks don't run in tests)
        with patch('app.services.crm.base.decrypt_secret', return_value="test-hubspot-api-key"):
            sync_response = authenticated_client.post(
                f"/api/v1/integrations/sync/entity/{entity_id}"
            )

        assert sync_response.status_code == 200
        sync_data = sync_response.json()
        assert sync_data["synced_count"] == 1

        # Step 6: Verify sync log was created
        logs_response = authenticated_client.get("/api/v1/integrations/sync-logs")
        assert logs_response.status_code == 200
        logs = logs_response.json()["items"]
        assert len(logs) >= 1


@pytest.mark.e2e
class TestZapierWebhookFlow:
    """
    Tests the complete Zapier webhook flow:
    Configure Zapier -> Create Entity -> Receive Webhook -> Verify Link
    """

    @responses.activate
    def test_zapier_webhook_roundtrip(
        self,
        authenticated_client,
        db_session,
        entity_type_factory,
    ):
        """Complete Zapier webhook roundtrip."""
        account = authenticated_client.current_account

        # Step 1: Configure Zapier integration
        config_response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={
                "enabled": True,
                "provider": "zapier",
                "zapier": {
                    "webhook_url_entity_created": "https://hooks.zapier.com/test/entity-created",
                    "webhook_url_entity_updated": "https://hooks.zapier.com/test/entity-updated",
                    "webhook_secret": "test-webhook-secret",
                }
            }
        )

        assert config_response.status_code == 200

        # Step 2: Mock Zapier webhook endpoint
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"status": "ok"},
            status=200,
        )

        # Step 3: Create entity (triggers outbound webhook)
        entity_type = entity_type_factory()

        with patch('app.services.crm.base.decrypt_secret', return_value="test-webhook-secret"):
            create_response = authenticated_client.post(
                "/api/v1/entities",
                json={
                    "name": "Zapier Test Vendor",
                    "entity_type_id": str(entity_type.id),
                    "email": "zapier-test@vendor.com",
                }
            )

        assert create_response.status_code == 201
        entity_data = create_response.json()
        entity_id = entity_data["id"]

        # Entity initially has no external_id
        assert entity_data.get("external_id") is None

        # Step 4: Simulate inbound webhook from Zapier (CRM created the record)
        import hmac
        import hashlib
        import json

        webhook_payload = {
            "event": "contact.created",
            "external_id": "zapier-crm-record-456",
            "data": {
                "email": "zapier-test@vendor.com",
            }
        }
        payload_json = json.dumps(webhook_payload)
        signature = hmac.new(
            "test-webhook-secret".encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()

        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as webhook_client:
            webhook_response = webhook_client.post(
                f"/api/v1/integrations/webhooks/zapier/{account.id}",
                content=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                }
            )

        assert webhook_response.status_code == 200

        # Step 5: Verify entity now has external_id
        get_response = authenticated_client.get(f"/api/v1/entities/{entity_id}")
        assert get_response.status_code == 200
        updated_entity = get_response.json()

        assert updated_entity["external_id"] == "zapier-crm-record-456"
        assert updated_entity["external_source"] == "zapier"


@pytest.mark.e2e
class TestCRMSyncErrorHandling:
    """Tests CRM sync error handling and recovery."""

    @responses.activate
    def test_sync_failure_logs_error(
        self,
        authenticated_client,
        db_session,
        entity_factory,
    ):
        """Failed sync should log error and not crash."""
        account = authenticated_client.current_account

        # Configure HubSpot
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

        # Create entity
        entity = entity_factory(account=account, name="Error Test Vendor")

        # Mock HubSpot API to return error
        responses.add(
            responses.POST,
            "https://api.hubapi.com/crm/v3/objects/companies",
            json={"status": "error", "message": "Rate limit exceeded"},
            status=429,
        )

        with patch('app.services.crm.base.decrypt_secret', return_value="test-api-key"):
            sync_response = authenticated_client.post(
                f"/api/v1/integrations/sync/entity/{entity.id}"
            )

        # Should return success=False but not crash
        assert sync_response.status_code == 200
        data = sync_response.json()
        assert data["success"] is False
        assert data["failed_count"] == 1
        assert len(data["errors"]) > 0

        # Verify error was logged
        logs_response = authenticated_client.get(
            "/api/v1/integrations/sync-logs",
            params={"status": "failed"}
        )
        assert logs_response.status_code == 200
        assert logs_response.json()["total"] >= 1
