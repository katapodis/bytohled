# tests/test_bezrealitky.py
import pytest
import responses as resp_mock
from unittest.mock import patch
from scrapers.bezrealitky import BezrealitkyScraper
from core.database import Database

SAMPLE_RESPONSE = {
    "records": [
        {
            "id": "abc123",
            "uri": "/nemovitosti-byty-domy/ostrava/abc123",
            "headline": "Prodej bytu 1+1, 38 m², Ostrava-Jih",
            "price": 1350000,
            "surface": 38,
            "disposition": "1_1",
            "location": {"city": "Ostrava", "cityPart": "Ostrava-Jih"},
            "mainImageUrl": "https://cdn.bezrealitky.cz/img/abc.jpg",
        }
    ]
}

@pytest.fixture
def scraper(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    config = {"base_url": "https://www.bezrealitky.cz/api/record/markers"}
    return BezrealitkyScraper(config, db)

@resp_mock.activate
@patch('time.sleep')
def test_parses_records(mock_sleep, scraper):
    resp_mock.add(resp_mock.GET,
                  "https://www.bezrealitky.cz/api/record/markers",
                  json=SAMPLE_RESPONSE, status=200)
    listings = scraper.fetch_listings()
    assert len(listings) == 1
    assert listings[0].source == "bezrealitky"
    assert listings[0].price == 1350000
    assert "Ostrava" in listings[0].location

@resp_mock.activate
@patch('time.sleep')
def test_handles_error(mock_sleep, scraper):
    resp_mock.add(resp_mock.GET,
                  "https://www.bezrealitky.cz/api/record/markers",
                  status=500)
    listings = scraper.fetch_listings()
    assert listings == []
