import os
from flask import current_app


class CloudflareService:
    def __init__(self):
        self.api_key = os.environ.get('CLOUDFLARE_API_KEY')
        self.account_id = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
        self.zone_id = os.environ.get('CLOUDFLARE_ZONE_ID')
        self.email_domain = os.environ.get('EMAIL_DOMAIN')

    def _is_configured(self):
        return all([self.api_key, self.account_id, self.zone_id, self.email_domain])

    def create_email_forwarding(self, local_part, destination_email):
        """Create an email forwarding rule via Cloudflare Email Routing"""
        if not self._is_configured():
            current_app.logger.warning('Cloudflare not configured - skipping email forwarding')
            return None

        import requests

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/email/routing/rules"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        rule_name = f"ticket-{local_part}"

        rule_data = {
            "name": rule_name,
            "enabled": True,
            "matchers": [
                {
                    "field": "to",
                    "type": "literal",
                    "value": f"{local_part}@{self.email_domain}"
                }
            ],
            "actions": [
                {
                    "type": "forward",
                    "value": [destination_email]
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=rule_data)
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result['result']['id']
            return None
        except Exception as e:
            current_app.logger.error(f'Failed to create email forwarding: {e}')
            return None

    def delete_email_forwarding(self, rule_id):
        """Delete an email forwarding rule"""
        if not self._is_configured():
            return False

        import requests

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/email/routing/rules/{rule_id}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            current_app.logger.error(f'Failed to delete email forwarding: {e}')
            return False

    def list_email_forwardings(self):
        """List all email forwarding rules"""
        if not self._is_configured():
            return []

        import requests

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/email/routing/rules"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result['result']
            return []
        except Exception as e:
            current_app.logger.error(f'Failed to list email forwardings: {e}')
            return []


cloudflare_service = CloudflareService()
