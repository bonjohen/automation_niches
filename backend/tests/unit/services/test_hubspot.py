"""Unit tests for HubSpot CRM connector."""
import pytest
import responses
from unittest.mock import patch


class TestHubSpotConnector:
    """Tests for the HubSpot CRM connector."""

    HUBSPOT_BASE_URL = "https://api.hubapi.com"

    @pytest.fixture
    def connector(self):
        """Create a connector with API key."""
        from app.services.crm.hubspot import HubSpotConnector

        return HubSpotConnector(
            api_key="test-api-key",
            portal_id="12345678",
            object_type="companies",
        )

    @pytest.fixture
    def connector_oauth(self):
        """Create a connector with OAuth token."""
        from app.services.crm.hubspot import HubSpotConnector

        return HubSpotConnector(
            oauth_token="oauth-access-token",
            portal_id="12345678",
            object_type="contacts",
        )

    def test_init_with_api_key(self):
        """Constructor should accept API key."""
        from app.services.crm.hubspot import HubSpotConnector

        connector = HubSpotConnector(api_key="my-key")

        assert connector.api_key == "my-key"
        assert connector.oauth_token is None

    def test_init_with_oauth_token(self):
        """Constructor should accept OAuth token."""
        from app.services.crm.hubspot import HubSpotConnector

        connector = HubSpotConnector(oauth_token="my-token")

        assert connector.oauth_token == "my-token"
        assert connector.api_key is None

    def test_init_requires_credential(self):
        """Constructor should raise without credentials."""
        from app.services.crm.hubspot import HubSpotConnector

        with pytest.raises(ValueError, match="api_key or oauth_token"):
            HubSpotConnector()

    def test_provider_name(self, connector):
        """Provider name should return 'hubspot'."""
        assert connector.provider_name == "hubspot"

    def test_get_headers_with_api_key(self, connector):
        """Headers should include Bearer token from API key."""
        headers = connector._get_headers()

        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Content-Type"] == "application/json"

    def test_get_headers_with_oauth(self, connector_oauth):
        """Headers should include Bearer token from OAuth."""
        headers = connector_oauth._get_headers()

        assert headers["Authorization"] == "Bearer oauth-access-token"

    def test_get_object_url_companies(self, connector):
        """Object URL should be correct for companies."""
        url = connector._get_object_url()

        assert url == f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies"

    def test_get_object_url_contacts(self, connector_oauth):
        """Object URL should be correct for contacts."""
        url = connector_oauth._get_object_url()

        assert url == f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/contacts"

    def test_get_object_url_with_id(self, connector):
        """Object URL should include ID when provided."""
        url = connector._get_object_url("12345")

        assert url == f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies/12345"

    @responses.activate
    def test_test_connection_success(self, connector):
        """Successful connection should return success=True."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/account-info/v3/details",
            json={"portalId": 12345678, "accountType": "STANDARD"},
            status=200,
        )

        result = connector.test_connection()

        assert result["success"] is True
        assert "12345678" in result["message"]
        assert result["portal_id"] == 12345678

    @responses.activate
    def test_test_connection_401(self, connector):
        """Unauthorized should return success=False."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/account-info/v3/details",
            json={"status": "error", "message": "Invalid API key"},
            status=401,
        )

        result = connector.test_connection()

        assert result["success"] is False
        assert "401" in result["message"]

    @responses.activate
    def test_test_connection_timeout(self, connector):
        """Timeout should be handled gracefully."""
        from requests.exceptions import Timeout

        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/account-info/v3/details",
            body=Timeout("Connection timed out"),
        )

        result = connector.test_connection()

        assert result["success"] is False
        assert "timed out" in result["message"]

    @responses.activate
    def test_get_contacts_success(self, connector):
        """get_contacts should parse HubSpot response correctly."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies",
            json={
                "results": [
                    {
                        "id": "123",
                        "properties": {
                            "name": "Test Company",
                            "domain": "test.com",
                            "phone": "(555) 123-4567",
                        }
                    },
                    {
                        "id": "456",
                        "properties": {
                            "name": "Another Company",
                            "domain": "another.com",
                        }
                    }
                ],
                "paging": {}
            },
            status=200,
        )

        result = connector.get_contacts(limit=50)

        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["external_id"] == "123"
        assert result["results"][0]["name"] == "Test Company"
        assert result["has_more"] is False

    @responses.activate
    def test_get_contacts_pagination(self, connector):
        """get_contacts should handle pagination correctly."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies",
            json={
                "results": [{"id": "1", "properties": {"name": "Company 1"}}],
                "paging": {"next": {"after": "cursor123"}}
            },
            status=200,
        )

        result = connector.get_contacts(limit=1)

        assert result["success"] is True
        assert result["has_more"] is True
        assert result["next_cursor"] == "cursor123"

    @responses.activate
    def test_get_contacts_with_cursor(self, connector):
        """get_contacts should pass cursor in params."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies",
            json={"results": [], "paging": {}},
            status=200,
        )

        connector.get_contacts(after="cursor123")

        # Check the request params
        request = responses.calls[0].request
        assert "after=cursor123" in request.url

    @responses.activate
    def test_get_contact_success(self, connector):
        """get_contact should fetch a single company."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies/123",
            json={
                "id": "123",
                "properties": {
                    "name": "Test Company",
                    "domain": "test.com",
                }
            },
            status=200,
        )

        result = connector.get_contact("123")

        assert result["success"] is True
        assert result["data"]["external_id"] == "123"
        assert result["data"]["name"] == "Test Company"

    @responses.activate
    def test_get_contact_not_found(self, connector):
        """get_contact should handle 404."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies/999",
            json={"status": "error"},
            status=404,
        )

        result = connector.get_contact("999")

        assert result["success"] is False
        assert result["data"] is None
        assert "Not found" in result["error"]

    @responses.activate
    def test_create_contact_success(self, connector):
        """create_contact should return external_id on 201."""
        responses.add(
            responses.POST,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies",
            json={
                "id": "new-123",
                "properties": {"name": "New Company"}
            },
            status=201,
        )

        result = connector.create_contact({
            "name": "New Company",
            "email": "info@new.com",
        })

        assert result["success"] is True
        assert result["external_id"] == "new-123"

    @responses.activate
    def test_create_contact_failure(self, connector):
        """create_contact should handle errors."""
        responses.add(
            responses.POST,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies",
            json={"status": "error", "message": "Invalid property"},
            status=400,
        )

        result = connector.create_contact({"name": "Test"})

        assert result["success"] is False
        assert "400" in result["error"]

    @responses.activate
    def test_update_contact_success(self, connector):
        """update_contact should PATCH correctly."""
        responses.add(
            responses.PATCH,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies/123",
            json={"id": "123", "properties": {"name": "Updated"}},
            status=200,
        )

        result = connector.update_contact("123", {"name": "Updated Company"})

        assert result["success"] is True

    @responses.activate
    def test_update_contact_request_body(self, connector):
        """update_contact should send properties in correct format."""
        import json

        responses.add(
            responses.PATCH,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies/123",
            json={"id": "123"},
            status=200,
        )

        connector.update_contact("123", {"name": "Test", "phone": "(555) 000-0000"})

        request_body = json.loads(responses.calls[0].request.body)
        assert "properties" in request_body
        assert request_body["properties"]["name"] == "Test"
        assert request_body["properties"]["phone"] == "(555) 000-0000"

    @responses.activate
    def test_push_compliance_status(self, connector):
        """push_compliance_status should update custom properties."""
        import json

        responses.add(
            responses.PATCH,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies/123",
            json={"id": "123"},
            status=200,
        )

        result = connector.push_compliance_status("123", {
            "compliance_status": "compliant",
            "compliance_expiry": "2025-01-01",
            "compliance_last_updated": "2024-01-15T10:00:00Z",
        })

        assert result["success"] is True

        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["properties"]["compliance_status"] == "compliant"
        assert request_body["properties"]["compliance_expiry"] == "2025-01-01"

    @responses.activate
    def test_push_compliance_status_property_not_exists(self, connector):
        """push_compliance_status should handle missing custom properties."""
        responses.add(
            responses.PATCH,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/objects/companies/123",
            json={
                "status": "error",
                "message": "PROPERTY_DOESNT_EXIST",
                "correlationId": "xxx"
            },
            status=400,
        )

        result = connector.push_compliance_status("123", {
            "compliance_status": "compliant",
        })

        assert result["success"] is False
        assert "not configured" in result["error"]

    def test_normalize_contact_companies(self, connector):
        """_normalize_contact should normalize company response."""
        hubspot_data = {
            "id": "123",
            "properties": {
                "name": "Test Company",
                "domain": "test.com",
                "phone": "(555) 123-4567",
                "industry": "Technology",
                "compliance_status": "compliant",
            }
        }

        result = connector._normalize_contact(hubspot_data)

        assert result["external_id"] == "123"
        assert result["name"] == "Test Company"
        assert result["domain"] == "test.com"
        assert result["industry"] == "Technology"
        assert result["compliance_status"] == "compliant"
        assert "raw" in result

    def test_normalize_contact_contacts(self, connector_oauth):
        """_normalize_contact should normalize contact response (with first/last name)."""
        hubspot_data = {
            "id": "456",
            "properties": {
                "firstname": "John",
                "lastname": "Doe",
                "email": "john@example.com",
                "phone": "(555) 987-6543",
            }
        }

        result = connector_oauth._normalize_contact(hubspot_data)

        assert result["external_id"] == "456"
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"

    def test_map_to_hubspot_properties_companies(self, connector):
        """_map_to_hubspot_properties should map fields for companies."""
        data = {
            "name": "Test Company",
            "email": "info@test.com",
            "phone": "(555) 123-4567",
            "custom_field": "custom_value",
        }

        result = connector._map_to_hubspot_properties(data)

        assert result["name"] == "Test Company"
        assert result["phone"] == "(555) 123-4567"
        assert result["custom_field"] == "custom_value"  # Pass-through

    def test_map_to_hubspot_properties_contacts(self, connector_oauth):
        """_map_to_hubspot_properties should map 'name' to 'lastname' for contacts."""
        data = {
            "name": "Doe",
            "email": "john@example.com",
        }

        result = connector_oauth._map_to_hubspot_properties(data)

        assert result["lastname"] == "Doe"
        assert result["email"] == "john@example.com"

    def test_map_to_hubspot_properties_skips_empty(self, connector):
        """_map_to_hubspot_properties should skip empty values."""
        data = {
            "name": "Test",
            "email": "",
            "phone": None,
        }

        result = connector._map_to_hubspot_properties(data)

        assert result["name"] == "Test"
        assert "email" not in result or result.get("email") == ""
        assert "phone" not in result

    def test_get_default_properties_companies(self, connector):
        """Default properties for companies should include expected fields."""
        props = connector._get_default_properties()

        assert "name" in props
        assert "domain" in props
        assert "phone" in props
        assert "compliance_status" in props
        assert "compliance_expiry" in props

    def test_get_default_properties_contacts(self, connector_oauth):
        """Default properties for contacts should include expected fields."""
        props = connector_oauth._get_default_properties()

        assert "firstname" in props
        assert "lastname" in props
        assert "email" in props
        assert "compliance_status" in props

    @responses.activate
    def test_get_properties(self, connector):
        """get_properties should fetch available properties."""
        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/crm/v3/properties/companies",
            json={
                "results": [
                    {"name": "name", "label": "Name", "type": "string", "fieldType": "text"},
                    {"name": "domain", "label": "Domain", "type": "string", "fieldType": "text"},
                ]
            },
            status=200,
        )

        result = connector.get_properties()

        assert result["success"] is True
        assert len(result["properties"]) == 2
        assert result["properties"][0]["name"] == "name"

    @responses.activate
    def test_request_exception_handling(self, connector):
        """Request exceptions should be handled gracefully."""
        from requests.exceptions import ConnectionError

        responses.add(
            responses.GET,
            f"{self.HUBSPOT_BASE_URL}/account-info/v3/details",
            body=ConnectionError("Network error"),
        )

        result = connector.test_connection()

        assert result["success"] is False
        assert "error" in result["message"].lower()
