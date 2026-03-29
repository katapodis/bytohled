from pathlib import Path
from bs4 import BeautifulSoup
from scrapers.bazos.scraper import parse_page

FIXTURE = Path(__file__).parent / "fixtures" / "bazos_page.html"


def _listings():
    html = FIXTURE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    return parse_page(soup, price_type="sale")


def test_parse_page_returns_listings():
    listings = _listings()
    assert len(listings) > 0
    assert listings[0].source == "bazos"
    assert listings[0].url.startswith("https://")
    assert listings[0].title != ""


def test_parse_page_extracts_price():
    listings = _listings()
    assert listings[0].price is None or isinstance(listings[0].price, int)


def test_parse_page_extracts_address():
    listings = _listings()
    assert listings[0].address is not None


def test_parse_page_external_id_is_numeric_string():
    listings = _listings()
    assert listings[0].external_id.isdigit()
