# scrapers/local_agency.py
import re
import json
import hashlib
from typing import List
from bs4 import BeautifulSoup
from loguru import logger
from scrapers.base import BaseScraper
from core.database import Listing, Database


class LocalAgencyScraper(BaseScraper):
    """Generic scraper for local agency websites. Best-effort HTML extraction."""

    def __init__(self, agency_config: dict, db: Database):
        source_config = {
            "base_url": agency_config["url"],
            "name": agency_config["name"],
        }
        super().__init__(source_config, db)
        self.agency_name = agency_config["name"]
        self.source_id = f"agency_{self._slug(agency_config['name'])}"

    @staticmethod
    def _slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]", "_", name.lower())[:20]

    def fetch_listings(self) -> List[Listing]:
        url = self.config["base_url"]
        resp = self._get(url)
        if resp is None:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        listings = []
        # Generic selectors - works for most RK sites
        links = soup.select("a[href*='byt'], a[href*='flat'], a[href*='prodej']")
        seen: set = set()
        for link in links:
            href = link.get("href", "")
            if not href or href in seen:
                continue
            seen.add(href)
            full_url = href if href.startswith("http") else f"{self._base_domain(url)}{href}"
            text = link.get_text(strip=True)
            if not text or len(text) < 5:
                continue
            price = self._extract_price(text)
            eid = hashlib.md5(full_url.encode()).hexdigest()[:12]
            listings.append(Listing(
                source=self.source_id,
                external_id=eid,
                url=full_url,
                title=text[:200],
                price=price,
                location="Ostrava",
                size_category=self._extract_disposition(text),
            ))
        return listings[:50]  # cap at 50 per agency

    @staticmethod
    def _base_domain(url: str) -> str:
        m = re.match(r"(https?://[^/]+)", url)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_price(text: str) -> int | None:
        nums = re.sub(r"[^\d]", "", text)
        if nums and 100000 < int(nums) < 50000000:
            return int(nums)
        return None

    @staticmethod
    def _extract_disposition(title: str) -> str | None:
        m = re.search(r"(1\s*\+\s*(?:1|kk|KK))", title, re.IGNORECASE)
        return m.group(1) if m else None
