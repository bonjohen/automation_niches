"""Zapier webhook connector implementation."""
from datetime import datetime
from typing import Optional
import hashlib
import hmac
import json
import logging

import requests

from .base import CRMConnector

logger = logging.getLogger(__name__)


class ZapierWebhookConnector(CRMConnector):
    """
    Zapier webhook connector for CRM integration.

    This connector sends outbound webhooks to Zapier when events occur,
    allowing users to connect to any CRM via Zapier's integrations.

    Inbound webhooks from Zapier are handled by the API endpoint.
    """

    def __init__(
        self,
        webhook_url_entity_created: Optional[str] = None,
        webhook_url_entity_updated: Optional[str] = None,
        webhook_url_compliance_changed: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """
        Initialize Zapier webhook connector.

        Args:
            webhook_url_entity_created: Webhook URL for entity creation events
            webhook_url_entity_updated: Webhook URL for entity update events
            webhook_url_compliance_changed: Webhook URL for compliance status changes
            webhook_secret: Secret for HMAC signature (for webhook validation)
        """
        self.webhook_urls = {
            "entity_created": webhook_url_entity_created,
            "entity_updated": webhook_url_entity_updated,
            "compliance_changed": webhook_url_compliance_changed,
        }
        self.webhook_secret = webhook_secret

    @property
    def provider_name(self) -> str:
        return "zapier"

    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for webhook payload."""
        if not self.webhook_secret:
            return ""

        return hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _send_webhook(
        self,
        event_type: str,
        payload: dict,
        timeout: int = 10,
    ) -> dict:
        """
        Send a webhook to Zapier.

        Args:
            event_type: Type of event (maps to webhook URL)
            payload: Data to send
            timeout: Request timeout in seconds

        Returns:
            dict with success status and any error
        """
        url = self.webhook_urls.get(event_type)

        if not url:
            return {
                "success": False,
                "error": f"No webhook URL configured for event: {event_type}",
            }

        # Build the full payload
        full_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": payload,
        }

        payload_json = json.dumps(full_payload, default=str)

        # Add signature header
        headers = {
            "Content-Type": "application/json",
        }

        if self.webhook_secret:
            headers["X-Webhook-Signature"] = self._generate_signature(payload_json)

        try:
            response = requests.post(
                url,
                data=payload_json,
                headers=headers,
                timeout=timeout,
            )

            # Zapier typically returns 200 or 202
            if response.status_code in (200, 201, 202):
                return {"success": True, "status_code": response.status_code}

            return {
                "success": False,
                "error": f"Webhook failed: {response.status_code} - {response.text[:200]}",
                "status_code": response.status_code,
            }

        except requests.Timeout:
            return {"success": False, "error": "Webhook timed out"}
        except requests.RequestException as e:
            return {"success": False, "error": f"Webhook error: {str(e)}"}

    def test_connection(self) -> dict:
        """
        Test connection by sending a test webhook.

        Sends to the first configured webhook URL.
        """
        # Find first configured webhook
        test_url = None
        test_event = None

        for event, url in self.webhook_urls.items():
            if url:
                test_url = url
                test_event = event
                break

        if not test_url:
            return {
                "success": False,
                "message": "No webhook URLs configured",
            }

        # Send test payload
        test_payload = {
            "test": True,
            "message": "Connection test from SMB Compliance Platform",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        result = self._send_webhook(test_event, test_payload)

        if result.get("success"):
            return {
                "success": True,
                "message": f"Test webhook sent successfully to {test_event} endpoint",
            }

        return {
            "success": False,
            "message": f"Test webhook failed: {result.get('error', 'Unknown error')}",
        }

    def get_contacts(self, limit: int = 100, after: Optional[str] = None) -> dict:
        """
        Zapier doesn't support fetching contacts - this is a push-only connector.
        """
        return {
            "success": False,
            "results": [],
            "error": "Zapier connector is push-only. Use pull sync with direct CRM connection.",
        }

    def get_contact(self, external_id: str) -> dict:
        """
        Zapier doesn't support fetching contacts - this is a push-only connector.
        """
        return {
            "success": False,
            "data": None,
            "error": "Zapier connector is push-only. Use direct CRM connection to fetch contacts.",
        }

    def create_contact(self, data: dict) -> dict:
        """
        Send entity creation webhook to Zapier.

        Note: Zapier doesn't return an external_id since we don't know
        what CRM it will ultimately create the record in.
        """
        result = self._send_webhook("entity_created", data)

        if result.get("success"):
            return {
                "success": True,
                "external_id": None,  # Zapier doesn't give us an ID back
                "note": "Entity sent to Zapier. External ID will be set via webhook callback.",
            }

        return result

    def update_contact(self, external_id: str, data: dict) -> dict:
        """Send entity update webhook to Zapier."""
        payload = {
            "external_id": external_id,
            **data,
        }

        return self._send_webhook("entity_updated", payload)

    def push_compliance_status(self, external_id: str, status: dict) -> dict:
        """Send compliance status change webhook to Zapier."""
        payload = {
            "external_id": external_id,
            **status,
        }

        return self._send_webhook("compliance_changed", payload)

    @staticmethod
    def verify_webhook_signature(
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify an incoming webhook signature.

        Used by the webhook receiver endpoint to validate requests.

        Args:
            payload: Raw request body
            signature: Signature from X-Webhook-Signature header
            secret: Webhook secret for this account

        Returns:
            True if signature is valid
        """
        if not secret or not signature:
            return False

        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
