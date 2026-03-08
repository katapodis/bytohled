# scrapers/reality_cz.py
import json
import re
from typing import List
from bs4 import BeautifulSoup
from loguru import logger
from scrapers.base import BaseScraper
from core.database import Listing


class RealityCzScraper(BaseScraper):
    source_id = "reality_cz"

    BASE_URL = "https://www.reality.cz/byty/ostrava/"
    PARAMS = {
        "Disp[]": ["1_1", "1_kk"],
        "PriceMax": 2500000,
        "PriceType": "total",
    }

    def fetch_listings(self) -> List[Listing]:
        url = self.config.get("base_url", self.BASE_URL)
        resp = self._get(url, params=self.PARAMS)
        if resp is None:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        listings = []
        # Reality.cz listing cards - adjust selector if site changes
        cards = soup.select("article.item, div.property-item, .b-result__item")
        if not cards:
            logger.warning(f"[{self.source_id}] No cards found - selector may need update")
        for card in cards:
            listing = self._parse_card(card)
            if listing:
                listings.append(listing)
        return listings

    def _parse_card(self, card) -> Listing | None:
        try:
            link = card.select_one("a[href*='/byty/']") or card.select_one("a")
            if not link:
                return None
            href = link.get("href", "")
            url = f"https://www.reality.cz{href}" if href.startswith("/") else href
            # Extract ID from URL path
            external_id = re.search(r"/(\d+)/?$", url)
            if not external_id:
                return None
            eid = external_id.group(1)

            title_el = card.select_one("h2, h3, .title, .item-title")
            title = title_el.get_text(strip=True) if title_el else ""

            price_el = card.select_one(".price, .item-price, [class*='price']")
            price = self._extract_price(price_el.get_text() if price_el else "")

            location_el = card.select_one(".locality, .location, address")
            location = location_el.get_text(strip=True) if location_el else "Ostrava"

            img_el = card.select_one("img")
            img_src = img_el.get("src") or img_el.get("data-src", "") if img_el else ""

            return Listing(
                source=self.source_id,
                external_id=eid,
                url=url,
                title=title,
                price=price,
                size_category=self._extract_disposition(title),
                location=location,
                images_json=json.dumps([img_src]) if img_src else None,
            )
        except Exception as e:
            logger.warning(f"[{self.source_id}] Parse error: {e}")
            return None

    @staticmethod
    def _extract_price(text: str) -> int | None:
        nums = re.sub(r"[^\d]", "", text)
        return int(nums) if nums else None

    @staticmethod
    def _extract_disposition(title: str) -> str | None:
        m = re.search(r"(1\s*\+\s*(?:1|kk|KK))", title, re.IGNORECASE)
        return m.group(1) if m else None
