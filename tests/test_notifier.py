import json
import pytest
import respx
import httpx
from scrapers.notifier import TelegramNotifier


@pytest.fixture
def notifier(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    return TelegramNotifier()


@respx.mock
def test_send_listing_calls_telegram_api(notifier):
    route = respx.post("https://api.telegram.org/bottest-token/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    listing_data = {
        "id": "abc-123",
        "disposition": "1+1",
        "area_m2": 38,
        "price": 1_800_000,
        "price_type": "sale",
        "address": "Ostrava-Poruba",
        "source": "sreality",
        "url": "https://sreality.cz/42",
    }
    notifier.send_listing(listing_data, dashboard_url="https://bytohled.vercel.app/listing/abc-123")
    assert route.called


@respx.mock
def test_send_listing_formats_price_with_spaces(notifier):
    route = respx.post("https://api.telegram.org/bottest-token/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    listing_data = {
        "id": "x",
        "disposition": "1+kk",
        "area_m2": 30,
        "price": 1_500_000,
        "price_type": "rent",
        "address": "Frýdek-Místek",
        "source": "bazos",
        "url": "https://bazos.cz/1",
    }
    notifier.send_listing(listing_data)
    body = json.loads(route.calls[0].request.content)
    assert "1 500 000" in body["text"]


@respx.mock
def test_send_listing_handles_none_price(notifier):
    route = respx.post("https://api.telegram.org/bottest-token/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    listing_data = {
        "id": "x",
        "disposition": "2+1",
        "area_m2": 55,
        "price": None,
        "price_type": "sale",
        "address": "Ostrava",
        "source": "sreality",
        "url": "https://sreality.cz/99",
    }
    notifier.send_listing(listing_data)
    body_text = json.loads(route.calls[0].request.content)["text"]
    assert "neuvedena" in body_text
