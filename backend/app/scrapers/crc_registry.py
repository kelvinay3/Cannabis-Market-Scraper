"""
NJ Cannabis Regulatory Commission (CRC) dispensary registry scraper.
Runs weekly to discover new/updated licensed dispensaries in NJ.
Public source: https://www.nj.gov/cannabis/businesses/
"""
import re
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper

CRC_BASE = "https://www.nj.gov/cannabis"
CRC_LICENSEES_URL = f"{CRC_BASE}/businesses/resources/license_lists/CRC_Licenses.json"
CRC_HTML_URL = f"{CRC_BASE}/businesses/"

LICENSE_TYPES = {"dispensary", "retailer", "delivery", "dispensary-retailer"}


class CRCRegistryScraper(BaseScraper):
    platform = "crc_registry"

    async def fetch_deals(self, store_config: dict) -> list[dict]:
        return []

    async def fetch_menu(self, store_config: dict) -> list[dict]:
        return []

    async def get_all_nj_dispensaries(self) -> list[dict]:
        json_data = await self._get(CRC_LICENSEES_URL)
        if json_data and isinstance(json_data, list):
            return self._normalize_json(json_data)

        html_result = await self._get(
            CRC_HTML_URL,
            extra_headers={"Accept": "text/html,application/xhtml+xml,*/*"},
        )
        if html_result and isinstance(html_result, str):
            return self._parse_html(html_result)

        return []

    def _normalize_json(self, records: list[dict]) -> list[dict]:
        result = []
        for r in records:
            license_type = (r.get("license_type") or r.get("licenseType") or "").lower()
            if not any(t in license_type for t in LICENSE_TYPES):
                continue

            address = r.get("address") or r.get("premise_address") or {}
            if isinstance(address, str):
                address = {"full": address}

            result.append({
                "name": r.get("business_name") or r.get("businessName") or r.get("name", ""),
                "license_number": r.get("license_number") or r.get("licenseNumber", ""),
                "license_type": license_type,
                "address": address.get("full") or address.get("street") or address.get("address1", ""),
                "city": address.get("city") or r.get("city", ""),
                "county": (address.get("county") or r.get("county", "")).title(),
                "zip": address.get("zip") or address.get("postal_code") or r.get("zip", ""),
                "state": "NJ",
                "phone": r.get("phone") or r.get("phone_number", ""),
                "website": r.get("website") or r.get("website_url", ""),
                "email": r.get("email", ""),
                "status": (r.get("status") or r.get("license_status") or "active").lower(),
                "med_only": "medic" in license_type,
                "source": "crc_json",
                "raw": r,
            })
        return result

    def _parse_html(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        result = []
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if not any(h in headers for h in ["business", "name", "license"]):
                continue
            for row in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if not cells:
                    continue
                row_data = dict(zip(headers, cells))
                name = row_data.get("business name") or row_data.get("name") or cells[0]
                if not name:
                    continue
                result.append({
                    "name": name,
                    "license_number": row_data.get("license #") or row_data.get("license number", ""),
                    "license_type": (row_data.get("license type") or row_data.get("type", "")).lower(),
                    "address": row_data.get("address", ""),
                    "city": row_data.get("city", ""),
                    "county": row_data.get("county", "").title(),
                    "zip": row_data.get("zip") or row_data.get("postal code", ""),
                    "state": "NJ",
                    "phone": row_data.get("phone", ""),
                    "website": row_data.get("website", ""),
                    "email": row_data.get("email", ""),
                    "status": "active",
                    "med_only": False,
                    "source": "crc_html",
                    "raw": row_data,
                })
        return result
