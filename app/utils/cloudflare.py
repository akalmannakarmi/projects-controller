import requests
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareManager:
    def __init__(self):
        self.zone_id = settings.CF_ZONE_ID
        self.headers = {
            "Authorization": f"Bearer {settings.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }

    def _get_record_id(self, name: str):
        url = f"{API_BASE}/zones/{self.zone_id}/dns_records?type=A&name={name}"
        resp = requests.get(url, headers=self.headers)
        data = resp.json()
        if data.get("result"):
            return data["result"][0]["id"]
        return None

    def update_dns(self, name: str, ip: str):
        """Create or update A record."""
        record_id = self._get_record_id(name)
        payload = {
            "type": "A",
            "name": name,
            "content": ip,
            "ttl": 60,
            "proxied": True,
        }

        if record_id:
            url = f"{API_BASE}/zones/{self.zone_id}/dns_records/{record_id}"
            r = requests.put(url, headers=self.headers, json=payload)
        else:
            url = f"{API_BASE}/zones/{self.zone_id}/dns_records"
            r = requests.post(url, headers=self.headers, json=payload)

        if not r.ok:
            logger.error(f"Cloudflare DNS update failed: {r.text}")
        else:
            logger.info(f"Updated DNS: {name} → {ip}")

    def revert_to_vps(self, name: str):
        """Revert subdomain to VPS IP from settings."""
        self.update_dns(name, settings.VPS_PUBLIC_IP)
