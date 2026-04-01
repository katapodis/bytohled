import json
import logging
import os
import re

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, Listing
from scrapers.db import SupabaseDB
from scrapers.notifier import TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DASHBOARD_BASE_URL = os.getenv("DASHBOARD_BASE_URL", "")


def run_scrapers(
    scrapers: list[BaseScraper],
    db: SupabaseDB | None = None,
    notifier: TelegramNotifier | None = None,
    extra_listings: list[Listing] | None = None,
) -> None:
    if db is None:
        db = SupabaseDB()
    if notifier is None:
        notifier = TelegramNotifier()

    all_listings: list[Listing] = list(extra_listings or [])

    for scraper in scrapers:
        try:
            listings = scraper.fetch_listings()
            log.info("%s: %d inzerátů nalezeno", scraper.__class__.__name__, len(listings))
            all_listings.extend(listings)
        except Exception as e:
            log.error("%s selhalo: %s", scraper.__class__.__name__, e)

    new_count = 0
    for listing in all_listings:
        if db.listing_exists(listing.external_id, listing.source):
            if listing.city:
                db.update_listing_city(listing.external_id, listing.source, listing.city)
            continue

        storage_images = db.upload_images(listing.source, listing.external_id, listing.images)
        row = db.insert_listing(listing, storage_images)
        db.mark_notified(row["id"])

        dashboard_url = f"{DASHBOARD_BASE_URL}/listing/{row['id']}" if DASHBOARD_BASE_URL else ""
        notifier.send_listing(row, dashboard_url=dashboard_url)
        new_count += 1

    log.info("Hotovo: %d nových inzerátů", new_count)


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "cs,en;q=0.9",
}


def _check_sreality(resp: httpx.Response) -> bool:
    """Sreality: inzerát je stažen pokud stránka obsahuje chybové hlášky,
    nebo pokud v __NEXT_DATA__ chybí data o nemovitosti."""
    if resp.status_code >= 400:
        return False
    text = resp.text
    inactive_phrases = [
        "nebyl nalezen",
        "nenalezena",
        "byl stažen",
        "není k dispozici",
        "inzerát neexistuje",
    ]
    text_lower = text.lower()
    if any(phrase in text_lower for phrase in inactive_phrases):
        return False
    # Pokud stránka neobsahuje žádná data o ceně ani dispozici, považujeme za neaktivní
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        text, re.DOTALL,
    )
    if match:
        try:
            data = json.loads(match.group(1))
            page_props = data.get("props", {}).get("pageProps", {})
            if page_props.get("statusCode") == 404 or page_props.get("notFound"):
                return False
        except (json.JSONDecodeError, KeyError):
            pass
    return True


def _check_bezrealitky(resp: httpx.Response) -> bool:
    """Bezrealitky: zkontroluj __NEXT_DATA__ na notFound/statusCode,
    nebo přítomnost chybových textů na stránce."""
    if resp.status_code >= 400:
        return False
    text = resp.text
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        text, re.DOTALL,
    )
    if match:
        try:
            data = json.loads(match.group(1))
            page_props = data.get("props", {}).get("pageProps", {})
            if page_props.get("notFound") or page_props.get("statusCode") == 404:
                return False
            # Pokud apolloCache neobsahuje žádný Advert klíč, inzerát byl odstraněn
            apollo = page_props.get("apolloCache", {})
            if apollo and not any(k.startswith("Advert:") for k in apollo):
                return False
        except (json.JSONDecodeError, KeyError):
            pass
    inactive_phrases = [
        "stažen z nabídky",
        "není k dispozici",
        "inzerát byl smazán",
        "nemovitost nebyla nalezena",
    ]
    if any(phrase in text.lower() for phrase in inactive_phrases):
        return False
    return True


def _check_bazos(resp: httpx.Response) -> bool:
    """Bazoš: stránka odstraněného inzerátu obsahuje specifické hlášky,
    nebo chybí element .inzeratdetail."""
    if resp.status_code >= 400:
        return False
    text_lower = resp.text.lower()
    inactive_phrases = [
        "byl smazán",
        "vypršela jeho platnost",
        "inzerát neexistuje",
        "tento inzerát již",
    ]
    if any(phrase in text_lower for phrase in inactive_phrases):
        return False
    soup = BeautifulSoup(resp.text, "lxml")
    if soup.select_one(".inzeratdetail") is None:
        return False
    return True


_CHECKERS = {
    "sreality": _check_sreality,
    "bezrealitky": _check_bezrealitky,
    "bazos": _check_bazos,
}


def _is_listing_active(url: str, source: str) -> bool:
    """Stáhne stránku a zkontroluje obsah — ne jen HTTP status."""
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True, headers=_HEADERS)
    except Exception as e:
        log.warning("Nepodařilo se načíst %s: %s", url, e)
        return False

    checker = _CHECKERS.get(source)
    if checker:
        return checker(resp)
    # Neznámý zdroj — záložní chování: jen HTTP status
    return resp.status_code < 400


def check_stale_listings(db: SupabaseDB | None = None) -> None:
    if db is None:
        db = SupabaseDB()

    stale = db.get_stale_listings()
    log.info("Kontrola aktivity: %d inzerátů", len(stale))

    for row in stale:
        is_active = _is_listing_active(row["url"], row["source"])
        db.update_listing_active(row["id"], is_active)
        log.info("%s (%s) → aktivní=%s", row["url"], row["source"], is_active)


if __name__ == "__main__":
    from scrapers.sreality.scraper import SrealityScraper
    from scrapers.bezrealitky.scraper import BezrealitkyScraper
    from scrapers.bazos.scraper import BazosScraper

    active_scrapers = [
        SrealityScraper(),
        BezrealitkyScraper(),
        BazosScraper(),
    ]
    run_scrapers(active_scrapers)
    check_stale_listings()
