# tests/test_web_app.py
import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DASHBOARD_USER", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    # Import after env setup so auth reads correct values
    import importlib
    import web.app as app_module
    importlib.reload(app_module)
    return TestClient(app_module.app, follow_redirects=False)


def test_root_redirects_to_dashboard(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/dashboard"


def test_unauthenticated_dashboard_redirects_to_login(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]


def test_unauthenticated_listings_redirects_to_login(client):
    resp = client.get("/listings")
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]


def test_login_page_returns_200(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.content.lower() or b"p\xc5\x99ihl" in resp.content


def test_login_invalid_credentials(client):
    resp = client.post("/login", data={"username": "wrong", "password": "bad"})
    assert resp.status_code == 401


def test_login_valid_sets_cookie_and_redirects(client):
    resp = client.post("/login", data={"username": "admin", "password": "secret"})
    assert resp.status_code == 302
    assert "session" in resp.cookies


def test_authenticated_dashboard_returns_200(client):
    # Login first
    login = client.post("/login", data={"username": "admin", "password": "secret"},
                        follow_redirects=False)
    session = login.cookies["session"]
    client.cookies.set("session", session)
    resp = client.get("/dashboard")
    client.cookies.clear()
    assert resp.status_code == 200


def test_authenticated_listings_returns_200(client):
    login = client.post("/login", data={"username": "admin", "password": "secret"},
                        follow_redirects=False)
    session = login.cookies["session"]
    client.cookies.set("session", session)
    resp = client.get("/listings")
    client.cookies.clear()
    assert resp.status_code == 200


def test_logout_clears_cookie(client):
    login = client.post("/login", data={"username": "admin", "password": "secret"},
                        follow_redirects=False)
    session = login.cookies["session"]
    client.cookies.set("session", session)
    resp = client.post("/logout")
    client.cookies.clear()
    assert resp.status_code == 302
    # Cookie should be deleted (empty value or absent)
    assert resp.cookies.get("session", "") == ""
