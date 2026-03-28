from unittest.mock import MagicMock, patch
from scrapers.base import Listing
from scrapers.runner import run_scrapers, check_stale_listings


def make_listing(external_id="1", source="test"):
    return Listing(
        external_id=external_id,
        source=source,
        url=f"https://example.com/{external_id}",
        title="Byt",
        price=1_000_000,
        price_type="sale",
        disposition="1+1",
        area_m2=40,
        address="Ostrava",
        description="Popis",
    )


def test_new_listing_is_inserted_and_notified():
    db = MagicMock()
    notifier = MagicMock()
    db.listing_exists.return_value = False
    db.upload_images.return_value = []
    db.insert_listing.return_value = {"id": "uuid-1"}

    listing = make_listing()
    run_scrapers(scrapers=[], db=db, notifier=notifier, extra_listings=[listing])

    db.insert_listing.assert_called_once()
    notifier.send_listing.assert_called_once()


def test_existing_listing_is_skipped():
    db = MagicMock()
    notifier = MagicMock()
    db.listing_exists.return_value = True

    listing = make_listing()
    run_scrapers(scrapers=[], db=db, notifier=notifier, extra_listings=[listing])

    db.insert_listing.assert_not_called()
    notifier.send_listing.assert_not_called()


def test_scraper_error_does_not_stop_others():
    db = MagicMock()
    notifier = MagicMock()
    db.listing_exists.return_value = False
    db.upload_images.return_value = []
    db.insert_listing.return_value = {"id": "uuid-2"}

    bad_scraper = MagicMock()
    bad_scraper.fetch_listings.side_effect = Exception("Network error")

    good_listing = make_listing(external_id="99")
    good_scraper = MagicMock()
    good_scraper.fetch_listings.return_value = [good_listing]

    run_scrapers(scrapers=[bad_scraper, good_scraper], db=db, notifier=notifier)

    db.insert_listing.assert_called_once()


def test_check_stale_marks_inactive_on_404():
    db = MagicMock()
    db.get_stale_listings.return_value = [{"id": "uuid-3", "url": "https://example.com/gone"}]

    with patch("scrapers.runner.httpx.head") as mock_head:
        mock_head.return_value = MagicMock(status_code=404)
        check_stale_listings(db)

    db.update_listing_active.assert_called_once_with("uuid-3", False)


def test_check_stale_keeps_active_on_200():
    db = MagicMock()
    db.get_stale_listings.return_value = [{"id": "uuid-4", "url": "https://example.com/ok"}]

    with patch("scrapers.runner.httpx.head") as mock_head:
        mock_head.return_value = MagicMock(status_code=200)
        check_stale_listings(db)

    db.update_listing_active.assert_called_once_with("uuid-4", True)
