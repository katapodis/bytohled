import logging
import re
import httpx
import yaml
from pathlib import Path
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, Listing

CONFIG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())
BASE_URL = "https://reality.bazos.cz/byt/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
log = logging.getLogger(__name__)


def parse_price(text: str) -> int | None:
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def parse_page(soup: BeautifulSoup, price_type: str = "sale") -> list[Listing]:
    listings = []
    # Each listing is a div.inzeraty.inzeratyflex (sibling flex row elements)
    for item in soup.select("div.inzeraty.inzeratyflex"):
        try:
            title_el = item.select_one("h2.nadpis a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://reality.bazos.cz{href}"
            # Extract numeric ID from URL path, e.g. /inzerat/216500284/...
            id_match = re.search(r"/inzerat/(\d+)/", url)
            external_id = id_match.group(1) if id_match else url.split("/")[-1]
            # Price is in .inzeratycena span[translate="no"]
            price_el = item.select_one('.inzeratycena span[translate="no"]')
            price = parse_price(price_el.get_text()) if price_el else None
            # Location is in .inzeratylok (may contain city + ZIP on separate lines)
            lok_el = item.select_one(".inzeratylok")
            if lok_el:
                # Get only the first text node (city name), ignoring the ZIP code after <br>
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
                description=None,
            ))
        except Exception as e:
            log.warning("Bazoš parse error: %s", e)
    return listings


class BazosScraper(BaseScraper):
    def fetch_listings(self) -> list[Listing]:
        try:
            resp = httpx.get(BASE_URL, headers=HEADERS, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            return parse_page(soup, price_type=CONFIG.get("price_type", "sale"))
        except Exception as e:
            log.error("Bazoš chyba: %s", e)
            return []
