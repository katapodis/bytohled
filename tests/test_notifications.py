# tests/test_notifications.py
import pytest
from unittest.mock import patch, MagicMock
from core.database import Listing
from notifications.telegram import TelegramNotifier
from notifications.email_notifier import EmailNotifier


def make_listing(**kwargs):
    defaults = dict(
        source="sreality", external_id="99",
        url="https://www.sreality.cz/detail/prodej/byt/99",
        title="Byt 1+1, 38 m², Ostrava-Jih", price=1490000,
        size_category="1+1", location="Ostrava-Jih",
        description="Hezky zachovaly byt v klidne lokalite.",
        images_json='["https://cdn.sreality.cz/img/abc.jpg"]',
    )
    defaults.update(kwargs)
    return Listing(**defaults)


def test_format_message_contains_title():
    notifier = TelegramNotifier("fake_token", "fake_chat_id")
    msg = notifier.format_message(make_listing())
    assert "Byt 1+1" in msg


def test_format_message_contains_price():
    notifier = TelegramNotifier("fake_token", "fake_chat_id")
    msg = notifier.format_message(make_listing(price=1490000))
    # Price should appear in formatted form
    assert "1" in msg and "490" in msg


def test_format_message_no_price_shows_placeholder():
    notifier = TelegramNotifier("fake_token", "fake_chat_id")
    msg = notifier.format_message(make_listing(price=None))
    assert "neuvedena" in msg.lower() or "Cena" in msg


def test_format_message_contains_url():
    notifier = TelegramNotifier("fake_token", "fake_chat_id")
    msg = notifier.format_message(make_listing())
    assert "sreality.cz" in msg


def test_email_format_contains_html():
    notifier = EmailNotifier(
        host="smtp.test.com", port=587,
        user="a@b.com", password="pass",
        email_from="a@b.com", email_to="b@c.com"
    )
    html = notifier.format_html(make_listing())
    assert "<html" in html.lower()
    assert "Ostrava" in html
