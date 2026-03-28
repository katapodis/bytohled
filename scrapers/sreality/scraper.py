import re
import httpx
import yaml
from pathlib import Path
from scrapers.base import BaseScraper, Listing

CONFIG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())
BASE_URL = "https://www.sreality.cz/api/cs/v2/estates"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

DISPOSITIONS = ["1+kk", "1+1", "2+kk", "2+1", "3+kk", "3+1", "4+kk", "4+1", "5+kk", "5+1", "6+"]


def _extract_disposition(name: str) -> str | None:
    for disp in DISPOSITIONS:
        if disp.lower() in name.lower():
            return disp
    return None


def _extract_area(name: str) -> int | None:
    match = re.search(r"(\d+)\s*m[²2]", name)
    if match:
        return int(match.group(1))
    return None


def parse_listing(estate: dict) -> Listing:
    hash_id = str(estate["hash_id"])
    name = estate.get("name", "")

    # Price — prefer price_czk.value_raw, fall back to top-level price
    price: int | None = None
    price_czk = estate.get("price_czk", {})
    if isinstance(price_czk, dict):
        raw = price_czk.get("value_raw")
        if isinstance(raw, int) and raw > 0:
            price = raw
    if price is None:
        top_price = estate.get("price")
        if isinstance(top_price, int) and top_price > 0:
            price = top_price

    # URL — built from seo locality + hash_id
    seo = estate.get("seo", {})
    locality_seo = seo.get("locality", "ostrava") if isinstance(seo, dict) else "ostrava"
    price_type = CONFIG.get("price_type", "sale")
    action = "prodej" if price_type == "sale" else "pronajem"
    url = f"https://www.sreality.cz/detail/{action}/byt/{locality_seo}/{hash_id}"

    # Images — direct URLs (no placeholder substitution needed)
    images: list[str] = []
    links = estate.get("_links", {})
    for img in links.get("images", [])[:10]:
        href = img.get("href", "")
        if href:
            images.append(href)

    # Address — locality is a plain string in the API response
    address_raw = estate.get("locality", "")
    address = address_raw if isinstance(address_raw, str) else ""

    # Disposition and area — extracted from the listing name
    disposition = _extract_disposition(name)
    area_m2 = _extract_area(name)

    return Listing(
        external_id=hash_id,
        source="sreality",
        url=url,
        title=name,
        price=price,
        price_type=price_type,
        disposition=disposition,
        area_m2=area_m2,
        address=address,
        description=None,
        images=images,
    )


class SrealityScraper(BaseScraper):
    def fetch_listings(self) -> list[Listing]:
        listings: list[Listing] = []
        price_type = CONFIG.get("price_type", "sale")
        category_type_cb = 1 if price_type == "sale" else 2

        for location in CONFIG.get("locations", []):
            params: dict = {
                "category_main_cb": 1,
                "category_type_cb": category_type_cb,
                "per_page": 60,
                "page": 1,
                **location.get("params", {}),
            }
            try:
                resp = httpx.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                for estate in data.get("_embedded", {}).get("estates", []):
                    listings.append(parse_listing(estate))
            except Exception as e:
                print(f"Sreality chyba ({location.get('name', '')}): {e}")

        return listings
