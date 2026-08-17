from app.scrapers.base import BaseScraper

TREEZ_BASE = "https://app.treez.io/api/v2"


class TreezScraper(BaseScraper):
    platform = "treez"

    def _treez_headers(self, api_key: str) -> dict:
        return {
            "partner_key": api_key,
            "Content-Type": "application/json",
        }

    async def fetch_deals(self, store_config: dict) -> list[dict]:
        endpoint = store_config.get("treez_endpoint")
        api_key = store_config.get("treez_api_key")
        if not endpoint or not api_key:
            return []

        data = await self._get(
            f"{endpoint}/promotions",
            extra_headers=self._treez_headers(api_key),
        )
        if not data:
            return []
        promos = data.get("data") or data.get("promotions") or []
        return [self._normalize_deal(p) for p in promos]

    async def fetch_menu(self, store_config: dict) -> list[dict]:
        endpoint = store_config.get("treez_endpoint")
        api_key = store_config.get("treez_api_key")
        if not endpoint or not api_key:
            return []

        products = []
        page = 1
        while True:
            data = await self._get(
                f"{endpoint}/products",
                params={"page": page, "per_page": 100},
                extra_headers=self._treez_headers(api_key),
            )
            if not data:
                break
            items = data.get("data") or data.get("products") or []
            products.extend(items)
            meta = data.get("meta") or {}
            if not items or len(products) >= meta.get("total", 0):
                break
            page += 1

        return [self._normalize_product(p) for p in products]

    def _normalize_deal(self, p: dict) -> dict:
        ptype = (p.get("promotion_type") or p.get("type") or "").lower()
        if "percent" in ptype:
            deal_type, unit = "percent_off", "percent"
        elif "dollar" in ptype or "amount" in ptype:
            deal_type, unit = "dollar_off", "dollar"
        elif "bogo" in ptype:
            deal_type, unit = "bogo", "unit"
        else:
            deal_type, unit = ptype or "other", "other"

        cats = [c.lower() for c in (p.get("applicable_categories") or p.get("categories") or [])]

        return {
            "external_id": str(p.get("id", "")),
            "title": p.get("name") or p.get("title", ""),
            "description": p.get("description", ""),
            "deal_type": deal_type,
            "discount_value": p.get("discount_amount") or p.get("discount_value"),
            "discount_unit": unit,
            "minimum_purchase": p.get("minimum_subtotal") or p.get("minimum_purchase"),
            "applicable_categories": cats,
            "applicable_brands": p.get("applicable_brands") or [],
            "day_of_week": p.get("days_of_week") or [],
            "starts_at": p.get("start_date") or p.get("starts_at"),
            "ends_at": p.get("end_date") or p.get("ends_at"),
            "raw_text": str(p),
        }

    def _normalize_product(self, p: dict) -> dict:
        kind = (p.get("category") or p.get("product_type") or "").lower()
        price = p.get("price_per_unit") or p.get("price")
        sale_price = p.get("sale_price") or p.get("discounted_price")

        thc = None
        cbd = None
        lab = p.get("lab_results") or {}
        if isinstance(lab, dict):
            thc = lab.get("thc") or lab.get("thc_percent")
            cbd = lab.get("cbd") or lab.get("cbd_percent")
        if thc is None:
            thc = p.get("thc") or p.get("thc_percent")
        if cbd is None:
            cbd = p.get("cbd") or p.get("cbd_percent")

        return {
            "external_id": str(p.get("id") or p.get("product_id", "")),
            "name": p.get("name", ""),
            "brand": p.get("brand") or p.get("brand_name", ""),
            "category": kind,
            "thc_percent": thc,
            "cbd_percent": cbd,
            "weight": p.get("net_weight") or p.get("weight"),
            "current_price": price,
            "sale_price": sale_price if sale_price and sale_price != price else None,
        }
