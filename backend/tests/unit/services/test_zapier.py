"""Unit tests for Zapier webhook connector."""
import json
import pytest
import responses
from datetime import datetime


class TestZapierWebhookConnector:
    """Tests for the Zapier webhook connector."""

    @pytest.fixture
    def connector(self):
        """Create a connector with test webhook URLs."""
        from app.services.crm.zapier import ZapierWebhookConnector

        return ZapierWebhookConnector(
            webhook_url_entity_created="https://hooks.zapier.com/test/entity-created",
            webhook_url_entity_updated="https://hooks.zapier.com/test/entity-updated",
            webhook_url_compliance_changed="https://hooks.zapier.com/test/compliance-changed",
            webhook_secret="test-secret-key",
        )

    @pytest.fixture
    def connector_no_secret(self):
        """Create a connector without webhook secret."""
        from app.services.crm.zapier import ZapierWebhookConnector

        return ZapierWebhookConnector(
            webhook_url_entity_created="https://hooks.zapier.com/test/entity-created",
            webhook_secret=None,
        )

    def test_provider_name(self, connector):
        """Provider name should return 'zapier'."""
        assert connector.provider_name == "zapier"

    def test_generate_signature(self, connector):
        """Signature should be valid HMAC-SHA256."""
        payload = '{"test": "data"}'
        signature = connector._generate_signature(payload)

        # Should be a hex string
        assert len(signature) == 64  # SHA256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in signature)

    def test_generate_signature_no_secret(self, connector_no_secret):
        """Signature should be empty string when no secret is configured."""
        signature = connector_no_secret._generate_signature('{"test": "data"}')

        assert signature == ""

    def test_generate_signature_deterministic(self, connector):
        """Same payload should produce same signature."""
        payload = '{"key": "value"}'

        sig1 = connector._generate_signature(payload)
        sig2 = connector._generate_signature(payload)

        assert sig1 == sig2

    @responses.activate
    def test_send_webhook_success(self, connector):
        """Successful webhook should return success=True."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"status": "ok"},
            status=200,
        )

        result = connector._send_webhook("entity_created", {"name": "Test"})

        assert result["success"] is True
        assert result["status_code"] == 200

    @responses.activate
    def test_send_webhook_includes_signature(self, connector):
        """Webhook should include X-Webhook-Signature header."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"status": "ok"},
            status=200,
        )

        connector._send_webhook("entity_created", {"name": "Test"})

        # Check the request was made with signature header
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert "X-Webhook-Signature" in request.headers

    @responses.activate
    def test_send_webhook_no_signature_without_secret(self, connector_no_secret):
        """Webhook should not include signature when no secret is configured."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"status": "ok"},
            status=200,
        )

        connector_no_secret._send_webhook("entity_created", {"name": "Test"})

        request = responses.calls[0].request
        assert "X-Webhook-Signature" not in request.headers

    def test_send_webhook_no_url(self, connector):
        """Missing webhook URL should return error."""
        result = connector._send_webhook("nonexistent_event", {"name": "Test"})

        assert result["success"] is False
        assert "No webhook URL configured" in result["error"]

    @responses.activate
    def test_send_webhook_timeout(self, connector):
        """Timeout should be handled gracefully."""
        from requests.exceptions import Timeout

        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            body=Timeout("Connection timed out"),
        )

        result = connector._send_webhook("entity_created", {"name": "Test"})

        assert result["success"] is False
        assert "timed out" in result["error"]

    @responses.activate
    def test_send_webhook_error_status(self, connector):
        """Non-success status codes should return error."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"error": "Bad request"},
            status=400,
        )

        result = connector._send_webhook("entity_created", {"name": "Test"})

        assert result["success"] is False
        assert "400" in result["error"]

    @responses.activate
    def test_test_connection_finds_first_url(self, connector):
        """test_connection should use first configured webhook URL."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"status": "ok"},
            status=200,
        )

        result = connector.test_connection()

        assert result["success"] is True
        assert "entity_created" in result["message"]

    def test_test_connection_no_urls(self):
        """test_connection should fail when no URLs are configured."""
        from app.services.crm.zapier import ZapierWebhookConnector

        connector = ZapierWebhookConnector()

        result = connector.test_connection()

        assert result["success"] is False
        assert "No webhook URLs configured" in result["message"]

    def test_get_contacts_returns_error(self, connector):
        """get_contacts should return error (push-only connector)."""
        result = connector.get_contacts()

        assert result["success"] is False
        assert "push-only" in result["error"]
        assert result["results"] == []

    def test_get_contact_returns_error(self, connector):
        """get_contact should return error (push-only connector)."""
        result = connector.get_contact("ext-123")

        assert result["success"] is False
        assert "push-only" in result["error"]
        assert result["data"] is None

    @responses.activate
    def test_create_contact_sends_webhook(self, connector):
        """create_contact should send webhook to entity_created URL."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"status": "ok"},
            status=200,
        )

        result = connector.create_contact({
            "name": "New Vendor",
            "email": "vendor@example.com",
        })

        assert result["success"] is True
        assert result["external_id"] is None  # Zapier doesn't return ID

        # Verify payload was sent
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["event"] == "entity_created"
        assert request_body["data"]["name"] == "New Vendor"

    @responses.activate
    def test_update_contact_sends_webhook(self, connector):
        """update_contact should include external_id in payload."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-updated",
            json={"status": "ok"},
            status=200,
        )

        result = connector.update_contact("ext-123", {
            "name": "Updated Vendor",
        })

        assert result["success"] is True

        # Verify external_id is included
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["data"]["external_id"] == "ext-123"
        assert request_body["data"]["name"] == "Updated Vendor"

    @responses.activate
    def test_push_compliance_status(self, connector):
        """push_compliance_status should send to compliance_changed webhook."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/compliance-changed",
            json={"status": "ok"},
            status=200,
        )

        result = connector.push_compliance_status("ext-123", {
            "compliance_status": "compliant",
            "compliance_expiry": "2025-01-01",
        })

        assert result["success"] is True

        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["event"] == "compliance_changed"
        assert request_body["data"]["external_id"] == "ext-123"
        assert request_body["data"]["compliance_status"] == "compliant"

    def test_verify_webhook_signature_valid(self):
        """Valid signature should return True."""
        from app.services.crm.zapier import ZapierWebhookConnector

        payload = b'{"event": "entity_created", "data": {}}'
        secret = "my-secret"

        # Generate expected signature
        import hmac
        import hashlib
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        result = ZapierWebhookConnector.verify_webhook_signature(
            payload, expected_sig, secret
        )

        assert result is True

    def test_verify_webhook_signature_invalid(self):
        """Invalid signature should return False."""
        from app.services.crm.zapier import ZapierWebhookConnector

        payload = b'{"event": "entity_created"}'
        secret = "my-secret"

        result = ZapierWebhookConnector.verify_webhook_signature(
            payload, "invalid-signature", secret
        )

        assert result is False

    def test_verify_webhook_signature_no_secret(self):
        """Missing secret should return False."""
        from app.services.crm.zapier import ZapierWebhookConnector

        result = ZapierWebhookConnector.verify_webhook_signature(
            b'{"data": {}}', "some-sig", ""
        )

        assert result is False

    def test_verify_webhook_signature_no_signature(self):
        """Missing signature should return False."""
        from app.services.crm.zapier import ZapierWebhookConnector

        result = ZapierWebhookConnector.verify_webhook_signature(
            b'{"data": {}}', "", "my-secret"
        )

        assert result is False

    @responses.activate
    def test_webhook_payload_structure(self, connector):
        """Webhook payload should have correct structure."""
        responses.add(
            responses.POST,
            "https://hooks.zapier.com/test/entity-created",
            json={"status": "ok"},
            status=200,
        )

        connector._send_webhook("entity_created", {"name": "Test"})

        request_body = json.loads(responses.calls[0].request.body)

        # Required fields
        assert "event" in request_body
        assert "timestamp" in request_body
        assert "data" in request_body

        # Timestamp format (ISO 8601 with Z)
        assert request_body["timestamp"].endswith("Z")
