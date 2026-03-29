import json
import logging
import re

import httpx
import yaml
from pathlib import Path

from scrapers.base import BaseScraper, Listing

CONFIG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "cs,en;q=0.9",
}

# Maps Bezrealitky disposition codes to human-readable strings
DISPOSITION_MAP = {
    "DISP_1_KK": "1+kk",
    "DISP_1_1": "1+1",
    "DISP_2_KK": "2+kk",
    "DISP_2_1": "2+1",
    "DISP_3_KK": "3+kk",
    "DISP_3_1": "3+1",
    "DISP_4_KK": "4+kk",
    "DISP_4_1": "4+1",
    "DISP_5_KK": "5+kk",
    "DISP_5_1": "5+1",
    "DISP_6_KK": "6+kk",
    "DISP_6_1": "6+1",
    "DISP_7_1": "7+",
    "DISP_OTHER": None,
}

log = logging.getLogger(__name__)


def _extract_next_data(html: str) -> dict:
    """Extract __NEXT_DATA__ JSON embedded in the page."""
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        log.warning("Bezrealitky: nelze parsovat __NEXT_DATA__ JSON: %s", e)
        return {}


def _resolve_image_url(ref_id: str, apollo_cache: dict) -> str | None:
    """Resolve image URL from apolloCache using __ref id."""
    image_key = f"Image:{ref_id}"
    image = apollo_cache.get(image_key, {})
    # Prefer RECORD_MAIN, fall back to RECORD_THUMB
    url = image.get('url({"filter":"RECORD_MAIN"})')
    if not url:
        url = image.get('url({"filter":"RECORD_THUMB"})')
    return url or None


def parse_listing(item: dict, apollo_cache: dict | None = None) -> Listing:
    """Parse a single Advert dict from apolloCache into a Listing."""
    advert_id = str(item.get("id", ""))
    uri = item.get("uri", advert_id)
    price_type = CONFIG.get("price_type", "sale")

    # URL from URI slug
    url = f"https://www.bezrealitky.cz/nemovitosti-byty-domy/{uri}"

    # Price
    price_raw = item.get("price")
    price = int(price_raw) if isinstance(price_raw, (int, float)) and price_raw > 0 else None

    # Disposition
    disp_code = item.get("disposition")
    disposition = DISPOSITION_MAP.get(disp_code) if disp_code else None

    # Area
    surface = item.get("surface")
    area_m2 = int(surface) if isinstance(surface, (int, float)) and surface > 0 else None

    # Address — key has locale suffix in apollo cache
    address = item.get('address({"locale":"CS"})') or item.get("address") or None

    # Title from imageAltText (it's descriptive) or build from disposition + area
    alt_text = item.get('imageAltText({"locale":"CS"})') or ""
    if alt_text:
        title = alt_text
    else:
        parts = []
        if disposition:
            parts.append(f"Byt {disposition}")
        if area_m2:
            parts.append(f"{area_m2} m²")
        if address:
            parts.append(address)
        title = " ".join(parts) if parts else f"Inzerát {advert_id}"

    # Images — resolve __ref image IDs from apollo cache
    images: list[str] = []
    if apollo_cache is not None:
        public_images = item.get('publicImages({"limit":3})', [])
        for img_ref in public_images:
            ref = img_ref.get("__ref", "")
            if ref.startswith("Image:"):
                img_id = ref.split(":", 1)[1]
                url_img = _resolve_image_url(img_id, apollo_cache)
                if url_img:
                    images.append(url_img)

    return Listing(
        external_id=advert_id,
        source="bezrealitky",
        url=url,
        title=title,
        price=price,
        price_type=price_type,
        disposition=disposition,
        area_m2=area_m2,
        address=address,
        description=None,
        images=images,
    )


def parse_apollo_cache(apollo_cache: dict) -> list[Listing]:
    """Extract all Advert listings from an apolloCache dict."""
    listings = []
    for key, value in apollo_cache.items():
        if key.startswith("Advert:") and isinstance(value, dict):
            try:
                listings.append(parse_listing(value, apollo_cache))
            except Exception as e:
                log.warning("Bezrealitky: nelze zpracovat inzerát %s: %s", key, e)
    return listings


class BezrealitkyScraper(BaseScraper):
    def fetch_listings(self) -> list[Listing]:
        listings: list[Listing] = []
        for location in CONFIG.get("locations", []):
            url = location.get("url")
            if not url:
                continue
            try:
                resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
                resp.raise_for_status()
                next_data = _extract_next_data(resp.text)
                apollo_cache = (
                    next_data.get("props", {})
                    .get("pageProps", {})
                    .get("apolloCache", {})
                )
                if not apollo_cache:
                    log.warning("Bezrealitky: prázdný apolloCache pro %s", location.get("name", url))
                    continue
                location_listings = parse_apollo_cache(apollo_cache)
                log.info(
                    "Bezrealitky %s: načteno %d inzerátů",
                    location.get("name", ""),
                    len(location_listings),
                )
                listings.extend(location_listings)
            except Exception as e:
                log.error("Bezrealitky chyba (%s): %s", location.get("name", ""), e)
        return listings
