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


def test_get_dashboard_stats(db):
    db.insert_listing(Listing(source="sreality", external_id="s1",
                               url="https://ex.com/s1", title="A", price=1000000))
    db.insert_listing(Listing(source="bezrealitky", external_id="b1",
                               url="https://ex.com/b1", title="B"))
    db.mark_notified("sreality", "s1")
    stats = db.get_dashboard_stats()
    assert stats["total"] == 2
    assert stats["notified"] == 1
    assert stats["active"] == 2
    assert stats["sources"] == 2


def test_get_per_source_stats(db):
    db.insert_listing(Listing(source="sreality", external_id="s1",
                               url="https://ex.com/s1", title="A"))
    db.insert_listing(Listing(source="sreality", external_id="s2",
                               url="https://ex.com/s2", title="B"))
    db.insert_listing(Listing(source="bazos", external_id="z1",
                               url="https://ex.com/z1", title="C"))
    rows = db.get_per_source_stats()
    sources = {r["source"]: r for r in rows}
    assert sources["sreality"]["total"] == 2
    assert sources["bazos"]["total"] == 1


def test_get_all_sources(db):
    db.insert_listing(Listing(source="sreality", external_id="s1",
                               url="https://ex.com/s1", title="A"))
    db.insert_listing(Listing(source="bazos", external_id="z1",
                               url="https://ex.com/z1", title="B"))
    sources = db.get_all_sources()
    assert "sreality" in sources
    assert "bazos" in sources


def test_get_listings_filtered_by_source(db):
    db.insert_listing(Listing(source="sreality", external_id="s1",
                               url="https://ex.com/s1", title="A"))
    db.insert_listing(Listing(source="bazos", external_id="z1",
                               url="https://ex.com/z1", title="B"))
    items, total = db.get_listings_filtered(source="sreality")
    assert total == 1
    assert items[0].source == "sreality"


def test_get_listings_filtered_by_price(db):
    db.insert_listing(Listing(source="sreality", external_id="s1",
                               url="https://ex.com/s1", title="A", price=1000000))
    db.insert_listing(Listing(source="sreality", external_id="s2",
                               url="https://ex.com/s2", title="B", price=3000000))
    items, total = db.get_listings_filtered(max_price=2000000)
    assert total == 1
    assert items[0].price == 1000000


def test_get_listings_filtered_unnotified_only(db):
    db.insert_listing(Listing(source="sreality", external_id="s1",
                               url="https://ex.com/s1", title="A"))
    db.insert_listing(Listing(source="sreality", external_id="s2",
                               url="https://ex.com/s2", title="B"))
    db.mark_notified("sreality", "s1")
    items, total = db.get_listings_filtered(unnotified_only=True)
    assert total == 1
    assert items[0].external_id == "s2"


def test_get_listings_filtered_pagination(db):
    for i in range(5):
        db.insert_listing(Listing(source="sreality", external_id=str(i),
                                   url=f"https://ex.com/{i}", title=f"Byt {i}"))
    items, total = db.get_listings_filtered(page=1, per_page=2)
    assert total == 5
    assert len(items) == 2


def test_get_recent_scrape_logs_all_sources(db):
    from datetime import datetime
    db.log_scrape("sreality", datetime.now(), datetime.now(), 10, 5, None)
    db.log_scrape("bazos", datetime.now(), datetime.now(), 3, 1, "timeout")
    logs = db.get_recent_scrape_logs(limit=10)
    assert len(logs) == 2
