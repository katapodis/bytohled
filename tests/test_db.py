import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")

from unittest.mock import MagicMock, patch
from scrapers.base import Listing
from scrapers.db import SupabaseDB


@patch("scrapers.db.create_client")
def test_listing_exists_returns_true_when_found(mock_create):
    mock_client = MagicMock()
    mock_create.return_value = mock_client
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": "abc"}]

    db = SupabaseDB()
    assert db.listing_exists("123", "sreality") is True


@patch("scrapers.db.create_client")
def test_listing_exists_returns_false_when_not_found(mock_create):
    mock_client = MagicMock()
    mock_create.return_value = mock_client
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

    db = SupabaseDB()
    assert db.listing_exists("999", "sreality") is False


@patch("scrapers.db.create_client")
def test_insert_listing_maps_fields_correctly(mock_create):
    mock_client = MagicMock()
    mock_create.return_value = mock_client
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "new-id"}]

    db = SupabaseDB()
    listing = Listing(
        external_id="42",
        source="sreality",
        url="https://sreality.cz/42",
        title="Byt 1+1",
        price=1_800_000,
        price_type="sale",
        disposition="1+1",
        area_m2=38,
        address="Ostrava-Poruba",
        description="Popis bytu",
    )
    result = db.insert_listing(listing, storage_images=["https://storage/img.jpg"])

    call_args = mock_client.table.return_value.insert.call_args[0][0]
    assert call_args["external_id"] == "42"
    assert call_args["source"] == "sreality"
    assert call_args["price"] == 1_800_000
    assert call_args["images"] == ["https://storage/img.jpg"]
    assert result == {"id": "new-id"}
