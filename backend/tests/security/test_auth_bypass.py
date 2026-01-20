"""Security tests for authentication bypass attempts."""
import pytest
import jwt
from datetime import datetime, timedelta


@pytest.mark.security
class TestJWTValidation:
    """Tests for JWT token validation."""

    def test_jwt_signature_invalid(self, client):
        """Requests with invalid JWT signatures should be rejected."""
        # Create a token with a different secret
        wrong_secret = "wrong-secret-key"
        payload = {
            "sub": "user-123",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401

    def test_jwt_expired(self, client):
        """Requests with expired JWT should be rejected."""
        import os
        secret = os.environ.get("SECRET_KEY", "test-secret-key-for-testing-only-not-for-production")

        payload = {
            "sub": "user-123",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401

    def test_jwt_wrong_algorithm(self, client):
        """Requests with wrong algorithm should be rejected."""
        import os
        secret = os.environ.get("SECRET_KEY", "test-secret-key-for-testing-only-not-for-production")

        payload = {
            "sub": "user-123",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        # Use HS384 instead of expected HS256
        token = jwt.encode(payload, secret, algorithm="HS384")

        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should reject due to algorithm mismatch
        assert response.status_code in (401, 403)

    def test_jwt_missing(self, client):
        """Requests without Authorization header should be rejected."""
        response = client.get("/api/v1/entities")

        assert response.status_code == 401

    def test_jwt_malformed(self, client):
        """Requests with malformed JWT should be rejected."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": "Bearer not.a.valid.jwt.token"}
        )

        assert response.status_code == 401

    def test_jwt_bearer_missing(self, client):
        """Authorization header without 'Bearer' prefix should be rejected."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": "some-token-without-bearer"}
        )

        assert response.status_code == 401

    def test_jwt_empty_bearer(self, client):
        """Empty Bearer token should be rejected."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": "Bearer "}
        )

        assert response.status_code == 401


@pytest.mark.security
class TestDisabledUser:
    """Tests for disabled/inactive user handling."""

    def test_disabled_user_token(self, client, user_factory, account_factory, db_session):
        """Active token for disabled user should be rejected."""
        import os
        secret = os.environ.get("SECRET_KEY", "test-secret-key-for-testing-only-not-for-production")

        account = account_factory()
        user = user_factory(account=account, is_active=False)  # Disabled user

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "account_id": str(user.account_id),
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should reject inactive user
        assert response.status_code in (401, 403)


@pytest.mark.security
class TestAuthEndpoints:
    """Tests for authentication endpoints security."""

    def test_login_wrong_password(self, client, user_factory, account_factory, db_session):
        """Login with wrong password should be rejected."""
        account = account_factory()
        user = user_factory(account=account, email="test@example.com", password="correct-password")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong-password"}
        )

        assert response.status_code == 401

    def test_login_unknown_email(self, client):
        """Login with unknown email should be rejected."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "anypassword"}
        )

        assert response.status_code == 401

    def test_me_unauthenticated(self, client):
        """GET /auth/me without auth should be rejected."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401


@pytest.mark.security
class TestAPIKeyLeakage:
    """Tests to ensure API keys are not leaked in responses."""

    def test_api_key_not_in_error_messages(self, authenticated_client, db_session):
        """API keys should not appear in error messages."""
        from app.services.crm.encryption import encrypt_secret

        account = authenticated_client.current_account
        secret_key = "super-secret-api-key-12345"
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "api_key": encrypt_secret(secret_key),
                }
            }
        }
        db_session.commit()

        # This should trigger some error processing
        response = authenticated_client.post("/api/v1/integrations/test-connection")

        # Regardless of success/failure, the secret should not appear
        response_text = str(response.json())
        assert secret_key not in response_text
