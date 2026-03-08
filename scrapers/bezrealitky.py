# scrapers/bezrealitky.py
import json
from typing import List
from loguru import logger
from scrapers.base import BaseScraper
from core.database import Listing


class BezrealitkyScraper(BaseScraper):
    source_id = "bezrealitky"

    PARAMS = {
        "offerType": "PRODEJ",
        "estateType": "BYT",
        "disposition[]": ["1_1", "1_kk"],
        "location[]": "Ostrava",
        "priceMax": 2500000,
        "limit": 100,
    }

    def fetch_listings(self) -> List[Listing]:
        base_url = self.config.get(
            "base_url", "https://www.bezrealitky.cz/api/record/markers"
        )
        resp = self._get(base_url, params=self.PARAMS)
        if resp is None:
            return []
        try:
            data = resp.json()
        except ValueError:
            logger.error(f"[{self.source_id}] Invalid JSON")
            return []

        records = data if isinstance(data, list) else data.get("records", [])
        return [l for l in (self._parse_record(r) for r in records) if l]

    def _parse_record(self, record: dict) -> "Listing | None":
        try:
            rid = str(record.get("id", ""))
            if not rid:
                return None
            uri = record.get("uri", "")
            url = f"https://www.bezrealitky.cz{uri}" if uri.startswith("/") else uri
            location_obj = record.get("location", {})
            city_part = location_obj.get("cityPart", "")
            city = location_obj.get("city", "")
            location = f"{city_part}, {city}".strip(", ") if city_part else city
            disp_raw = record.get("disposition", "")
            # Convert "1_1" -> "1+1", "1_kk" -> "1+kk"
            size_cat = disp_raw.replace("_", "+") if disp_raw else None
            image = record.get("mainImageUrl") or ""
            return Listing(
                source=self.source_id,
                external_id=rid,
                url=url,
                title=record.get("headline", ""),
                price=record.get("price"),
                size_category=size_cat,
                location=location,
                images_json=json.dumps([image]) if image else None,
                raw_data=json.dumps(record),
            )
        except Exception as e:
            logger.warning(f"[{self.source_id}] Parse error: {e}")
            return None
