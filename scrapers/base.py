# scrapers/base.py
import time
import random
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from loguru import logger
from core.database import Listing, Database


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]


class BaseScraper(ABC):
    source_id: str = ""  # override in subclass
    max_retries: int = 3
    backoff_base: float = 2.0

    def __init__(self, config: dict, db: Database):
        self.config = config
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self._random_ua()})

    def _random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    def _get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET with retry + exponential backoff + random delay."""
        for attempt in range(self.max_retries):
            try:
                time.sleep(random.uniform(1.0, 3.0))  # polite delay
                self.session.headers["User-Agent"] = self._random_ua()
                resp = self.session.get(url, timeout=15, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                wait = self.backoff_base ** attempt
                logger.warning(
                    f"[{self.source_id}] Attempt {attempt+1}/{self.max_retries} "
                    f"failed for {url}: {e}. Retrying in {wait:.1f}s"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait)
        logger.error(f"[{self.source_id}] All retries exhausted for {url}")
        return None

    def run(self) -> dict:
        """Execute scraping cycle. Returns stats dict."""
        started = datetime.now()
        listings_found = 0
        new_count = 0
        error_msg = None
        try:
            listings = self.fetch_listings()
            listings_found = len(listings)
            for listing in listings:
                if self.db.insert_listing(listing):
                    new_count += 1
            logger.info(
                f"[{self.source_id}] {listings_found} found, {new_count} new"
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{self.source_id}] Scraper error: {e}")
        finally:
            self.db.log_scrape(
                source=self.source_id,
                started_at=started,
                finished_at=datetime.now(),
                listings_found=listings_found,
                new_listings=new_count,
                error=error_msg,
            )
        return {"source": self.source_id, "found": listings_found,
                "new": new_count, "error": error_msg}

    @abstractmethod
    def fetch_listings(self) -> List[Listing]:
        """Return list of Listing objects from this source."""
        ...
