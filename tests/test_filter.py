# tests/test_filter.py
import pytest
from core.filter import ListingFilter
from core.database import Listing

CRITERIA = {
    "location": "Ostrava",
    "disposition": ["1+1", "1+kk", "1 kk", "1 + kk"],
    "max_price": 2500000,
    "include_no_price": True,
}

@pytest.fixture
def flt():
    return ListingFilter(CRITERIA)

def make_listing(**kwargs) -> Listing:
    defaults = dict(source="test", external_id="1", url="http://x.com",
                    title="Byt 1+1 Ostrava-Jih", price=1500000,
                    size_category="1+1", location="Ostrava-Jih")
    defaults.update(kwargs)
    return Listing(**defaults)

def test_passes_valid_listing(flt):
    assert flt.matches(make_listing()) is True

def test_rejects_wrong_location(flt):
    assert flt.matches(make_listing(location="Praha-1")) is False

def test_rejects_too_expensive(flt):
    assert flt.matches(make_listing(price=3000000)) is False

def test_passes_no_price_when_allowed(flt):
    assert flt.matches(make_listing(price=None)) is True

def test_rejects_no_price_when_not_allowed(flt):
    criteria = {**CRITERIA, "include_no_price": False}
    flt2 = ListingFilter(criteria)
    assert flt2.matches(make_listing(price=None)) is False

def test_disposition_case_insensitive(flt):
    for disp in ["1+KK", "1 KK", "1 + kk", "1+1"]:
        assert flt.matches(make_listing(size_category=disp)) is True

def test_rejects_wrong_disposition(flt):
    assert flt.matches(make_listing(size_category="2+1")) is False

def test_includes_unknown_disposition(flt):
    """When size_category is None/empty, include listing so user can judge from title."""
    assert flt.matches(make_listing(size_category=None)) is True

def test_location_in_title_fallback(flt):
    """If location field is empty, check title."""
    assert flt.matches(make_listing(location=None, title="Byt 1+1 Ostrava")) is True

def test_rejects_location_missing_entirely(flt):
    assert flt.matches(make_listing(location=None, title="Byt 1+1 Praha")) is False
