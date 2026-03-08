# tests/test_database.py
import pytest
from datetime import datetime
from core.database import Database, Listing

@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    yield database
    database.close()

def test_create_tables(db):
    """Tables should exist after initialization."""
    tables = db.get_table_names()
    assert "listings" in tables
    assert "scrape_log" in tables

def test_insert_listing(db):
    listing = Listing(
        source="sreality",
        external_id="12345",
        url="https://example.com/12345",
        title="Byt 1+1 Ostrava-Jih",
        price=1500000,
        size_category="1+1",
        location="Ostrava-Jih",
        description="Pěkný byt",
    )
    db.insert_listing(listing)
    result = db.get_listing_by_external_id("sreality", "12345")
    assert result is not None
    assert result.price == 1500000

def test_duplicate_prevention(db):
    listing = Listing(source="sreality", external_id="999",
                      url="https://example.com/999", title="Test")
    db.insert_listing(listing)
    db.insert_listing(listing)  # second insert should be ignored
    all_listings = db.get_listings_by_source("sreality")
    assert len(all_listings) == 1

def test_mark_notified(db):
    listing = Listing(source="sreality", external_id="42",
                      url="https://example.com/42", title="Test")
    db.insert_listing(listing)
    db.mark_notified("sreality", "42")
    result = db.get_listing_by_external_id("sreality", "42")
    assert result.notified_at is not None

def test_get_unnotified_listings(db):
    for i in range(3):
        db.insert_listing(Listing(
            source="sreality", external_id=str(i),
            url=f"https://example.com/{i}", title=f"Byt {i}",
            price=1000000 * (i + 1)
        ))
    db.mark_notified("sreality", "0")
    unnotified = db.get_unnotified_listings()
    assert len(unnotified) == 2

def test_log_scrape(db):
    db.log_scrape("sreality", started_at=datetime.now(),
                  finished_at=datetime.now(), listings_found=5,
                  new_listings=2, error=None)
    logs = db.get_scrape_logs("sreality", limit=1)
    assert len(logs) == 1
    assert logs[0]["listings_found"] == 5

def test_insert_listing_return_value(db):
    """insert_listing returns True for new listings, False for duplicates."""
    listing = Listing(source="sreality", external_id="777",
                      url="https://example.com/777", title="Test Return")
    first = db.insert_listing(listing)
    second = db.insert_listing(listing)
    assert first is True
    assert second is False

def test_get_unnotified_excludes_inactive(db):
    """get_unnotified_listings should not return is_active=0 listings."""
    active = Listing(source="sreality", external_id="active1",
                     url="https://example.com/active1", title="Active")
    inactive = Listing(source="sreality", external_id="inactive1",
                       url="https://example.com/inactive1", title="Inactive",
                       is_active=False)
    db.insert_listing(active)
    db.insert_listing(inactive)
    # Force the inactive listing's is_active flag to 0 (insert sets it to 1 via UPDATE)
    db.conn.execute(
        "UPDATE listings SET is_active=0 WHERE source=? AND external_id=?",
        ("sreality", "inactive1"),
    )
    db.conn.commit()
    unnotified = db.get_unnotified_listings()
    external_ids = [l.external_id for l in unnotified]
    assert "active1" in external_ids
    assert "inactive1" not in external_ids
