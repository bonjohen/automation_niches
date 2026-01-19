"""Abstract CRM connector and service layer."""
from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

from .encryption import decrypt_secret

logger = logging.getLogger(__name__)


class CRMConnector(ABC):
    """
    Abstract base class for CRM connectors.

    Implementations should handle authentication and API communication
    with specific CRM providers (HubSpot, Salesforce, etc.).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'hubspot', 'zapier')."""
        pass

    @abstractmethod
    def test_connection(self) -> dict:
        """
        Test the CRM connection.

        Returns:
            dict with keys:
                - success: bool
                - message: str (success message or error description)
        """
        pass

    @abstractmethod
    def get_contacts(self, limit: int = 100, after: Optional[str] = None) -> dict:
        """
        Fetch contacts/companies from CRM.

        Args:
            limit: Maximum number of records to fetch
            after: Pagination cursor for next page

        Returns:
            dict with keys:
                - success: bool
                - results: list of contact dicts
                - has_more: bool
                - next_cursor: Optional[str]
                - error: Optional[str]
        """
        pass

    @abstractmethod
    def get_contact(self, external_id: str) -> dict:
        """
        Get a single contact by CRM ID.

        Returns:
            dict with keys:
                - success: bool
                - data: Optional[dict] (contact data)
                - error: Optional[str]
        """
        pass

    @abstractmethod
    def create_contact(self, data: dict) -> dict:
        """
        Create a contact in CRM.

        Args:
            data: Contact properties to create

        Returns:
            dict with keys:
                - success: bool
                - external_id: Optional[str] (CRM record ID)
                - error: Optional[str]
        """
        pass

    @abstractmethod
    def update_contact(self, external_id: str, data: dict) -> dict:
        """
        Update a contact in CRM.

        Args:
            external_id: CRM record ID
            data: Contact properties to update

        Returns:
            dict with keys:
                - success: bool
                - error: Optional[str]
        """
        pass

    @abstractmethod
    def push_compliance_status(self, external_id: str, status: dict) -> dict:
        """
        Push compliance status to CRM custom fields.

        Args:
            external_id: CRM record ID
            status: Compliance status data (status, expiry, etc.)

        Returns:
            dict with keys:
                - success: bool
                - error: Optional[str]
        """
        pass


class CRMService:
    """
    CRM service that manages connectors per account.

    Reads CRM configuration from account.settings["crm"] and
    instantiates the appropriate connector.
    """

    def __init__(self, account: Any, field_mapping: Optional[dict] = None):
        """
        Initialize CRM service for an account.

        Args:
            account: Account model instance
            field_mapping: Optional field mapping override
        """
        self.account = account
        self.config = (account.settings or {}).get("crm", {})
        self.enabled = self.config.get("enabled", False)
        self.provider = self.config.get("provider")
        self.field_mapping = field_mapping or self.config.get("field_mapping", {})
        self._connector: Optional[CRMConnector] = None

    @property
    def connector(self) -> Optional[CRMConnector]:
        """Get the configured CRM connector, or None if not configured."""
        if self._connector is not None:
            return self._connector

        if not self.enabled or not self.provider:
            return None

        self._connector = self._create_connector()
        return self._connector

    def _create_connector(self) -> Optional[CRMConnector]:
        """Create the appropriate connector based on provider config."""
        if self.provider == "hubspot":
            from .hubspot import HubSpotConnector

            hubspot_config = self.config.get("hubspot", {})
            api_key = decrypt_secret(hubspot_config.get("api_key", ""))
            oauth_token = decrypt_secret(hubspot_config.get("oauth_token", ""))

            if not api_key and not oauth_token:
                logger.warning(f"HubSpot configured but no credentials for account {self.account.id}")
                return None

            return HubSpotConnector(
                api_key=api_key,
                oauth_token=oauth_token,
                portal_id=hubspot_config.get("portal_id"),
                object_type=hubspot_config.get("object_type", "companies"),
            )

        elif self.provider == "zapier":
            from .zapier import ZapierWebhookConnector

            zapier_config = self.config.get("zapier", {})
            webhook_secret = decrypt_secret(zapier_config.get("webhook_secret", ""))

            return ZapierWebhookConnector(
                webhook_url_entity_created=zapier_config.get("webhook_url_entity_created"),
                webhook_url_entity_updated=zapier_config.get("webhook_url_entity_updated"),
                webhook_url_compliance_changed=zapier_config.get("webhook_url_compliance_changed"),
                webhook_secret=webhook_secret,
            )

        else:
            logger.warning(f"Unknown CRM provider: {self.provider}")
            return None

    def is_configured(self) -> bool:
        """Check if CRM is properly configured and ready to use."""
        return self.enabled and self.connector is not None

    def map_entity_to_crm(self, entity: Any) -> dict:
        """
        Map an Entity to CRM contact fields using configured field mapping.

        Args:
            entity: Entity model instance

        Returns:
            dict of CRM field names to values
        """
        result = {}

        # Default mappings if none configured
        default_mapping = {
            "name": "name",
            "email": "email",
            "phone": "phone",
            "address": "address",
        }

        mapping = self.field_mapping or default_mapping

        for entity_field, crm_field in mapping.items():
            value = self._get_entity_field(entity, entity_field)
            if value is not None:
                result[crm_field] = value

        return result

    def _get_entity_field(self, entity: Any, field_path: str) -> Any:
        """
        Get a field value from an entity, supporting dot notation for nested fields.

        Examples:
            "name" -> entity.name
            "custom_fields.vendor_type" -> entity.custom_fields["vendor_type"]
        """
        parts = field_path.split(".")
        value = entity

        for part in parts:
            if value is None:
                return None

            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value

    def sync_entity(self, entity: Any, operation: str = "auto") -> dict:
        """
        Sync an entity to the CRM.

        Args:
            entity: Entity model instance
            operation: "create", "update", or "auto" (detect based on external_id)

        Returns:
            dict with sync result
        """
        if not self.is_configured():
            return {"success": False, "error": "CRM not configured"}

        connector = self.connector
        data = self.map_entity_to_crm(entity)

        # Determine operation
        if operation == "auto":
            operation = "update" if entity.external_id else "create"

        if operation == "create":
            result = connector.create_contact(data)
            if result.get("success") and result.get("external_id"):
                # Return the external_id for the caller to update the entity
                return {
                    "success": True,
                    "operation": "create",
                    "external_id": result["external_id"],
                }
            return {"success": False, "operation": "create", "error": result.get("error")}

        elif operation == "update":
            if not entity.external_id:
                return {"success": False, "error": "No external_id for update"}

            result = connector.update_contact(entity.external_id, data)
            return {
                "success": result.get("success", False),
                "operation": "update",
                "error": result.get("error"),
            }

        return {"success": False, "error": f"Unknown operation: {operation}"}

    def push_entity_compliance(self, entity: Any) -> dict:
        """
        Push compliance status for an entity to the CRM.

        Args:
            entity: Entity model instance with requirements relationship

        Returns:
            dict with push result
        """
        if not self.is_configured():
            return {"success": False, "error": "CRM not configured"}

        if not entity.external_id:
            return {"success": False, "error": "Entity has no external_id"}

        # Calculate compliance status from requirements
        status = self._calculate_compliance_status(entity)

        result = self.connector.push_compliance_status(entity.external_id, status)
        return result

    def _calculate_compliance_status(self, entity: Any) -> dict:
        """Calculate compliance status from entity requirements."""
        from datetime import datetime, date

        requirements = getattr(entity, "requirements", []) or []

        if not requirements:
            return {
                "compliance_status": "no_requirements",
                "compliance_expiry": None,
                "compliance_last_updated": datetime.utcnow().isoformat(),
            }

        # Find earliest expiry and overall status
        statuses = []
        earliest_expiry = None

        for req in requirements:
            statuses.append(req.status if hasattr(req, "status") else "unknown")
            due_date = getattr(req, "due_date", None)
            if due_date:
                if isinstance(due_date, datetime):
                    due_date = due_date.date()
                if earliest_expiry is None or due_date < earliest_expiry:
                    earliest_expiry = due_date

        # Determine overall status
        if "expired" in statuses:
            overall_status = "non_compliant"
        elif "expiring_soon" in statuses:
            overall_status = "expiring_soon"
        elif all(s in ("compliant", "completed") for s in statuses):
            overall_status = "compliant"
        else:
            overall_status = "pending"

        return {
            "compliance_status": overall_status,
            "compliance_expiry": earliest_expiry.isoformat() if earliest_expiry else None,
            "compliance_last_updated": datetime.utcnow().isoformat(),
        }


def get_crm_service(account: Any) -> CRMService:
    """
    Get a CRM service instance for an account.

    Args:
        account: Account model instance

    Returns:
        CRMService instance
    """
    return CRMService(account)
