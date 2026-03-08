# scrapers/facebook.py
"""
Facebook scraper -- best-effort stub.

Facebook aggressively blocks automated access. This module is a stub that:
1. Logs that Facebook scraping is disabled/unavailable
2. Returns empty list without raising errors
3. Will not block other scrapers from running

Future implementation options:
- RSS Bridge (https://github.com/RSS-Bridge/rss-bridge) self-hosted
- Playwright headless (public pages only, expect frequent breakage)
- Official Facebook Graph API (requires app approval, limited data)
"""
from typing import List
from loguru import logger
from scrapers.base import BaseScraper
from core.database import Listing


class FacebookScraper(BaseScraper):
    source_id = "facebook"

    def fetch_listings(self) -> List[Listing]:
        groups = self.config.get("groups", [])
        if not groups:
            return []
        logger.info(
            "[facebook] Facebook scraping is not implemented (best-effort stub). "
            f"Configured groups: {groups}. Skipping."
        )
        return []
