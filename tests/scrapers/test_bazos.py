from pathlib import Path
from bs4 import BeautifulSoup
from scrapers.bazos.scraper import parse_page

FIXTURE = Path(__file__).parent / "fixtures" / "bazos_page.html"


def test_parse_page_returns_listings():
    html = FIXTURE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    listings = parse_page(soup, price_type="sale")

    assert len(listings) > 0
    assert listings[0].source == "bazos"
    assert listings[0].url.startswith("https://")
    assert listings[0].title != ""
