import json
from pathlib import Path
from scrapers.sreality.scraper import SrealityScraper, parse_listing


FIXTURE = Path(__file__).parent / "fixtures" / "sreality_response.json"


def test_parse_listing_returns_listing_object():
    data = json.loads(FIXTURE.read_text())
    estates = data["_embedded"]["estates"]
    assert len(estates) > 0

    listing = parse_listing(estates[0])

    assert listing.source == "sreality"
    assert listing.price_type == "sale"
    assert listing.external_id != ""
    assert listing.url.startswith("https://")
    assert listing.title != ""


def test_parse_listing_extracts_price():
    data = json.loads(FIXTURE.read_text())
    estate = data["_embedded"]["estates"][0]
    listing = parse_listing(estate)
    # Cena může být None pokud je "Cena na vyžádání", jinak musí být int
    assert listing.price is None or isinstance(listing.price, int)


def test_parse_listing_extracts_disposition():
    data = json.loads(FIXTURE.read_text())
    estate = data["_embedded"]["estates"][0]
    listing = parse_listing(estate)
    assert listing.disposition is not None
