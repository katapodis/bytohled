# tests/test_web_auth.py
from unittest.mock import MagicMock


def test_check_credentials_valid(monkeypatch):
    monkeypatch.setenv("DASHBOARD_USER", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    from web.auth import check_credentials
    assert check_credentials("admin", "secret") is True


def test_check_credentials_invalid(monkeypatch):
    monkeypatch.setenv("DASHBOARD_USER", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    from web.auth import check_credentials
    assert check_credentials("admin", "wrong") is False
    assert check_credentials("hacker", "secret") is False


def test_make_and_parse_session_cookie(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-key")
    from web.auth import make_session_cookie, get_current_user
    token = make_session_cookie("admin")
    assert isinstance(token, str) and len(token) > 10
    # Simulate request with cookie
    request = MagicMock()
    request.cookies = {"session": token}
    assert get_current_user(request) == "admin"


def test_get_current_user_no_cookie(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-key")
    from web.auth import get_current_user
    request = MagicMock()
    request.cookies = {}
    assert get_current_user(request) is None


def test_get_current_user_bad_token(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-key")
    from web.auth import get_current_user
    request = MagicMock()
    request.cookies = {"session": "tampered.garbage.token"}
    assert get_current_user(request) is None
