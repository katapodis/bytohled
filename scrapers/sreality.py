# scrapers/sreality.py
import json
from typing import List
from loguru import logger
from scrapers.base import BaseScraper
from core.database import Listing


class SrealityScraper(BaseScraper):
    source_id = "sreality"

    # Sreality API: byty (1), prodej (1), Ostrava-město (district 72)
    API_PARAMS = {
        "category_main_cb": 1,   # byty
        "category_type_cb": 1,   # prodej
        "locality_district_id": 72,  # Ostrava-město
        "per_page": 60,
    }
    # category_sub_cb: 2=1+1, 3=1+kk
    DISPOSITION_CODES = [2, 3]

    def fetch_listings(self) -> List[Listing]:
        base_url = self.config.get(
            "base_url", "https://www.sreality.cz/api/cs/v2/estates"
        )
        all_listings = []
        for disp_code in self.DISPOSITION_CODES:
            params = {**self.API_PARAMS, "category_sub_cb": disp_code, "page": 1}
            page = 1
            while page <= 10:
                params["page"] = page
                resp = self._get(base_url, params=params)
                if resp is None:
                    break
                try:
                    data = resp.json()
                except ValueError:
                    logger.error(f"[{self.source_id}] Invalid JSON response")
                    break
                estates = data.get("_embedded", {}).get("estates", [])
                if not estates:
                    break
                for estate in estates:
                    listing = self._parse_estate(estate)
                    if listing:
                        all_listings.append(listing)
                if len(estates) < params.get("per_page", 60):
                    break  # last page
                page += 1
        return all_listings

    def _parse_estate(self, estate: dict) -> "Listing | None":
        try:
            hash_id = str(estate.get("hash_id", ""))
            if not hash_id or hash_id == "0":
                return None
            url = f"https://www.sreality.cz/detail/prodej/byt/{hash_id}"
            price_raw = (estate.get("price_czk") or {}).get("value_raw")
            price = int(price_raw) if price_raw else None
            images = estate.get("_links", {}).get("images", [])
            images_json = json.dumps([img["href"] for img in images[:5] if "href" in img])
            return Listing(
                source=self.source_id,
                external_id=hash_id,
                url=url,
                title=estate.get("name", ""),
                price=price,
                size_category=self._map_disposition(estate),
                location=estate.get("locality", ""),
                description="",
                images_json=images_json,
                raw_data=json.dumps(estate),
            )
        except Exception as e:
            logger.warning(f"[{self.source_id}] Parse error: {e}")
            return None

    def _map_disposition(self, estate: dict) -> str:
        sub = estate.get("subtype", 0)
        mapping = {2: "1+1", 3: "1+kk"}
        return mapping.get(sub, "")
