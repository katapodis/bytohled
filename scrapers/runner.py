import logging
import os

import httpx

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


def check_stale_listings(db: SupabaseDB | None = None) -> None:
    if db is None:
        db = SupabaseDB()

    stale = db.get_stale_listings()
    log.info("Kontrola aktivity: %d inzerátů", len(stale))

    for row in stale:
        try:
            resp = httpx.head(row["url"], timeout=10, follow_redirects=True)
            is_active = resp.status_code < 400
        except Exception:
            is_active = False
        db.update_listing_active(row["id"], is_active)
        log.info("%s → aktivní=%s", row["url"], is_active)


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
