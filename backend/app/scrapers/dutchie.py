from app.scrapers.base import BaseScraper

DUTCHIE_GQL_URL = "https://dutchie.com/api/retailer/graphql"

MENU_QUERY = """
query GetMenu($retailerId: ID!) {
  menu(retailerId: $retailerId) {
    products {
      id name brand subcategory
      strainType thcContent cbdContent
      variants { id option price salePrice isDefault }
    }
    specials {
      id name description discountType discountAmount
      startDate endDate enabled
      conditions { minimumPurchasePrice applicableCategories }
    }
  }
}
"""


class DutchieScraper(BaseScraper):
    platform = "dutchie"

    async def fetch_deals(self, store_config: dict) -> list[dict]:
        retailer_id = store_config.get("dutchie_id")
        if not retailer_id:
            return []
        data = await self._post(DUTCHIE_GQL_URL, json_body={"query": MENU_QUERY, "variables": {"retailerId": retailer_id}},
                                extra_headers={"Referer": "https://dutchie.com", "Content-Type": "application/json"})
        if not data:
            return []
        specials = (data.get("data") or {}).get("menu", {}).get("specials", []) or []
        return [self._normalize_special(s) for s in specials if s.get("enabled")]

    async def fetch_menu(self, store_config: dict) -> list[dict]:
        retailer_id = store_config.get("dutchie_id")
        if not retailer_id:
            return []
        data = await self._post(DUTCHIE_GQL_URL, json_body={"query": MENU_QUERY, "variables": {"retailerId": retailer_id}},
                                extra_headers={"Referer": "https://dutchie.com", "Content-Type": "application/json"})
        if not data:
            return []
        products = (data.get("data") or {}).get("menu", {}).get("products", []) or []
        return [self._normalize_product(p) for p in products]

    def _normalize_special(self, s: dict) -> dict:
        dtype = (s.get("discountType") or "").lower()
        deal_type = "percent_off" if "percent" in dtype else "dollar_off" if "dollar" in dtype else dtype or "other"
        conditions = s.get("conditions") or {}
        cats = [c.lower() for c in (conditions.get("applicableCategories") or [])]
        return {
            "external_id": str(s.get("id", "")),
            "title": s.get("name", ""),
            "description": s.get("description", ""),
            "deal_type": deal_type,
            "discount_value": s.get("discountAmount"),
            "discount_unit": "percent" if "percent" in dtype else "dollar",
            "minimum_purchase": conditions.get("minimumPurchasePrice"),
            "applicable_categories": cats,
            "applicable_brands": [],
            "day_of_week": [],
            "starts_at": s.get("startDate"),
            "ends_at": s.get("endDate"),
            "raw_text": str(s),
        }

    def _normalize_product(self, p: dict) -> dict:
        default_variant = next((v for v in (p.get("variants") or []) if v.get("isDefault")), None)
        if not default_variant and p.get("variants"):
            default_variant = p["variants"][0]

        price = default_variant.get("price") if default_variant else None
        sale_price = default_variant.get("salePrice") if default_variant else None

        return {
            "external_id": str(p.get("id", "")),
            "name": p.get("name", ""),
            "brand": p.get("brand", ""),
            "category": (p.get("subcategory") or "").lower(),
            "thc_percent": p.get("thcContent"),
            "cbd_percent": p.get("cbdContent"),
            "weight": None,
            "current_price": price,
            "sale_price": sale_price if sale_price != price else None,
        }
