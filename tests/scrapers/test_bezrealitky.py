import json
from pathlib import Path

from scrapers.bezrealitky.scraper import parse_listing, parse_apollo_cache

FIXTURE = Path(__file__).parent / "fixtures" / "bezrealitky_response.json"


def test_fixture_has_adverts():
    data = json.loads(FIXTURE.read_text())
    advert_keys = [k for k in data.keys() if k.startswith("Advert:")]
    assert len(advert_keys) > 0, "Fixture musí obsahovat alespoň jeden Advert"


def test_parse_listing_returns_listing():
    data = json.loads(FIXTURE.read_text())
    advert_keys = [k for k in data.keys() if k.startswith("Advert:")]
    assert len(advert_keys) > 0

    first_advert = data[advert_keys[0]]
    listing = parse_listing(first_advert, apollo_cache=data)

    assert listing.source == "bezrealitky"
    assert listing.external_id != ""
    assert listing.url.startswith("https://")


def test_parse_listing_price():
    data = json.loads(FIXTURE.read_text())
    advert_keys = [k for k in data.keys() if k.startswith("Advert:")]
    first_advert = data[advert_keys[0]]
    listing = parse_listing(first_advert, apollo_cache=data)

    # Price should be a positive integer for sale listings
    assert listing.price is None or (isinstance(listing.price, int) and listing.price > 0)


def test_parse_listing_disposition():
    data = json.loads(FIXTURE.read_text())
    advert_keys = [k for k in data.keys() if k.startswith("Advert:")]
    first_advert = data[advert_keys[0]]
    listing = parse_listing(first_advert, apollo_cache=data)

    # Disposition should be a human-readable string or None
    if listing.disposition is not None:
        assert "+" in listing.disposition, f"Unexpected disposition: {listing.disposition}"


def test_parse_listing_area():
    data = json.loads(FIXTURE.read_text())
    advert_keys = [k for k in data.keys() if k.startswith("Advert:")]
    first_advert = data[advert_keys[0]]
    listing = parse_listing(first_advert, apollo_cache=data)

    # Area should be a positive integer or None
    assert listing.area_m2 is None or (isinstance(listing.area_m2, int) and listing.area_m2 > 0)


def test_parse_apollo_cache_returns_all_adverts():
    data = json.loads(FIXTURE.read_text())
    advert_keys = [k for k in data.keys() if k.startswith("Advert:")]
    expected_count = len(advert_keys)

    listings = parse_apollo_cache(data)

    assert len(listings) == expected_count
    for listing in listings:
        assert listing.source == "bezrealitky"
        assert listing.external_id != ""
        assert listing.url.startswith("https://")
