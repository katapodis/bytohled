# core/filter.py
from typing import Optional
from core.database import Listing
from loguru import logger


class ListingFilter:
    def __init__(self, criteria: dict):
        self.location = criteria["location"].lower()
        self.dispositions = [d.lower() for d in criteria["disposition"]]
        self.max_price = criteria["max_price"]
        self.include_no_price = criteria.get("include_no_price", True)

    def matches(self, listing: Listing) -> bool:
        if not self._check_location(listing):
            logger.debug(f"Rejected (location): {listing.url}")
            return False
        if not self._check_disposition(listing):
            logger.debug(f"Rejected (disposition): {listing.url}")
            return False
        if not self._check_price(listing):
            logger.debug(f"Rejected (price): {listing.url}")
            return False
        return True

    def _check_location(self, listing: Listing) -> bool:
        if listing.location:
            return self.location in listing.location.lower()
        if listing.title:
            return self.location in listing.title.lower()
        return False

    def _check_disposition(self, listing: Listing) -> bool:
        if not listing.size_category:
            return True  # include when disposition unknown — user judges from title
        normalized = listing.size_category.lower().replace(" ", "")
        for d in self.dispositions:
            if d.replace(" ", "") == normalized:
                return True
        return False

    def _check_price(self, listing: Listing) -> bool:
        if listing.price is None:
            return self.include_no_price
        return listing.price <= self.max_price
