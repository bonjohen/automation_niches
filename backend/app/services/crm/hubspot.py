"""HubSpot CRM connector implementation."""
from typing import Optional
import logging

import requests

from .base import CRMConnector

logger = logging.getLogger(__name__)


class HubSpotConnector(CRMConnector):
    """
    HubSpot CRM connector using HubSpot API v3.

    Supports both API key and OAuth token authentication.
    Can work with either Companies or Contacts objects.
    """

    BASE_URL = "https://api.hubapi.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        portal_id: Optional[str] = None,
        object_type: str = "companies",
    ):
        """
        Initialize HubSpot connector.

        Args:
            api_key: HubSpot API key (private app token)
            oauth_token: OAuth access token (alternative to API key)
            portal_id: HubSpot portal/account ID
            object_type: Object type to sync with ("companies" or "contacts")
        """
        self.api_key = api_key
        self.oauth_token = oauth_token
        self.portal_id = portal_id
        self.object_type = object_type

        if not api_key and not oauth_token:
            raise ValueError("Either api_key or oauth_token must be provided")

    @property
    def provider_name(self) -> str:
        return "hubspot"

    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        token = self.oauth_token or self.api_key
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get_object_url(self, object_id: Optional[str] = None) -> str:
        """Get the API URL for the configured object type."""
        base = f"{self.BASE_URL}/crm/v3/objects/{self.object_type}"
        if object_id:
            return f"{base}/{object_id}"
        return base

    def test_connection(self) -> dict:
        """Test connection by fetching account info."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/account-info/v3/details",
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": f"Connected to HubSpot portal: {data.get('portalId', 'unknown')}",
                    "portal_id": data.get("portalId"),
                }

            return {
                "success": False,
                "message": f"Connection failed: {response.status_code} - {response.text}",
            }

        except requests.Timeout:
            return {"success": False, "message": "Connection timed out"}
        except requests.RequestException as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}

    def get_contacts(self, limit: int = 100, after: Optional[str] = None) -> dict:
        """Fetch companies/contacts from HubSpot."""
        try:
            # Default properties to fetch
            properties = self._get_default_properties()

            params = {
                "limit": min(limit, 100),  # HubSpot max is 100
                "properties": ",".join(properties),
            }

            if after:
                params["after"] = after

            response = requests.get(
                self._get_object_url(),
                headers=self._get_headers(),
                params=params,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                paging = data.get("paging", {})
                next_page = paging.get("next", {})

                return {
                    "success": True,
                    "results": [self._normalize_contact(r) for r in results],
                    "has_more": bool(next_page),
                    "next_cursor": next_page.get("after"),
                }

            return {
                "success": False,
                "results": [],
                "error": f"Failed to fetch: {response.status_code} - {response.text}",
            }

        except requests.RequestException as e:
            return {"success": False, "results": [], "error": str(e)}

    def get_contact(self, external_id: str) -> dict:
        """Get a single company/contact by HubSpot ID."""
        try:
            properties = self._get_default_properties()

            response = requests.get(
                self._get_object_url(external_id),
                headers=self._get_headers(),
                params={"properties": ",".join(properties)},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": self._normalize_contact(data),
                }

            if response.status_code == 404:
                return {"success": False, "data": None, "error": "Not found"}

            return {
                "success": False,
                "data": None,
                "error": f"Failed: {response.status_code} - {response.text}",
            }

        except requests.RequestException as e:
            return {"success": False, "data": None, "error": str(e)}

    def create_contact(self, data: dict) -> dict:
        """Create a company/contact in HubSpot."""
        try:
            # Map our field names to HubSpot property names
            properties = self._map_to_hubspot_properties(data)

            response = requests.post(
                self._get_object_url(),
                headers=self._get_headers(),
                json={"properties": properties},
                timeout=10,
            )

            if response.status_code in (200, 201):
                result = response.json()
                return {
                    "success": True,
                    "external_id": result.get("id"),
                }

            return {
                "success": False,
                "error": f"Failed to create: {response.status_code} - {response.text}",
            }

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def update_contact(self, external_id: str, data: dict) -> dict:
        """Update a company/contact in HubSpot."""
        try:
            properties = self._map_to_hubspot_properties(data)

            response = requests.patch(
                self._get_object_url(external_id),
                headers=self._get_headers(),
                json={"properties": properties},
                timeout=10,
            )

            if response.status_code == 200:
                return {"success": True}

            return {
                "success": False,
                "error": f"Failed to update: {response.status_code} - {response.text}",
            }

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def push_compliance_status(self, external_id: str, status: dict) -> dict:
        """
        Push compliance status to HubSpot custom properties.

        Note: This requires custom properties to be created in HubSpot:
        - compliance_status (string)
        - compliance_expiry (date)
        - compliance_last_updated (datetime)
        """
        try:
            # Map compliance fields to HubSpot custom properties
            properties = {
                "compliance_status": status.get("compliance_status", ""),
                "compliance_expiry": status.get("compliance_expiry", ""),
                "compliance_last_updated": status.get("compliance_last_updated", ""),
            }

            # Remove empty values
            properties = {k: v for k, v in properties.items() if v}

            response = requests.patch(
                self._get_object_url(external_id),
                headers=self._get_headers(),
                json={"properties": properties},
                timeout=10,
            )

            if response.status_code == 200:
                return {"success": True}

            # If properties don't exist, log warning but don't fail
            if response.status_code == 400 and "PROPERTY_DOESNT_EXIST" in response.text:
                logger.warning(
                    f"HubSpot compliance properties not configured. "
                    f"Create custom properties: compliance_status, compliance_expiry, compliance_last_updated"
                )
                return {
                    "success": False,
                    "error": "Compliance properties not configured in HubSpot",
                }

            return {
                "success": False,
                "error": f"Failed to push status: {response.status_code} - {response.text}",
            }

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_properties(self) -> dict:
        """Get available properties for the configured object type."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/crm/v3/properties/{self.object_type}",
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                properties = [
                    {
                        "name": p.get("name"),
                        "label": p.get("label"),
                        "type": p.get("type"),
                        "fieldType": p.get("fieldType"),
                    }
                    for p in data.get("results", [])
                ]
                return {"success": True, "properties": properties}

            return {
                "success": False,
                "properties": [],
                "error": f"Failed: {response.status_code}",
            }

        except requests.RequestException as e:
            return {"success": False, "properties": [], "error": str(e)}

    def _get_default_properties(self) -> list[str]:
        """Get default properties to fetch based on object type."""
        if self.object_type == "companies":
            return [
                "name",
                "domain",
                "phone",
                "address",
                "city",
                "state",
                "zip",
                "country",
                "industry",
                "numberofemployees",
                "annualrevenue",
                "compliance_status",
                "compliance_expiry",
            ]
        else:  # contacts
            return [
                "firstname",
                "lastname",
                "email",
                "phone",
                "company",
                "jobtitle",
                "address",
                "city",
                "state",
                "zip",
                "compliance_status",
                "compliance_expiry",
            ]

    def _map_to_hubspot_properties(self, data: dict) -> dict:
        """Map our standard field names to HubSpot property names."""
        # Direct mapping for most fields
        result = {}

        if self.object_type == "companies":
            mapping = {
                "name": "name",
                "email": "email",  # Companies don't have email, but we try
                "phone": "phone",
                "address": "address",
                "domain": "domain",
            }
        else:
            mapping = {
                "name": "lastname",  # For contacts, use lastname
                "email": "email",
                "phone": "phone",
                "address": "address",
            }

        for our_field, hubspot_field in mapping.items():
            if our_field in data and data[our_field]:
                result[hubspot_field] = data[our_field]

        # Pass through any fields not in our mapping (for custom properties)
        for key, value in data.items():
            if key not in mapping and value:
                result[key] = value

        return result

    def _normalize_contact(self, hubspot_data: dict) -> dict:
        """Normalize HubSpot response to standard format."""
        properties = hubspot_data.get("properties", {})

        if self.object_type == "companies":
            return {
                "external_id": hubspot_data.get("id"),
                "name": properties.get("name", ""),
                "email": properties.get("email", ""),
                "phone": properties.get("phone", ""),
                "address": properties.get("address", ""),
                "domain": properties.get("domain", ""),
                "industry": properties.get("industry", ""),
                "compliance_status": properties.get("compliance_status", ""),
                "compliance_expiry": properties.get("compliance_expiry", ""),
                "raw": properties,
            }
        else:
            return {
                "external_id": hubspot_data.get("id"),
                "name": f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
                "email": properties.get("email", ""),
                "phone": properties.get("phone", ""),
                "address": properties.get("address", ""),
                "company": properties.get("company", ""),
                "compliance_status": properties.get("compliance_status", ""),
                "compliance_expiry": properties.get("compliance_expiry", ""),
                "raw": properties,
            }
