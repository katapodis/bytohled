# tests/test_sreality.py
import pytest
import responses as resp_mock
import json
from unittest.mock import patch
from scrapers.sreality import SrealityScraper
from core.database import Database

SAMPLE_RESPONSE = {
    "_embedded": {
        "estates": [
            {
                "hash_id": 12345678,
                "name": "Prodej bytu 1+1 32 m²",
                "locality": "Ostrava-Jih, Ostrava",
                "price_czk": {"value_raw": 1490000},
                "type": 1,
                "subtype": 2,
                "_links": {
                    "self": {"href": "/cs/v2/estates/12345678"},
                    "images": [{"href": "https://cdn.sreality.cz/img/abc.jpg"}]
                }
            }
        ]
    },
    "result_size": 1
}

@pytest.fixture
def scraper(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    config = {"base_url": "https://www.sreality.cz/api/cs/v2/estates"}
    return SrealityScraper(config, db)

@resp_mock.activate
@patch('time.sleep')
def test_fetch_listings_parses_response(mock_sleep, scraper):
    resp_mock.add(
        resp_mock.GET,
        "https://www.sreality.cz/api/cs/v2/estates",
        json=SAMPLE_RESPONSE,
        status=200,
    )
    listings = scraper.fetch_listings()
    assert len(listings) >= 1
    assert listings[0].source == "sreality"
    assert listings[0].external_id == "12345678"
    assert listings[0].price == 1490000
    assert "Ostrava" in listings[0].location

@resp_mock.activate
@patch('time.sleep')
def test_fetch_listings_handles_empty(mock_sleep, scraper):
    resp_mock.add(
        resp_mock.GET,
        "https://www.sreality.cz/api/cs/v2/estates",
        json={"_embedded": {"estates": []}, "result_size": 0},
        status=200,
    )
    listings = scraper.fetch_listings()
    assert listings == []

@resp_mock.activate
@patch('time.sleep')
def test_fetch_listings_handles_http_error(mock_sleep, scraper):
    resp_mock.add(
        resp_mock.GET,
        "https://www.sreality.cz/api/cs/v2/estates",
        status=403,
    )
    listings = scraper.fetch_listings()
    assert listings == []
