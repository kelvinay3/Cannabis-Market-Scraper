from app.scrapers.jane import JaneScraper
from app.scrapers.dutchie import DutchieScraper
from app.scrapers.weedmaps import WeedmapsScraper
from app.scrapers.leafly import LeaflyScraper
from app.scrapers.treez import TreezScraper

SCRAPER_MAP = {
    "jane": JaneScraper,
    "dutchie": DutchieScraper,
    "weedmaps": WeedmapsScraper,
    "leafly": LeaflyScraper,
    "treez": TreezScraper,
}

__all__ = ["JaneScraper", "DutchieScraper", "WeedmapsScraper", "LeaflyScraper", "TreezScraper", "SCRAPER_MAP"]
