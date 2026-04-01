import os
from datetime import datetime, timedelta, timezone

import httpx
from supabase import create_client, Client

from scrapers.base import Listing


class SupabaseDB:
    def __init__(self) -> None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.client: Client = create_client(url, key)

    def listing_exists(self, external_id: str, source: str) -> bool:
        result = (
            self.client.table("listings")
            .select("id")
            .eq("external_id", external_id)
            .eq("source", source)
            .execute()
        )
        return len(result.data) > 0

    def insert_listing(self, listing: Listing, storage_images: list[str]) -> dict:
        data = {
            "external_id": listing.external_id,
            "source": listing.source,
            "url": listing.url,
            "title": listing.title,
            "price": listing.price,
            "price_type": listing.price_type,
            "disposition": listing.disposition,
            "area_m2": listing.area_m2,
            "address": listing.address,
            "city": listing.city,
            "description": listing.description,
            "images": storage_images,
            "is_active": True,
        }
        result = self.client.table("listings").insert(data).execute()
        return result.data[0]

    def get_stale_listings(self) -> list[dict]:
        """Vrátí aktivní inzeráty nekontrolované déle než 24 hodin."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        result = (
            self.client.table("listings")
            .select("id,url,source")
            .eq("is_active", True)
            .lt("last_checked_at", cutoff)
            .execute()
        )
        return result.data

    def update_listing_city(self, external_id: str, source: str, city: str) -> None:
        self.client.table("listings").update({"city": city}).eq("external_id", external_id).eq("source", source).eq("city", None).execute()

    def update_listing_active(self, listing_id: str, is_active: bool) -> None:
        self.client.table("listings").update({
            "is_active": is_active,
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", listing_id).execute()

    def mark_notified(self, listing_id: str) -> None:
        self.client.table("listings").update({
            "notified_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", listing_id).execute()

    def upload_images(self, source: str, external_id: str, image_urls: list[str]) -> list[str]:
        """Stáhne fotky ze zdrojových URL a nahraje do Supabase Storage.
        Vrátí seznam Storage public URL. Selhání jednotlivých fotek se tiše přeskočí."""
        storage_urls = []
        for i, url in enumerate(image_urls[:10]):
            try:
                response = httpx.get(url, timeout=10, follow_redirects=True)
                response.raise_for_status()
                path = f"{source}/{external_id}/{i}.jpg"
                self.client.storage.from_("listing-images").upload(
                    path,
                    response.content,
                    {"content-type": "image/jpeg", "upsert": "true"},
                )
                public_url = self.client.storage.from_("listing-images").get_public_url(path)
                storage_urls.append(public_url)
            except Exception:
                pass
        return storage_urls
