import re
import json
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper

LEAFLY_BASE = "https://consumer-api.leafly.com/api"
LEAFLY_WEB = "https://www.leafly.com"


CATEGORY_MAP = {
    "flower": "flower", "pre-roll": "preroll", "pre_roll": "preroll",
    "edible": "edible", "concentrate": "concentrate", "vaporizer": "vape",
    "vape": "vape", "tincture": "tincture", "topical": "topical",
    "accessory": "accessories", "seed": "seeds",
}


class LeaflyScraper(BaseScraper):
    platform = "leafly"

    def _leafly_headers(self, slug: str = "") -> dict:
        referer = f"{LEAFLY_WEB}/dispensary-info/{slug}" if slug else LEAFLY_WEB
        return {
            "Referer": referer,
            "App-Release-Version": "2024.1.0",
            "X-Leafly-Client": "web",
        }

    async def get_nj_dispensaries(self) -> list[dict]:
        results = []
        skip = 0
        take = 50
        while True:
            data = await self._get(
                f"{LEAFLY_BASE}/dispensary_v2.0",
                params={
                    "state": "NJ",
                    "take": take,
                    "skip": skip,
                    "filter_license_type": "recreational",
                },
                extra_headers=self._leafly_headers(),
            )
            if not data:
                break
            items = data.get("dispensaries") or []
            results.extend(items)
            if len(items) < take:
                break
            skip += take
        return results

    async def fetch_deals(self, store_config: dict) -> list[dict]:
        slug = store_config.get("leafly_slug")
        if not slug:
            return []

        data = await self._get(
            f"{LEAFLY_BASE}/dispensary_v2.0/{slug}/deals",
            extra_headers=self._leafly_headers(slug),
        )
        if not data:
            return []

        deals = data.get("deals") or data.get("specials") or []
        return [self._normalize_deal(d) for d in deals]

    async def fetch_menu(self, store_config: dict) -> list[dict]:
        slug = store_config.get("leafly_slug")
        if not slug:
            return []

        products = []
        page = 1
        while True:
            data = await self._get(
                f"{LEAFLY_BASE}/strain_playlists/v2",
                params={
                    "dispensary_slug": slug,
                    "strain_playlist_type": "all",
                    "page": page,
                    "page_size": 100,
                },
                extra_headers=self._leafly_headers(slug),
            )
            if not data:
                break
            items = (data.get("hits") or {}).get("strain", []) or data.get("products") or []
            products.extend(items)
            total = (data.get("total_count") or data.get("hits", {}).get("total") or 0)
            if not items or len(products) >= total:
                break
            page += 1

        return [self._normalize_product(p) for p in products]

    async def _scrape_page(self, slug: str) -> dict:
        html = await self._get(
            f"{LEAFLY_WEB}/dispensary-info/{slug}",
            extra_headers={**self._leafly_headers(slug), "Accept": "text/html,application/xhtml+xml,*/*"},
        )
        if not html or not isinstance(html, str):
            return {}
        soup = BeautifulSoup(html, "lxml")
        tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not tag:
            return {}
        try:
            return json.loads(tag.string or "{}")
        except Exception:
            return {}

    def _normalize_deal(self, d: dict) -> dict:
        raw_type = (d.get("deal_type") or d.get("type") or "").lower()
        if "percent" in raw_type:
            deal_type, discount_unit = "percent_off", "percent"
        elif "dollar" in raw_type or "amount" in raw_type:
            deal_type, discount_unit = "dollar_off", "dollar"
        elif "bogo" in raw_type:
            deal_type, discount_unit = "bogo", "unit"
        else:
            deal_type, discount_unit = raw_type or "other", "other"

        cats = []
        for c in (d.get("applicable_categories") or d.get("categories") or []):
            key = c.lower().replace(" ", "_")
            cats.append(CATEGORY_MAP.get(key, key))

        return {
            "external_id": str(d.get("id", "")),
            "title": d.get("title") or d.get("name", ""),
            "description": d.get("description", ""),
            "deal_type": deal_type,
            "discount_value": d.get("discount_amount") or d.get("discount_value"),
            "discount_unit": discount_unit,
            "minimum_purchase": d.get("minimum_purchase"),
            "applicable_categories": cats,
            "applicable_brands": d.get("applicable_brands") or [],
            "day_of_week": d.get("days_of_week") or d.get("applicable_days") or [],
            "starts_at": d.get("start_date") or d.get("starts_at"),
            "ends_at": d.get("end_date") or d.get("ends_at"),
            "raw_text": str(d),
        }

    def _normalize_product(self, p: dict) -> dict:
        kind = (p.get("category") or p.get("category_type") or "").lower()
        price = p.get("price") or (p.get("prices") or [{}])[0].get("price") if p.get("prices") else None
        sale_price = p.get("sale_price") or p.get("discounted_price")

        return {
            "external_id": str(p.get("id", p.get("slug", ""))),
            "name": p.get("name", ""),
            "brand": p.get("brand") or p.get("brand_name", ""),
            "category": CATEGORY_MAP.get(kind.replace(" ", "_"), kind),
            "thc_percent": p.get("thc") or p.get("percent_thc"),
            "cbd_percent": p.get("cbd") or p.get("percent_cbd"),
            "weight": p.get("net_weight") or p.get("weight"),
            "current_price": price,
            "sale_price": sale_price if sale_price and sale_price != price else None,
        }
