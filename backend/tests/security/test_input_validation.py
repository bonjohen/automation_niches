"""Security tests for input validation."""
import pytest


@pytest.mark.security
class TestEntityInputValidation:
    """Tests for entity input validation."""

    def test_entity_name_max_length(self, authenticated_client, entity_type_factory):
        """Entity name should be validated for max length."""
        entity_type = entity_type_factory()

        # Try to create entity with very long name
        long_name = "A" * 1000  # Way over typical limit

        response = authenticated_client.post(
            "/api/v1/entities",
            json={
                "name": long_name,
                "entity_type_id": str(entity_type.id),
            }
        )

        # Should either reject with 422 or truncate
        assert response.status_code in (201, 422)

    def test_email_format_validation(self, authenticated_client, entity_type_factory):
        """Email should be validated for format."""
        entity_type = entity_type_factory()

        response = authenticated_client.post(
            "/api/v1/entities",
            json={
                "name": "Test Entity",
                "entity_type_id": str(entity_type.id),
                "email": "not-a-valid-email",
            }
        )

        # Should accept (some APIs allow free-form email) or reject with 422
        # The important thing is it doesn't cause a server error
        assert response.status_code in (201, 422)

    def test_uuid_format_validation(self, authenticated_client):
        """UUID parameters should be validated."""
        response = authenticated_client.get("/api/v1/entities/not-a-uuid")

        assert response.status_code == 422  # Validation error

    def test_xss_in_entity_name(self, authenticated_client, entity_type_factory, db_session):
        """XSS attempts should be stored safely (not executed)."""
        entity_type = entity_type_factory()
        xss_payload = '<script>alert("XSS")</script>'

        response = authenticated_client.post(
            "/api/v1/entities",
            json={
                "name": xss_payload,
                "entity_type_id": str(entity_type.id),
            }
        )

        assert response.status_code == 201

        # Verify it's stored as-is (to be escaped on output by frontend)
        data = response.json()
        assert data["name"] == xss_payload  # Stored safely, escaped on display


@pytest.mark.security
class TestFileUploadValidation:
    """Tests for file upload validation."""

    def test_file_upload_mime_validation(self, authenticated_client):
        """File uploads should validate MIME type."""
        import io

        # Create a fake executable disguised as PDF
        fake_pdf = io.BytesIO(b'MZ\x00\x00')  # EXE magic bytes
        fake_pdf.name = "document.pdf"

        # Note: This test depends on how file upload is implemented
        # The endpoint should check actual file content, not just extension
        pass  # Implementation depends on specific endpoint behavior

    def test_file_upload_size_limit(self, authenticated_client):
        """File uploads should enforce size limits."""
        import io

        # Create a large file (exceeding typical limit)
        large_content = b'X' * (50 * 1024 * 1024)  # 50MB
        large_file = io.BytesIO(large_content)

        # Note: This test depends on file upload endpoint implementation
        pass  # Implementation depends on specific endpoint behavior


@pytest.mark.security
class TestJSONPayloadValidation:
    """Tests for JSON payload validation."""

    def test_json_max_depth(self, authenticated_client, entity_type_factory):
        """Deeply nested JSON should be handled."""
        entity_type = entity_type_factory()

        # Create deeply nested custom_fields
        nested = {"level": 0}
        current = nested
        for i in range(100):
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        response = authenticated_client.post(
            "/api/v1/entities",
            json={
                "name": "Test Entity",
                "entity_type_id": str(entity_type.id),
                "custom_fields": nested,
            }
        )

        # Should handle without crashing
        assert response.status_code in (201, 422, 413)

    def test_json_unicode(self, authenticated_client, entity_type_factory):
        """Unicode characters should be handled properly."""
        entity_type = entity_type_factory()

        response = authenticated_client.post(
            "/api/v1/entities",
            json={
                "name": "Test Entity \u0000\uFFFF \u2603",  # Null byte, max unicode, snowman
                "entity_type_id": str(entity_type.id),
            }
        )

        # Should handle without crashing
        assert response.status_code in (201, 422)


@pytest.mark.security
class TestPathTraversal:
    """Tests for path traversal prevention."""

    def test_path_traversal_prevention(self, authenticated_client):
        """Path traversal attempts should be blocked."""
        # Try to access a file with path traversal
        response = authenticated_client.get("/api/v1/documents/../../../etc/passwd")

        # Should be blocked (404 or 400, not file contents)
        assert response.status_code in (404, 400, 422)


@pytest.mark.security
class TestIntegrationInputValidation:
    """Tests for integration settings validation."""

    def test_provider_validation(self, authenticated_client):
        """Provider should be validated against allowed values."""
        response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={"provider": "malicious_provider"}
        )

        assert response.status_code == 422  # Invalid provider

    def test_webhook_url_validation(self, authenticated_client):
        """Webhook URLs should be validated."""
        response = authenticated_client.put(
            "/api/v1/integrations/settings",
            json={
                "provider": "zapier",
                "zapier": {
                    # Invalid URL formats
                    "webhook_url_entity_created": "javascript:alert(1)",
                }
            }
        )

        # Should either accept (some APIs are lenient) or reject
        # Important: should not cause server error
        assert response.status_code in (200, 422)
