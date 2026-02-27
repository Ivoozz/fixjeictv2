import logging
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from .config import settings
from .models import Ticket

logger = logging.getLogger(__name__)


class CloudflareService:
    """Cloudflare API service for email routing"""

    def __init__(self):
        self.api_key = settings.CLOUDFLARE_API_KEY
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.zone_id = settings.CLOUDFLARE_ZONE_ID
        self.email_domain = settings.EMAIL_DOMAIN
        self.base_url = "https://api.cloudflare.com/client/v4"

    def _is_configured(self) -> bool:
        """Check if Cloudflare service is properly configured"""
        return all([self.api_key, self.account_id, self.zone_id, self.email_domain])

    def _get_headers(self) -> dict:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_email_forwarding(self, local_part: str, destination_email: str) -> Optional[str]:
        """Create an email forwarding rule via Cloudflare Email Routing"""
        if not self._is_configured():
            logger.warning("Cloudflare not configured - skipping email forwarding")
            return None

        rule_name = f"ticket-{local_part}"

        rule_data = {
            "name": rule_name,
            "enabled": True,
            "matchers": [
                {
                    "field": "to",
                    "type": "literal",
                    "value": f"{local_part}@{self.email_domain}",
                }
            ],
            "actions": [
                {
                    "type": "forward",
                    "value": [destination_email],
                }
            ],
        }

        try:
            url = f"{self.base_url}/accounts/{self.account_id}/email/routing/rules"
            response = httpx.post(url, headers=self._get_headers(), json=rule_data)
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                logger.info(f"Created email forwarding: {local_part}@{self.email_domain} -> {destination_email}")
                return result["result"]["id"]
            return None
        except Exception as e:
            logger.error(f"Failed to create email forwarding: {e}")
            return None

    def delete_email_forwarding(self, rule_id: str) -> bool:
        """Delete an email forwarding rule"""
        if not self._is_configured():
            return False

        try:
            url = f"{self.base_url}/accounts/{self.account_id}/email/routing/rules/{rule_id}"
            response = httpx.delete(url, headers=self._get_headers())
            response.raise_for_status()
            logger.info(f"Deleted email forwarding rule: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete email forwarding: {e}")
            return False

    def list_email_forwardings(self) -> List[dict]:
        """List all email forwarding rules"""
        if not self._is_configured():
            return []

        try:
            url = f"{self.base_url}/accounts/{self.account_id}/email/routing/rules"
            response = httpx.get(url, headers=self._get_headers())
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                return result["result"]
            return []
        except Exception as e:
            logger.error(f"Failed to list email forwardings: {e}")
            return []

    def create_ticket_email(self, ticket_id: int, client_email: str) -> Optional[str]:
        """Create email forwarding for a specific ticket"""
        local_part = f"ticket-{ticket_id}"
        return self.create_email_forwarding(local_part, client_email)

    def delete_ticket_email(self, rule_id: str) -> bool:
        """Delete ticket email forwarding"""
        return self.delete_email_forwarding(rule_id)


# Global cloudflare service instance
cloudflare_service = CloudflareService()
