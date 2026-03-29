import logging
import re
import httpx
import yaml
from pathlib import Path
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, Listing, extract_city

CONFIG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
log = logging.getLogger(__name__)


def parse_price(text: str) -> int | None:
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def parse_page(soup: BeautifulSoup, price_type: str = "sale") -> list[Listing]:
    listings = []
    for item in soup.select("div.inzeraty.inzeratyflex"):
        try:
            title_el = item.select_one("h2.nadpis a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://reality.bazos.cz{href}"
            id_match = re.search(r"/inzerat/(\d+)/", url)
            external_id = id_match.group(1) if id_match else url.split("/")[-1]
            price_el = item.select_one('.inzeratycena span[translate="no"]')
            price = parse_price(price_el.get_text()) if price_el else None
            lok_el = item.select_one(".inzeratylok")
            if lok_el:
                parts = [t.strip() for t in lok_el.stripped_strings]
                address = ", ".join(parts) if parts else None
            else:
                address = None
            listings.append(Listing(
                external_id=external_id,
                source="bazos",
                url=url,
                title=title,
                price=price,
                price_type=price_type,
                disposition=None,
                area_m2=None,
                address=address,
                city=extract_city(address),
                description=None,
            ))
        except Exception as e:
            log.warning("Bazoš parse error: %s", e)
    return listings


class BazosScraper(BaseScraper):
    def fetch_listings(self) -> list[Listing]:
        listings: list[Listing] = []
        price_type = CONFIG.get("price_type", "sale")
        seen_ids: set[str] = set()

        for location in CONFIG.get("locations", []):
            url = location.get("url", "")
            if not url:
                continue
            try:
                resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for listing in parse_page(soup, price_type=price_type):
                    if listing.external_id not in seen_ids:
                        seen_ids.add(listing.external_id)
                        listings.append(listing)
                log.info("Bazoš %s: %d inzerátů", location.get("name", ""), len(listings))
            except Exception as e:
                log.error("Bazoš chyba (%s): %s", location.get("name", ""), e)

        return listings
