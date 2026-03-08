# core/runner.py
import os
from typing import Optional
from loguru import logger
from core.database import Database
from core.filter import ListingFilter
from notifications.telegram import TelegramNotifier
from notifications.email_notifier import EmailNotifier
from scrapers.sreality import SrealityScraper
from scrapers.bezrealitky import BezrealitkyScraper
from scrapers.reality_cz import RealityCzScraper
from scrapers.bazos import BazosScraper
from scrapers.facebook import FacebookScraper
from scrapers.local_agency import LocalAgencyScraper


def build_notifiers(config: dict) -> tuple[Optional[TelegramNotifier], Optional[EmailNotifier]]:
    """Build notifiers from environment variables. Returns (telegram, email) tuple."""
    tg = None
    em = None

    if config.get("notifications", {}).get("telegram", {}).get("enabled", True):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            tg = TelegramNotifier(token, chat_id)
        else:
            logger.warning("Telegram credentials not set — skipping Telegram notifications")

    if config.get("notifications", {}).get("email", {}).get("enabled", True):
        host = os.getenv("SMTP_HOST")
        user = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASSWORD")
        if host and user and password:
            em = EmailNotifier(
                host=host,
                port=int(os.getenv("SMTP_PORT", "587")),
                user=user,
                password=password,
                email_from=os.getenv("EMAIL_FROM", user),
                email_to=os.getenv("EMAIL_TO", user),
            )
        else:
            logger.warning("SMTP credentials not set — skipping Email notifications")

    return tg, em


def run_once(config: dict, db: Database) -> None:
    """Run one full scraping cycle: scrape all sources, filter, notify."""
    sources = config.get("sources", {})
    criteria = config.get("search_criteria", {})
    listing_filter = ListingFilter(criteria)
    tg, em = build_notifiers(config)

    # Build list of active scrapers
    scrapers = []
    if sources.get("sreality", {}).get("enabled"):
        scrapers.append(SrealityScraper(sources["sreality"], db))
    if sources.get("bezrealitky", {}).get("enabled"):
        scrapers.append(BezrealitkyScraper(sources["bezrealitky"], db))
    if sources.get("reality_cz", {}).get("enabled"):
        scrapers.append(RealityCzScraper(sources["reality_cz"], db))
    if sources.get("bazos", {}).get("enabled"):
        scrapers.append(BazosScraper(sources["bazos"], db))
    if sources.get("facebook", {}).get("enabled"):
        scrapers.append(FacebookScraper(sources["facebook"], db))
    for agency in sources.get("local_agencies", []):
        if agency.get("enabled", True):
            scrapers.append(LocalAgencyScraper(agency, db))

    # Run each scraper in isolation (failure of one doesn't stop others)
    total_new = 0
    for scraper in scrapers:
        try:
            result = scraper.run()
            total_new += result.get("new", 0)
        except Exception as e:
            logger.error(f"Scraper {getattr(scraper, 'source_id', '?')} crashed: {e}")

    # Filter unnotified listings and send notifications
    unnotified = db.get_unnotified_listings()
    notified_count = 0
    for listing in unnotified:
        if listing_filter.matches(listing):
            logger.info(f"Match found: {listing.url}")
            if tg:
                try:
                    tg.send(listing)
                except Exception as e:
                    logger.error(f"Telegram send failed: {e}")
            if em:
                try:
                    em.send(listing)
                except Exception as e:
                    logger.error(f"Email send failed: {e}")
            notified_count += 1
        # Always mark as processed (notified_at set) to avoid re-checking every cycle
        db.mark_notified(listing.source, listing.external_id)

    logger.info(
        f"Cycle complete: {total_new} new listings scraped, "
        f"{notified_count} notifications sent"
    )
