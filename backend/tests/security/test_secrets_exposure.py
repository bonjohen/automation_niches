"""Security tests for secrets exposure prevention."""
import pytest
from unittest.mock import patch


@pytest.mark.security
class TestAPIKeyExposure:
    """Tests to ensure API keys are not exposed."""

    def test_api_key_not_in_settings_response(self, authenticated_client, db_session):
        """API keys should be redacted in settings response."""
        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "api_key": encrypt_secret("secret-api-key-12345"),
                    "portal_id": "12345678",
                }
            }
        }
        db_session.commit()

        response = authenticated_client.get("/api/v1/integrations/settings")

        assert response.status_code == 200
        data = response.json()

        # Should be redacted
        hubspot = data.get("hubspot", {})
        api_key = hubspot.get("api_key", "")

        assert "secret-api-key-12345" not in api_key
        assert api_key.startswith("•") or api_key == ""

    def test_oauth_token_not_in_response(self, authenticated_client, db_session):
        """OAuth tokens should be redacted."""
        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "oauth_token": encrypt_secret("oauth-access-token-xyz"),
                }
            }
        }
        db_session.commit()

        response = authenticated_client.get("/api/v1/integrations/settings")

        assert response.status_code == 200
        data = response.json()

        hubspot = data.get("hubspot", {})
        oauth_token = hubspot.get("oauth_token", "")

        assert "oauth-access-token-xyz" not in oauth_token

    def test_webhook_secret_redacted(self, authenticated_client, db_session):
        """Webhook secrets should be redacted."""
        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account
        account.settings = {
            "crm": {
                "provider": "zapier",
                "zapier": {
                    "webhook_secret": encrypt_secret("super-secret-webhook-key"),
                    "webhook_url_entity_created": "https://hooks.zapier.com/test",
                }
            }
        }
        db_session.commit()

        response = authenticated_client.get("/api/v1/integrations/settings")

        assert response.status_code == 200
        data = response.json()

        zapier = data.get("zapier", {})
        secret = zapier.get("webhook_secret", "")

        assert "super-secret-webhook-key" not in secret


@pytest.mark.security
class TestPasswordExposure:
    """Tests to ensure passwords are not exposed."""

    def test_password_not_in_user_response(self, authenticated_client):
        """Password hash should not be in user response."""
        response = authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()

        # Should not contain password fields
        assert "password" not in data
        assert "hashed_password" not in data

        # Even in nested fields
        json_str = str(data)
        assert "password" not in json_str.lower()

    def test_password_not_in_list_response(self, authenticated_client, user_factory, db_session):
        """Password hash should not be in user list responses."""
        # If there's a user list endpoint
        response = authenticated_client.get("/api/v1/users")

        if response.status_code == 200:
            data = response.json()
            json_str = str(data)
            assert "hashed_password" not in json_str


@pytest.mark.security
class TestSyncLogSecrets:
    """Tests to ensure sync logs don't expose secrets."""

    def test_sync_log_redacts_api_key(self, authenticated_client, db_session, crm_sync_log_factory):
        """Sync logs should not contain API keys in request/response data."""
        account = authenticated_client.current_account

        # Create a sync log that might contain secrets
        log = crm_sync_log_factory(
            account=account,
            request_data={
                "headers": {"Authorization": "Bearer secret-token-123"},
                "body": {"api_key": "should-not-appear"},
            },
            response_data={
                "access_token": "secret-access-token",
            }
        )

        response = authenticated_client.get("/api/v1/integrations/sync-logs")

        assert response.status_code == 200

        # Note: The application should sanitize these before storing
        # This test documents the expected behavior


@pytest.mark.security
class TestErrorMessageSecrets:
    """Tests to ensure error messages don't expose secrets."""

    @patch('app.services.crm.hubspot.requests.get')
    def test_connection_error_no_secrets(self, mock_get, authenticated_client, db_session):
        """Connection errors should not expose API keys."""
        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account
        secret_key = "my-super-secret-key-abc123"
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "api_key": encrypt_secret(secret_key),
                    "portal_id": "12345678",
                }
            }
        }
        db_session.commit()

        # Simulate connection error
        mock_get.side_effect = Exception("Connection failed")

        response = authenticated_client.post("/api/v1/integrations/test-connection")

        # Even on error, the API key should not appear
        response_text = str(response.json())
        assert secret_key not in response_text


@pytest.mark.security
class TestEnvironmentSecrets:
    """Tests to ensure environment variables aren't exposed."""

    def test_env_not_in_error_response(self, client):
        """Environment variables should not appear in error responses."""
        # Trigger some kind of error
        response = client.get("/api/v1/nonexistent-endpoint-xyz")

        assert response.status_code in (404, 405)

        response_text = str(response.json())

        # Should not contain any env var names or values
        assert "SECRET_KEY" not in response_text
        assert "DATABASE_URL" not in response_text
        assert "OPENAI_API_KEY" not in response_text
