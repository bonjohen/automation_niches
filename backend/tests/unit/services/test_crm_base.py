"""Unit tests for CRM base service."""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch


class TestCRMService:
    """Tests for the CRM service layer."""

    @pytest.fixture
    def mock_account(self):
        """Create a mock account with CRM settings."""
        account = MagicMock()
        account.id = "acc-123"
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "hubspot",
                "hubspot": {
                    "api_key": "test-api-key",
                    "portal_id": "12345678",
                    "object_type": "companies",
                },
                "field_mapping": {
                    "name": "name",
                    "email": "email",
                    "custom_fields.vendor_type": "vendor_type",
                }
            }
        }
        return account

    @pytest.fixture
    def mock_account_zapier(self):
        """Create a mock account with Zapier settings."""
        account = MagicMock()
        account.id = "acc-456"
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "zapier",
                "zapier": {
                    "webhook_url_entity_created": "https://hooks.zapier.com/test",
                    "webhook_secret": "secret",
                },
            }
        }
        return account

    @pytest.fixture
    def mock_account_disabled(self):
        """Create a mock account with CRM disabled."""
        account = MagicMock()
        account.id = "acc-789"
        account.settings = {
            "crm": {
                "enabled": False,
            }
        }
        return account

    @pytest.fixture
    def mock_entity(self):
        """Create a mock entity."""
        entity = MagicMock()
        entity.id = "ent-123"
        entity.name = "Test Vendor LLC"
        entity.email = "vendor@example.com"
        entity.phone = "(555) 123-4567"
        entity.address = "123 Test St"
        entity.external_id = None
        entity.custom_fields = {"vendor_type": "contractor"}
        return entity

    def test_crm_service_init(self, mock_account):
        """CRM service should read config from account.settings['crm']."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        assert service.enabled is True
        assert service.provider == "hubspot"
        assert service.account == mock_account

    def test_crm_service_not_configured(self, mock_account_disabled):
        """is_configured() should return False when disabled."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account_disabled)

        assert service.is_configured() is False

    @patch('app.services.crm.base.decrypt_secret')
    def test_crm_service_creates_hubspot_connector(self, mock_decrypt, mock_account):
        """Factory should create HubSpotConnector for hubspot provider."""
        mock_decrypt.return_value = "decrypted-api-key"

        from app.services.crm.base import CRMService

        service = CRMService(mock_account)
        connector = service.connector

        assert connector is not None
        assert connector.provider_name == "hubspot"

    @patch('app.services.crm.base.decrypt_secret')
    def test_crm_service_creates_zapier_connector(self, mock_decrypt, mock_account_zapier):
        """Factory should create ZapierWebhookConnector for zapier provider."""
        mock_decrypt.return_value = "decrypted-secret"

        from app.services.crm.base import CRMService

        service = CRMService(mock_account_zapier)
        connector = service.connector

        assert connector is not None
        assert connector.provider_name == "zapier"

    def test_crm_service_unknown_provider(self):
        """Unknown provider should return None connector."""
        from app.services.crm.base import CRMService

        account = MagicMock()
        account.settings = {
            "crm": {
                "enabled": True,
                "provider": "unknown_crm",
            }
        }

        service = CRMService(account)

        assert service.connector is None
        assert service.is_configured() is False

    def test_map_entity_to_crm_default_mapping(self, mock_account, mock_entity):
        """map_entity_to_crm should use default field mapping."""
        from app.services.crm.base import CRMService

        # Remove custom field mapping to test defaults
        mock_account.settings["crm"]["field_mapping"] = None

        service = CRMService(mock_account)
        result = service.map_entity_to_crm(mock_entity)

        assert result["name"] == "Test Vendor LLC"
        assert result["email"] == "vendor@example.com"
        assert result["phone"] == "(555) 123-4567"

    def test_map_entity_to_crm_custom_mapping(self, mock_account, mock_entity):
        """map_entity_to_crm should respect configured field_mapping."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)
        result = service.map_entity_to_crm(mock_entity)

        # Should include custom field from nested path
        assert result["vendor_type"] == "contractor"

    def test_get_entity_field_simple(self, mock_account, mock_entity):
        """_get_entity_field should handle simple attributes."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        result = service._get_entity_field(mock_entity, "name")

        assert result == "Test Vendor LLC"

    def test_get_entity_field_nested(self, mock_account, mock_entity):
        """_get_entity_field should handle dot notation for nested fields."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        result = service._get_entity_field(mock_entity, "custom_fields.vendor_type")

        assert result == "contractor"

    def test_get_entity_field_missing(self, mock_account):
        """_get_entity_field should return None for missing fields."""
        from app.services.crm.base import CRMService

        # Create entity with specific attributes only (not MagicMock)
        class MockEntity:
            id = "ent-123"
            name = "Test Vendor"
            email = "vendor@example.com"
            custom_fields = {}

        service = CRMService(mock_account)
        entity = MockEntity()

        result = service._get_entity_field(entity, "nonexistent_field")

        assert result is None

    @patch('app.services.crm.base.decrypt_secret')
    def test_sync_entity_auto_create(self, mock_decrypt, mock_account, mock_entity):
        """sync_entity should create when no external_id."""
        mock_decrypt.return_value = "api-key"

        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        # Mock the connector
        mock_connector = MagicMock()
        mock_connector.create_contact.return_value = {
            "success": True,
            "external_id": "new-ext-123",
        }
        service._connector = mock_connector

        mock_entity.external_id = None  # No external ID = create

        result = service.sync_entity(mock_entity)

        assert result["success"] is True
        assert result["operation"] == "create"
        assert result["external_id"] == "new-ext-123"
        mock_connector.create_contact.assert_called_once()

    @patch('app.services.crm.base.decrypt_secret')
    def test_sync_entity_auto_update(self, mock_decrypt, mock_account, mock_entity):
        """sync_entity should update when external_id exists."""
        mock_decrypt.return_value = "api-key"

        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        mock_connector = MagicMock()
        mock_connector.update_contact.return_value = {"success": True}
        service._connector = mock_connector

        mock_entity.external_id = "existing-123"  # Has external ID = update

        result = service.sync_entity(mock_entity)

        assert result["success"] is True
        assert result["operation"] == "update"
        mock_connector.update_contact.assert_called_once()

    def test_sync_entity_not_configured(self, mock_account_disabled, mock_entity):
        """sync_entity should return error when CRM not configured."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account_disabled)

        result = service.sync_entity(mock_entity)

        assert result["success"] is False
        assert "not configured" in result["error"]

    def test_calculate_compliance_status_no_requirements(self, mock_account, mock_entity):
        """_calculate_compliance_status should return no_requirements when empty."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)
        mock_entity.requirements = []

        result = service._calculate_compliance_status(mock_entity)

        assert result["compliance_status"] == "no_requirements"
        assert result["compliance_expiry"] is None

    def test_calculate_compliance_status_expired(self, mock_account, mock_entity):
        """_calculate_compliance_status should return non_compliant when expired."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        # Create mock requirement with expired status
        mock_req = MagicMock()
        mock_req.status = "expired"
        mock_req.due_date = date.today() - timedelta(days=10)
        mock_entity.requirements = [mock_req]

        result = service._calculate_compliance_status(mock_entity)

        assert result["compliance_status"] == "non_compliant"

    def test_calculate_compliance_status_expiring_soon(self, mock_account, mock_entity):
        """_calculate_compliance_status should return expiring_soon."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        mock_req = MagicMock()
        mock_req.status = "expiring_soon"
        mock_req.due_date = date.today() + timedelta(days=5)
        mock_entity.requirements = [mock_req]

        result = service._calculate_compliance_status(mock_entity)

        assert result["compliance_status"] == "expiring_soon"

    def test_calculate_compliance_status_compliant(self, mock_account, mock_entity):
        """_calculate_compliance_status should return compliant when all good."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        mock_req1 = MagicMock()
        mock_req1.status = "compliant"
        mock_req1.due_date = date.today() + timedelta(days=60)

        mock_req2 = MagicMock()
        mock_req2.status = "completed"
        mock_req2.due_date = date.today() + timedelta(days=90)

        mock_entity.requirements = [mock_req1, mock_req2]

        result = service._calculate_compliance_status(mock_entity)

        assert result["compliance_status"] == "compliant"

    def test_calculate_compliance_status_earliest_expiry(self, mock_account, mock_entity):
        """_calculate_compliance_status should use earliest expiry date."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        earliest_date = date.today() + timedelta(days=30)
        later_date = date.today() + timedelta(days=60)

        mock_req1 = MagicMock()
        mock_req1.status = "compliant"
        mock_req1.due_date = later_date

        mock_req2 = MagicMock()
        mock_req2.status = "compliant"
        mock_req2.due_date = earliest_date

        mock_entity.requirements = [mock_req1, mock_req2]

        result = service._calculate_compliance_status(mock_entity)

        assert result["compliance_expiry"] == earliest_date.isoformat()

    @patch('app.services.crm.base.decrypt_secret')
    def test_push_entity_compliance(self, mock_decrypt, mock_account, mock_entity):
        """push_entity_compliance should calculate and push status."""
        mock_decrypt.return_value = "api-key"

        from app.services.crm.base import CRMService

        service = CRMService(mock_account)

        mock_connector = MagicMock()
        mock_connector.push_compliance_status.return_value = {"success": True}
        service._connector = mock_connector

        mock_entity.external_id = "ext-123"
        mock_entity.requirements = []

        result = service.push_entity_compliance(mock_entity)

        assert result["success"] is True
        mock_connector.push_compliance_status.assert_called_once()

    def test_push_entity_compliance_no_external_id(self, mock_account, mock_entity):
        """push_entity_compliance should fail without external_id."""
        from app.services.crm.base import CRMService

        service = CRMService(mock_account)
        mock_entity.external_id = None

        # Need to mock connector to pass is_configured check
        service._connector = MagicMock()

        result = service.push_entity_compliance(mock_entity)

        assert result["success"] is False
        assert "no external_id" in result["error"]


class TestGetCRMService:
    """Tests for the get_crm_service helper function."""

    def test_get_crm_service_returns_service(self):
        """get_crm_service should return CRMService instance."""
        from app.services.crm.base import get_crm_service

        account = MagicMock()
        account.settings = {}

        service = get_crm_service(account)

        assert service is not None
        assert service.account == account
