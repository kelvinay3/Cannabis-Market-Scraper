from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
import asyncio
import random
import httpx


class BaseScraper(ABC):
    platform: str = "base"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self):
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0, follow_redirects=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def _get(self, url: str, params: dict = None, extra_headers: dict = None) -> Optional[dict]:
        await asyncio.sleep(random.uniform(1.5, 3.5))
        try:
            headers = {**self.headers, **(extra_headers or {})}
            resp = await self.client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                await asyncio.sleep(10)
            print(f"[{self.platform}] HTTP error {e.response.status_code} for {url}")
            return None
        except Exception as e:
            print(f"[{self.platform}] Error fetching {url}: {e}")
            return None

    async def _post(self, url: str, json_body: dict = None, extra_headers: dict = None) -> Optional[dict]:
        await asyncio.sleep(random.uniform(1.0, 2.5))
        try:
            headers = {**self.headers, **(extra_headers or {})}
            resp = await self.client.post(url, json=json_body, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[{self.platform}] Error posting to {url}: {e}")
            return None

    @abstractmethod
    async def fetch_deals(self, store_config: dict) -> list[dict]:
        """Return list of normalized deal dicts."""

    @abstractmethod
    async def fetch_menu(self, store_config: dict) -> list[dict]:
        """Return list of normalized menu item dicts."""

    @staticmethod
    def normalize_deal(raw: dict) -> dict:
        """Subclasses override this to normalize platform-specific response to our schema."""
        return raw
