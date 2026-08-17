from typing import Optional
from app.scrapers.base import BaseScraper


JANE_BASE = "https://api.iheartjane.com/v1"

CATEGORY_MAP = {
    "flower": "flower", "pre-roll": "preroll", "pre_roll": "preroll",
    "edible": "edible", "edibles": "edible", "concentrate": "concentrate",
    "concentrates": "concentrate", "vape": "vape", "vapes": "vape",
    "cartridge": "vape", "tincture": "tincture", "topical": "topical",
    "accessories": "accessories",
}


class JaneScraper(BaseScraper):
    platform = "jane"

    async def get_nj_stores(self) -> list[dict]:
        data = await self._get(f"{JANE_BASE}/stores", params={"state": "NJ", "limit": 500})
        if not data:
            return []
        return data.get("data", {}).get("stores", [])

    async def fetch_deals(self, store_config: dict) -> list[dict]:
        store_id = store_config.get("jane_store_id")
        if not store_id:
            return []
        data = await self._get(f"{JANE_BASE}/stores/{store_id}/specials")
        if not data:
            return []
        specials = data.get("data", {}).get("specials", [])
        return [self._normalize_special(s) for s in specials]

    async def fetch_menu(self, store_config: dict) -> list[dict]:
        store_id = store_config.get("jane_store_id")
        if not store_id:
            return []
        data = await self._get(f"{JANE_BASE}/stores/{store_id}/menu")
        if not data:
            return []
        products = data.get("data", {}).get("menu_products", [])
        return [self._normalize_product(p) for p in products]

    def _normalize_special(self, s: dict) -> dict:
        special_type = s.get("special_type", "")
        deal_type = "percent_off" if "percent" in special_type else "dollar_off" if "dollar" in special_type else special_type
        discount_unit = "percent" if deal_type == "percent_off" else "dollar"

        categories = []
        conditions = s.get("conditions", {}) or {}
        if kinds := conditions.get("applicable_kinds"):
            categories = [CATEGORY_MAP.get(k.lower(), k.lower()) for k in (kinds or [])]

        return {
            "external_id": str(s.get("id", "")),
            "title": s.get("title", s.get("name", "")),
            "description": s.get("description", ""),
            "deal_type": deal_type,
            "discount_value": s.get("special_amount"),
            "discount_unit": discount_unit,
            "minimum_purchase": conditions.get("min_subtotal"),
            "applicable_categories": categories,
            "applicable_brands": conditions.get("applicable_brands", []) or [],
            "day_of_week": s.get("days_of_week") or [],
            "starts_at": s.get("start_time"),
            "ends_at": s.get("end_time"),
            "raw_text": str(s),
        }

    def _normalize_product(self, p: dict) -> dict:
        kind = p.get("kind", "")
        return {
            "external_id": str(p.get("id", "")),
            "name": p.get("name", ""),
            "brand": p.get("brand", ""),
            "category": CATEGORY_MAP.get(kind.lower(), kind.lower()),
            "thc_percent": p.get("percent_thc"),
            "cbd_percent": p.get("percent_cbd"),
            "weight": p.get("net_weight"),
            "current_price": p.get("price"),
            "sale_price": p.get("discounted_price"),
        }
