"""
Walmart Marketplace API client.
Handles OAuth token management and inventory endpoints.
"""

import time
import base64
import requests
from typing import Optional


WALMART_API_BASE = "https://marketplace.walmartapis.com/v3"
TOKEN_URL = "https://marketplace.walmartapis.com/v3/token"


class WalmartAPIClient:
    def __init__(self, client_id: str, client_secret: str, channel_type: str = "SELLER"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.channel_type = channel_type
        self._token: Optional[str] = None
        self._token_expiry: float = 0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        resp = requests.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "WM_SVC.NAME": "Walmart Marketplace",
                "WM_QOS.CORRELATION_ID": "inventory-monitor",
            },
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 900)
        return self._token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
            "WM_SVC.NAME": "Walmart Marketplace",
            "WM_QOS.CORRELATION_ID": "inventory-monitor",
            "WM_SEC.ACCESS_TOKEN": self._get_token(),
        }

    def get_all_items(self, limit: int = 100, offset: int = 0) -> dict:
        """Fetch all listed items."""
        resp = requests.get(
            f"{WALMART_API_BASE}/items",
            headers=self._headers(),
            params={"limit": limit, "offset": offset},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_inventory(self, sku: str) -> dict:
        """Get inventory for a single SKU."""
        resp = requests.get(
            f"{WALMART_API_BASE}/inventory",
            headers=self._headers(),
            params={"sku": sku},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_inventory_bulk(self, skus: list[str]) -> list[dict]:
        """Get inventory for multiple SKUs (fetches one by one, Walmart has no batch endpoint)."""
        results = []
        for sku in skus:
            try:
                data = self.get_inventory(sku)
                results.append({"sku": sku, "quantity": data.get("quantity", {}).get("amount", 0)})
            except requests.HTTPError as e:
                results.append({"sku": sku, "quantity": None, "error": str(e)})
        return results

    def update_inventory(self, sku: str, quantity: int, fulfillment_lag_time: int = 1) -> dict:
        """Update inventory quantity for a SKU."""
        payload = {
            "sku": sku,
            "quantity": {
                "unit": "EACH",
                "amount": quantity,
            },
            "fulfillmentLagTime": fulfillment_lag_time,
        }
        resp = requests.put(
            f"{WALMART_API_BASE}/inventory",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload,
            params={"sku": sku},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_all_skus(self) -> list[str]:
        """Paginate through all items and collect SKUs."""
        skus = []
        offset = 0
        limit = 100
        while True:
            data = self.get_all_items(limit=limit, offset=offset)
            items = data.get("ItemResponse", [])
            if not items:
                break
            skus.extend(item["sku"] for item in items if "sku" in item)
            total = data.get("totalItems", 0)
            offset += limit
            if offset >= total:
                break
        return skus
