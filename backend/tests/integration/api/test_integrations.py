"""Integration tests for CRM integration endpoints."""
import pytest
import uuid
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestIntegrationSettings:
    """Tests for /integrations/settings endpoints."""

    def test_get_settings_default(self, authenticated_client):
        """GET /integrations/settings should return default settings."""
        response = authenticated_client.get("/api/v1/integrations/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["provider"] is None

    def test_get_settings_redacted(self, authenticated_client, db_session):
        """GET /integrations/settings should redact API keys."""
        # Setup account with HubSpot settings
        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "api_key": encrypt_secret("my-super-secret-api-key"),
                    "portal_id": "12345678",
                    "object_type": "companies",
                },
            }
        }
        db_session.commit()

        response = authenticated_client.get("/api/v1/integrations/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["provider"] == "hubspot"

        # API key should be redacted
        assert data["hubspot"]["api_key"].startswith("•")
        assert "super-secret" not in data["hubspot"]["api_key"]
        assert data["hubspot"]["has_credentials"] is True

    def test_update_settings_enable(self, authenticated_client):
        """PUT /integrations/settings should update enabled flag."""
        response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={
                "enabled": True,
                "provider": "hubspot",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["provider"] == "hubspot"

    def test_update_settings_encrypt_api_key(self, authenticated_client, db_session):
        """PUT /integrations/settings should encrypt API keys."""
        response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={
                "provider": "hubspot",
                "hubspot": {
                    "api_key": "new-api-key-12345",
                    "portal_id": "12345678",
                }
            }
        )

        assert response.status_code == 200

        # Verify the key is encrypted in database
        account = authenticated_client.current_account
        db_session.refresh(account)
        stored_key = account.settings["crm"]["hubspot"]["api_key"]

        assert stored_key.startswith("encrypted:")
        assert "new-api-key" not in stored_key

    def test_update_settings_skip_redacted(self, authenticated_client, db_session):
        """PUT /integrations/settings should not overwrite with redacted values."""
        from app.services.crm.encryption import encrypt_secret, decrypt_secret

        # Setup existing API key
        account = authenticated_client.current_account
        original_encrypted = encrypt_secret("original-secret-key")
        account.settings = {
            "crm": {
                "provider": "hubspot",
                "hubspot": {
                    "api_key": original_encrypted,
                }
            }
        }
        db_session.commit()

        # Update with redacted value (simulating frontend sending back redacted key)
        response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={
                "hubspot": {
                    "api_key": "••••••••••key",  # Redacted
                    "portal_id": "new-portal-id",
                }
            }
        )

        assert response.status_code == 200

        # Original key should still be there
        db_session.refresh(account)
        stored_key = account.settings["crm"]["hubspot"]["api_key"]
        assert decrypt_secret(stored_key) == "original-secret-key"

    def test_update_settings_zapier(self, authenticated_client):
        """PUT /integrations/settings should handle Zapier webhooks."""
        response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={
                "provider": "zapier",
                "zapier": {
                    "webhook_url_entity_created": "https://hooks.zapier.com/test/entity-created",
                    "webhook_secret": "my-webhook-secret",
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "zapier"
        assert data["zapier"]["webhook_url_entity_created"] == "https://hooks.zapier.com/test/entity-created"


@pytest.mark.integration
class TestTestConnection:
    """Tests for /integrations/test-connection endpoint."""

    def test_test_connection_not_configured(self, authenticated_client):
        """POST /integrations/test-connection should return 400 when not configured."""
        response = authenticated_client.post("/api/v1/integrations/test-connection")

        assert response.status_code == 400
        assert "not configured" in response.json()["detail"].lower()

    @patch('app.services.crm.base.decrypt_secret')
    def test_test_connection_hubspot(self, mock_decrypt, authenticated_client, db_session):
        """POST /integrations/test-connection should test HubSpot connection."""
        mock_decrypt.return_value = "test-api-key"

        # Setup HubSpot settings
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

        # Mock the HubSpot API call
        with patch('app.services.crm.hubspot.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"portalId": 12345678}
            )

            response = authenticated_client.post("/api/v1/integrations/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "hubspot"


@pytest.mark.integration
class TestSyncEndpoints:
    """Tests for /integrations/sync/* endpoints."""

    def test_push_to_crm_not_configured(self, authenticated_client):
        """POST /integrations/sync/push should return 400 when not configured."""
        response = authenticated_client.post("/api/v1/integrations/sync/push")

        assert response.status_code == 400

    @patch('app.services.crm.base.decrypt_secret')
    def test_push_to_crm_success(self, mock_decrypt, authenticated_client, db_session, entity_factory):
        """POST /integrations/sync/push should sync entities."""
        mock_decrypt.return_value = "test-api-key"

        # Setup account and entity
        account = authenticated_client.current_account
        entity = entity_factory(account=account, name="Test Vendor")

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

        # Mock HubSpot API
        with patch('app.services.crm.hubspot.requests.post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201,
                json=lambda: {"id": "new-hubspot-id"}
            )

            response = authenticated_client.post(
                "/api/v1/integrations/sync/push",
                json={"entity_ids": [str(entity.id)]}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["synced_count"] == 1
        assert data["failed_count"] == 0

    def test_sync_single_entity_not_found(self, authenticated_client):
        """POST /integrations/sync/entity/{id} should return 404 for unknown entity."""
        fake_id = uuid.uuid4()

        response = authenticated_client.post(f"/api/v1/integrations/sync/entity/{fake_id}")

        assert response.status_code == 404


@pytest.mark.integration
class TestSyncLogs:
    """Tests for /integrations/sync-logs endpoint."""

    def test_sync_logs_pagination(self, authenticated_client, crm_sync_log_factory, db_session):
        """GET /integrations/sync-logs should return paginated logs."""
        account = authenticated_client.current_account

        # Create some sync logs
        for i in range(25):
            crm_sync_log_factory(account=account, operation=f"test-{i}")

        response = authenticated_client.get(
            "/api/v1/integrations/sync-logs",
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_sync_logs_filter_status(self, authenticated_client, crm_sync_log_factory, db_session):
        """GET /integrations/sync-logs should filter by status."""
        account = authenticated_client.current_account

        # Create logs with different statuses
        crm_sync_log_factory(account=account, status="success")
        crm_sync_log_factory(account=account, status="success")
        crm_sync_log_factory(account=account, status="failed")

        response = authenticated_client.get(
            "/api/v1/integrations/sync-logs",
            params={"status": "failed"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "failed"


@pytest.mark.integration
class TestZapierWebhook:
    """Tests for /integrations/webhooks/zapier/{account_id} endpoint."""

    def test_zapier_webhook_account_not_found(self, client):
        """POST /integrations/webhooks/zapier/{id} should return 404 for unknown account."""
        fake_id = uuid.uuid4()

        response = client.post(
            f"/api/v1/integrations/webhooks/zapier/{fake_id}",
            json={"event": "test"}
        )

        assert response.status_code == 404

    def test_zapier_webhook_valid_signature(self, authenticated_client, db_session):
        """POST /integrations/webhooks/zapier/{id} should accept valid signature."""
        import hmac
        import hashlib
        import json

        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account
        webhook_secret = "my-webhook-secret"

        # Configure Zapier with webhook secret
        account.settings = {
            "crm": {
                "provider": "zapier",
                "zapier": {
                    "webhook_secret": encrypt_secret(webhook_secret),
                }
            }
        }
        db_session.commit()

        # Build signed payload
        payload = {"event": "contact.created", "external_id": "ext-123", "data": {"name": "Test"}}
        payload_json = json.dumps(payload)
        signature = hmac.new(
            webhook_secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()

        # Need to use TestClient directly since authenticated_client adds auth headers
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/integrations/webhooks/zapier/{account.id}",
                content=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"

    def test_zapier_webhook_invalid_signature(self, authenticated_client, db_session):
        """POST /integrations/webhooks/zapier/{id} should reject invalid signature."""
        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account

        # Configure Zapier with webhook secret
        account.settings = {
            "crm": {
                "provider": "zapier",
                "zapier": {
                    "webhook_secret": encrypt_secret("correct-secret"),
                }
            }
        }
        db_session.commit()

        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/integrations/webhooks/zapier/{account.id}",
                json={"event": "test"},
                headers={"X-Webhook-Signature": "wrong-signature"}
            )

        assert response.status_code == 401

    def test_zapier_webhook_links_external_id(self, authenticated_client, db_session, entity_factory):
        """POST /integrations/webhooks/zapier/{id} should link external_id to entity."""
        account = authenticated_client.current_account

        # Create an entity without external_id
        entity = entity_factory(
            account=account,
            name="Test Entity",
            email="test@example.com",
            external_id=None,
        )

        # No webhook secret (signature validation skipped)
        account.settings = {"crm": {"provider": "zapier", "zapier": {}}}
        db_session.commit()

        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/integrations/webhooks/zapier/{account.id}",
                json={
                    "event": "contact.created",
                    "external_id": "crm-record-123",
                    "data": {"email": "test@example.com"},
                }
            )

        assert response.status_code == 200

        # Entity should now have external_id
        db_session.refresh(entity)
        assert entity.external_id == "crm-record-123"
        assert entity.external_source == "zapier"
