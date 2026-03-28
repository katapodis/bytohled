from scrapers.base import Listing, BaseScraper


def test_listing_requires_price_type_sale_or_rent():
    listing = Listing(
        external_id="123",
        source="test",
        url="https://example.com/123",
        title="Test byt",
        price=1_500_000,
        price_type="sale",
        disposition="1+1",
        area_m2=40,
        address="Ostrava",
        description="Popis",
        images=[],
    )
    assert listing.price_type == "sale"


def test_listing_images_default_empty():
    listing = Listing(
        external_id="1",
        source="test",
        url="https://example.com/1",
        title="Byt",
        price=None,
        price_type="rent",
        disposition=None,
        area_m2=None,
        address=None,
        description=None,
    )
    assert listing.images == []


def test_base_scraper_raises_not_implemented():
    scraper = BaseScraper()
    try:
        scraper.fetch_listings()
        assert False, "Should have raised"
    except NotImplementedError:
        pass
