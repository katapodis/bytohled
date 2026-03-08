# scrapers/bazos.py
import json
import re
from typing import List
from bs4 import BeautifulSoup
from loguru import logger
from scrapers.base import BaseScraper
from core.database import Listing


class BazosScraper(BaseScraper):
    source_id = "bazos"

    BASE_URL = "https://reality.bazos.cz/byt/"

    def fetch_listings(self) -> List[Listing]:
        url = self.config.get("base_url", self.BASE_URL)
        params = {"hledat": "Ostrava", "cena": "2500000", "Submit": "Hledat"}
        resp = self._get(url, params=params)
        if resp is None:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        listings = []
        cards = soup.select(".inzeraty .inzerat, .maincontent .inzerat")
        if not cards:
            logger.warning(f"[{self.source_id}] No cards found - selector may need update")
        for card in cards:
            listing = self._parse_card(card)
            if listing:
                listings.append(listing)
        return listings

    def _parse_card(self, card) -> Listing | None:
        try:
            link = card.select_one("h2 a, .nadpis a, a[href*='reality.bazos.cz']")
            if not link:
                return None
            url = link.get("href", "")
            if not url.startswith("http"):
                url = f"https://reality.bazos.cz{url}"
            eid = re.search(r"/(\d+)/", url)
            if not eid:
                return None
            external_id = eid.group(1)
            title = link.get_text(strip=True)

            price_el = card.select_one(".cena, .price")
            price = self._extract_price(price_el.get_text() if price_el else "")

            location_el = card.select_one(".lokalita, .location")
            location = location_el.get_text(strip=True) if location_el else ""
            if "Ostrava" not in location:
                return None  # skip non-Ostrava listings

            return Listing(
                source=self.source_id,
                external_id=external_id,
                url=url,
                title=title,
                price=price,
                size_category=self._extract_disposition(title),
                location=location,
            )
        except Exception as e:
            logger.warning(f"[{self.source_id}] Parse error: {e}")
            return None

    @staticmethod
    def _extract_price(text: str) -> int | None:
        nums = re.sub(r"[^\d]", "", text)
        return int(nums) if nums and int(nums) > 0 else None

    @staticmethod
    def _extract_disposition(title: str) -> str | None:
        m = re.search(r"(1\s*\+\s*(?:1|kk|KK))", title, re.IGNORECASE)
        return m.group(1) if m else None
