import re
from app.scrapers.base import BaseScraper

WM_BASE = "https://api-g.weedmaps.com/wm/v2"
WM_DISCOVERY = "https://api-g.weedmaps.com/discovery/v1"


CATEGORY_MAP = {
    "flower": "flower", "pre-roll": "preroll", "pre_roll": "preroll",
    "edible": "edible", "edibles": "edible", "concentrate": "concentrate",
    "vape": "vape", "vape-cartridge": "vape", "tincture": "tincture",
    "topical": "topical", "accessories": "accessories", "seeds": "seeds",
    "gear": "gear",
}


class WeedmapsScraper(BaseScraper):
    platform = "weedmaps"

    async def _wm_headers(self, slug: str = "") -> dict:
        referer = f"https://weedmaps.com/dispensaries/{slug}" if slug else "https://weedmaps.com"
        return {
            "Referer": referer,
            "Origin": "https://weedmaps.com",
            "X-App-Version": "0.0.1",
            "x-wm-client": "web-client",
        }

    async def get_nj_listings(self) -> list[dict]:
        params = {
            "filter[state_abbr]": "NJ",
            "filter[license_type][]": "dispensary",
            "include_dispensary_types": "dispensary",
            "size": 100,
            "page": 1,
        }
        listings = []
        while True:
            data = await self._get(
                f"{WM_DISCOVERY}/listings",
                params=params,
                extra_headers=await self._wm_headers(),
            )
            if not data:
                break
            items = (data.get("data") or {}).get("listings") or []
            listings.extend(items)
            meta = data.get("meta", {}) or {}
            if len(listings) >= meta.get("total_count", 0) or not items:
                break
            params["page"] += 1
        return listings

    async def fetch_deals(self, store_config: dict) -> list[dict]:
        slug = store_config.get("weedmaps_id") or store_config.get("weedmaps_slug")
        if not slug:
            return []
        data = await self._get(
            f"{WM_BASE}/listings/{slug}/deals",
            extra_headers=await self._wm_headers(slug),
        )
        if not data:
            return []
        deals = (data.get("data") or {}).get("deals") or []
        return [self._normalize_deal(d) for d in deals]

    async def fetch_menu(self, store_config: dict) -> list[dict]:
        slug = store_config.get("weedmaps_id") or store_config.get("weedmaps_slug")
        if not slug:
            return []

        products = []
        page = 1
        while True:
            data = await self._get(
                f"{WM_BASE}/listings/{slug}/menu_items",
                params={"page": page, "page_size": 100},
                extra_headers=await self._wm_headers(slug),
            )
            if not data:
                break
            items = (data.get("data") or {}).get("menu_items") or []
            products.extend(items)
            meta = (data.get("meta") or {})
            if not items or len(products) >= meta.get("total_count", 0):
                break
            page += 1

        return [self._normalize_product(p) for p in products]

    def _normalize_deal(self, d: dict) -> dict:
        raw_type = (d.get("discount_type") or d.get("type") or "").lower()
        if "percent" in raw_type:
            deal_type, discount_unit = "percent_off", "percent"
        elif "dollar" in raw_type or "amount" in raw_type:
            deal_type, discount_unit = "dollar_off", "dollar"
        elif "bogo" in raw_type or "buy" in raw_type:
            deal_type, discount_unit = "bogo", "unit"
        else:
            deal_type, discount_unit = raw_type or "other", "other"

        cats = []
        for c in (d.get("applicable_categories") or d.get("categories") or []):
            key = c.lower().replace(" ", "-")
            cats.append(CATEGORY_MAP.get(key, key))

        return {
            "external_id": str(d.get("id", d.get("slug", ""))),
            "title": d.get("title", d.get("name", "")),
            "description": d.get("description", ""),
            "deal_type": deal_type,
            "discount_value": d.get("discount_amount") or d.get("discount_value"),
            "discount_unit": discount_unit,
            "minimum_purchase": d.get("minimum_purchase"),
            "applicable_categories": cats,
            "applicable_brands": d.get("applicable_brands") or [],
            "day_of_week": d.get("days_of_week") or [],
            "starts_at": d.get("start_date") or d.get("starts_at"),
            "ends_at": d.get("end_date") or d.get("ends_at"),
            "raw_text": str(d),
        }

    def _normalize_product(self, p: dict) -> dict:
        kind = (p.get("category") or p.get("type") or "").lower().replace(" ", "-")
        price_info = p.get("price_each") or {}
        price = price_info.get("price") or p.get("price")
        sale_price = price_info.get("sale_price") or p.get("sale_price")

        thc = p.get("lab_results", {}).get("thc") if isinstance(p.get("lab_results"), dict) else p.get("percent_thc")
        cbd = p.get("lab_results", {}).get("cbd") if isinstance(p.get("lab_results"), dict) else p.get("percent_cbd")

        return {
            "external_id": str(p.get("id", p.get("slug", ""))),
            "name": p.get("name", ""),
            "brand": p.get("brand") or (p.get("brand_info") or {}).get("name", ""),
            "category": CATEGORY_MAP.get(kind, kind),
            "thc_percent": thc,
            "cbd_percent": cbd,
            "weight": p.get("net_weight") or p.get("weight"),
            "current_price": price,
            "sale_price": sale_price if sale_price and sale_price != price else None,
        }
