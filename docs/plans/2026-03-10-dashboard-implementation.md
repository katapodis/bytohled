# Web Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a FastAPI web dashboard to BytoHled with login, stats, scrape logs, and filterable listings table.

**Architecture:** FastAPI + Jinja2 server-rendered HTML, itsdangerous session cookies for single-user auth, Bootstrap 5 via CDN. New `web/` package reads from existing `listings.db` via new methods added to `core/database.py`.

**Tech Stack:** FastAPI 0.115, Uvicorn 0.34, Jinja2 3.1, itsdangerous 2.2, python-multipart 0.0.20, Bootstrap 5 (CDN)

---

### Task 1: Add dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Add new packages**

Append to `requirements.txt`:
```
fastapi==0.115.12
uvicorn==0.34.0
jinja2==3.1.6
itsdangerous==2.2.0
python-multipart==0.0.20
```

**Step 2: Install**

```bash
pip install fastapi==0.115.12 uvicorn==0.34.0 jinja2==3.1.6 itsdangerous==2.2.0 python-multipart==0.0.20
```

Expected: All packages install without errors.

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat(web): add FastAPI dashboard dependencies"
```

---

### Task 2: web/auth.py + tests

**Files:**
- Create: `web/__init__.py`
- Create: `web/auth.py`
- Create: `tests/test_web_auth.py`

**Step 1: Create web/__init__.py (empty)**

```python
```

**Step 2: Write failing tests**

Create `tests/test_web_auth.py`:

```python
# tests/test_web_auth.py
import os
import pytest
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
```

**Step 3: Run to verify FAIL**

```bash
pytest tests/test_web_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'web'`

**Step 4: Create web/auth.py**

```python
# web/auth.py
import os
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request


def _serializer() -> URLSafeSerializer:
    secret = os.getenv("SECRET_KEY", "dev-secret-change-me")
    return URLSafeSerializer(secret, salt="session")


def make_session_cookie(username: str) -> str:
    return _serializer().dumps({"user": username})


def get_current_user(request: Request) -> str | None:
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        data = _serializer().loads(token)
        return data.get("user")
    except BadSignature:
        return None


def check_credentials(username: str, password: str) -> bool:
    expected_user = os.getenv("DASHBOARD_USER", "admin")
    expected_pass = os.getenv("DASHBOARD_PASSWORD", "changeme")
    return username == expected_user and password == expected_pass
```

**Step 5: Run tests to verify PASS**

```bash
pytest tests/test_web_auth.py -v
```

Expected: 5 passed.

**Step 6: Commit**

```bash
git add web/__init__.py web/auth.py tests/test_web_auth.py
git commit -m "feat(web): auth module with session cookie and credential check"
```

---

### Task 3: Dashboard DB queries + tests

**Files:**
- Modify: `core/database.py` (add 5 methods after `get_scrape_logs`)
- Modify: `tests/test_database.py` (add tests at end)

**Step 1: Write failing tests**

Add to `tests/test_database.py`:

```python
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
```

**Step 2: Run to verify FAIL**

```bash
pytest tests/test_database.py -v -k "dashboard or per_source or all_sources or filtered or recent_scrape"
```

Expected: `AttributeError: 'Database' object has no attribute 'get_dashboard_stats'`

**Step 3: Add methods to core/database.py**

Add after the existing `get_scrape_logs` method (line ~151):

```python
def get_dashboard_stats(self) -> dict:
    row = self.conn.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN notified_at IS NOT NULL THEN 1 ELSE 0 END) AS notified,
            SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) AS active,
            COUNT(DISTINCT source) AS sources
        FROM listings
    """).fetchone()
    return dict(row)

def get_per_source_stats(self) -> List[dict]:
    rows = self.conn.execute("""
        SELECT
            source,
            COUNT(*) AS total,
            SUM(CASE WHEN notified_at IS NOT NULL THEN 1 ELSE 0 END) AS notified,
            MAX(last_seen_at) AS last_seen
        FROM listings
        GROUP BY source
        ORDER BY total DESC
    """).fetchall()
    return [dict(r) for r in rows]

def get_all_sources(self) -> List[str]:
    rows = self.conn.execute(
        "SELECT DISTINCT source FROM listings ORDER BY source"
    ).fetchall()
    return [r[0] for r in rows]

def get_listings_filtered(
    self,
    source: Optional[str] = None,
    disposition: Optional[str] = None,
    max_price: Optional[int] = None,
    unnotified_only: bool = False,
    page: int = 1,
    per_page: int = 50,
) -> tuple:
    """Returns (listings, total_count)."""
    where = ["1=1"]
    params: List = []
    if source:
        where.append("source = ?")
        params.append(source)
    if disposition:
        where.append("size_category = ?")
        params.append(disposition)
    if max_price is not None:
        where.append("(price IS NULL OR price <= ?)")
        params.append(max_price)
    if unnotified_only:
        where.append("notified_at IS NULL")
    clause = " AND ".join(where)
    total = self.conn.execute(
        f"SELECT COUNT(*) FROM listings WHERE {clause}", params
    ).fetchone()[0]
    offset = (page - 1) * per_page
    rows = self.conn.execute(
        f"SELECT * FROM listings WHERE {clause} "
        f"ORDER BY first_seen_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()
    return [self._row_to_listing(r) for r in rows], total

def get_recent_scrape_logs(self, limit: int = 20) -> List[dict]:
    rows = self.conn.execute(
        "SELECT * FROM scrape_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]
```

> **Note:** The existing `get_scrape_logs(source, limit)` method on line ~146 filters by source. The new `get_recent_scrape_logs(limit)` is a separate method that returns logs across all sources. Both coexist.

**Step 4: Run tests to verify PASS**

```bash
pytest tests/test_database.py -v
```

Expected: All tests pass (existing + new).

**Step 5: Commit**

```bash
git add core/database.py tests/test_database.py
git commit -m "feat(web): add dashboard DB query methods"
```

---

### Task 4: web/app.py + route tests

**Files:**
- Create: `web/app.py`
- Create: `tests/test_web_app.py`

**Step 1: Write failing tests**

Create `tests/test_web_app.py`:

```python
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
    resp = client.get("/dashboard", cookies={"session": session})
    assert resp.status_code == 200


def test_authenticated_listings_returns_200(client):
    login = client.post("/login", data={"username": "admin", "password": "secret"},
                        follow_redirects=False)
    session = login.cookies["session"]
    resp = client.get("/listings", cookies={"session": session})
    assert resp.status_code == 200


def test_logout_clears_cookie(client):
    login = client.post("/login", data={"username": "admin", "password": "secret"},
                        follow_redirects=False)
    session = login.cookies["session"]
    resp = client.post("/logout", cookies={"session": session})
    assert resp.status_code == 302
    # Cookie should be deleted (empty value or absent)
    assert resp.cookies.get("session", "") == ""
```

**Step 2: Run to verify FAIL**

```bash
pytest tests/test_web_app.py -v
```

Expected: `ModuleNotFoundError: No module named 'web.app'`

**Step 3: Create web/app.py**

```python
# web/app.py
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.database import Database
from web.auth import check_credentials, get_current_user, make_session_cookie

app = FastAPI(title="BytoHled Dashboard")
_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _from_json(value) -> list:
    if not value:
        return []
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []


templates.env.filters["from_json"] = _from_json


def _get_db() -> Database:
    return Database(os.getenv("DB_PATH", "listings.db"))


# --- Auth routes ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/dashboard"):
    if get_current_user(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(
        "login.html", {"request": request, "next": next, "error": None}
    )


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    next: str = Form(default="/dashboard"),
):
    if check_credentials(username, password):
        target = next if next.startswith("/") else "/dashboard"
        response = RedirectResponse(target, status_code=302)
        response.set_cookie("session", make_session_cookie(username),
                            httponly=True, samesite="lax")
        return response
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next, "error": "Nesprávné jméno nebo heslo"},
        status_code=401,
    )


@app.post("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session")
    return response


# --- App routes ---

@app.get("/", response_class=RedirectResponse)
async def index():
    return RedirectResponse("/dashboard", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/login?next=/dashboard", status_code=302)
    db = _get_db()
    try:
        stats = db.get_dashboard_stats()
        per_source = db.get_per_source_stats()
        logs = db.get_recent_scrape_logs(limit=20)
    finally:
        db.close()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": stats, "per_source": per_source, "logs": logs},
    )


@app.get("/listings", response_class=HTMLResponse)
async def listings(
    request: Request,
    source: str = "",
    disposition: str = "",
    max_price: Optional[int] = None,
    unnotified: bool = False,
    page: int = 1,
):
    if not get_current_user(request):
        return RedirectResponse("/login?next=/listings", status_code=302)
    db = _get_db()
    try:
        all_sources = db.get_all_sources()
        items, total = db.get_listings_filtered(
            source=source or None,
            disposition=disposition or None,
            max_price=max_price,
            unnotified_only=unnotified,
            page=page,
        )
    finally:
        db.close()
    per_page = 50
    total_pages = max(1, (total + per_page - 1) // per_page)
    return templates.TemplateResponse(
        "listings.html",
        {
            "request": request,
            "listings": items,
            "sources": all_sources,
            "filters": {
                "source": source,
                "disposition": disposition,
                "max_price": max_price,
                "unnotified": unnotified,
            },
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )
```

**Step 4: Run tests to verify PASS**

```bash
pytest tests/test_web_app.py -v
```

Expected: All 9 tests pass.

**Step 5: Commit**

```bash
git add web/app.py tests/test_web_app.py
git commit -m "feat(web): FastAPI app with auth, dashboard, and listings routes"
```

---

### Task 5: HTML templates

**Files:**
- Create: `web/templates/base.html`
- Create: `web/templates/login.html`
- Create: `web/templates/dashboard.html`
- Create: `web/templates/listings.html`

> No unit tests for templates — they are covered by route tests returning HTTP 200. Verify visually after.

**Step 1: Create web/templates/base.html**

```html
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BytoHled {% block title %}{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="/dashboard">🏠 BytoHled</a>
    <div class="navbar-nav ms-auto align-items-center">
      <a class="nav-link {% if request.url.path == '/dashboard' %}active{% endif %}" href="/dashboard">Dashboard</a>
      <a class="nav-link {% if request.url.path == '/listings' %}active{% endif %}" href="/listings">Inzeráty</a>
      <form method="post" action="/logout" class="d-inline ms-2">
        <button class="btn btn-outline-light btn-sm">Odhlásit</button>
      </form>
    </div>
  </div>
</nav>
<div class="container-fluid mt-4 px-4">
  {% block content %}{% endblock %}
</div>
</body>
</html>
```

**Step 2: Create web/templates/login.html**

```html
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BytoHled — Přihlášení</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container">
  <div class="row justify-content-center mt-5">
    <div class="col-md-4">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h4 class="card-title mb-4">🏠 BytoHled</h4>
          {% if error %}
          <div class="alert alert-danger py-2">{{ error }}</div>
          {% endif %}
          <form method="post" action="/login">
            <input type="hidden" name="next" value="{{ next }}">
            <div class="mb-3">
              <label class="form-label">Uživatelské jméno</label>
              <input type="text" name="username" class="form-control" required autofocus>
            </div>
            <div class="mb-3">
              <label class="form-label">Heslo</label>
              <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Přihlásit se</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
```

**Step 3: Create web/templates/dashboard.html**

```html
{% extends "base.html" %}
{% block title %}— Dashboard{% endblock %}
{% block content %}
<h4 class="mb-4">Dashboard</h4>

<div class="row g-3 mb-4">
  <div class="col-6 col-md-3">
    <div class="card text-center border-0 bg-primary text-white">
      <div class="card-body py-3">
        <div class="fs-1 fw-bold">{{ stats.total }}</div>
        <div class="small">Celkem inzerátů</div>
      </div>
    </div>
  </div>
  <div class="col-6 col-md-3">
    <div class="card text-center border-0 bg-success text-white">
      <div class="card-body py-3">
        <div class="fs-1 fw-bold">{{ stats.notified }}</div>
        <div class="small">Notifikováno</div>
      </div>
    </div>
  </div>
  <div class="col-6 col-md-3">
    <div class="card text-center border-0 bg-info text-white">
      <div class="card-body py-3">
        <div class="fs-1 fw-bold">{{ stats.active }}</div>
        <div class="small">Aktivních</div>
      </div>
    </div>
  </div>
  <div class="col-6 col-md-3">
    <div class="card text-center border-0 bg-secondary text-white">
      <div class="card-body py-3">
        <div class="fs-1 fw-bold">{{ stats.sources }}</div>
        <div class="small">Zdrojů</div>
      </div>
    </div>
  </div>
</div>

<div class="row g-4">
  <div class="col-md-5">
    <h6>Statistiky per zdroj</h6>
    <table class="table table-sm table-bordered">
      <thead class="table-light">
        <tr><th>Zdroj</th><th>Celkem</th><th>Notif.</th><th>Poslední scrape</th></tr>
      </thead>
      <tbody>
        {% for row in per_source %}
        <tr>
          <td><code>{{ row.source }}</code></td>
          <td>{{ row.total }}</td>
          <td>{{ row.notified }}</td>
          <td class="text-muted small">{{ (row.last_seen or "–")[:16] }}</td>
        </tr>
        {% else %}
        <tr><td colspan="4" class="text-muted">Žádná data</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="col-md-7">
    <h6>Poslední scrape logy</h6>
    <table class="table table-sm table-bordered">
      <thead class="table-light">
        <tr><th>Zdroj</th><th>Čas</th><th>Nalezeno</th><th>Nových</th><th>Chyba</th></tr>
      </thead>
      <tbody>
        {% for log in logs %}
        <tr class="{{ 'table-danger' if log.error else '' }}">
          <td><code>{{ log.source }}</code></td>
          <td class="small text-muted">{{ (log.finished_at or log.started_at or "")[:16] }}</td>
          <td>{{ log.listings_found }}</td>
          <td>{{ log.new_listings }}</td>
          <td class="small text-danger">{{ log.error or "" }}</td>
        </tr>
        {% else %}
        <tr><td colspan="5" class="text-muted">Žádné logy</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
```

**Step 4: Create web/templates/listings.html**

```html
{% extends "base.html" %}
{% block title %}— Inzeráty{% endblock %}
{% block content %}
<h4 class="mb-3">Inzeráty <span class="badge bg-secondary">{{ total }}</span></h4>

<form method="get" class="row g-2 mb-4 align-items-end">
  <div class="col-auto">
    <label class="form-label small">Zdroj</label>
    <select name="source" class="form-select form-select-sm">
      <option value="">Všechny</option>
      {% for s in sources %}
      <option value="{{ s }}" {% if s == filters.source %}selected{% endif %}>{{ s }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-auto">
    <label class="form-label small">Dispozice</label>
    <select name="disposition" class="form-select form-select-sm">
      <option value="">Všechny</option>
      {% for d in ["1+1", "1+kk"] %}
      <option value="{{ d }}" {% if d == filters.disposition %}selected{% endif %}>{{ d }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-auto">
    <label class="form-label small">Max. cena (Kč)</label>
    <input type="number" name="max_price" class="form-control form-control-sm" style="width:130px"
           value="{{ filters.max_price or '' }}" placeholder="např. 2500000">
  </div>
  <div class="col-auto">
    <div class="form-check mt-4">
      <input type="checkbox" name="unnotified" value="true" class="form-check-input"
             id="unnotified" {% if filters.unnotified %}checked{% endif %}>
      <label class="form-check-label small" for="unnotified">Jen nenotifikované</label>
    </div>
  </div>
  <div class="col-auto">
    <button type="submit" class="btn btn-primary btn-sm">Filtrovat</button>
    <a href="/listings" class="btn btn-outline-secondary btn-sm ms-1">Reset</a>
  </div>
</form>

<div class="table-responsive">
  <table class="table table-sm table-hover table-bordered align-middle">
    <thead class="table-light">
      <tr>
        <th style="width:70px">Foto</th>
        <th>Titulek</th>
        <th>Cena</th>
        <th>Dispoziace</th>
        <th>Lokalita</th>
        <th>Zdroj</th>
        <th>Nalezeno</th>
        <th>Notif.</th>
      </tr>
    </thead>
    <tbody>
      {% for listing in listings %}
      {% set images = listing.images_json | from_json %}
      <tr>
        <td>
          {% if images %}
          <img src="{{ images[0] }}" width="64" height="48" style="object-fit:cover;border-radius:4px" loading="lazy">
          {% else %}
          <span class="text-muted small">—</span>
          {% endif %}
        </td>
        <td>
          <a href="{{ listing.url }}" target="_blank" rel="noopener">
            {{ listing.title or "—" }}
          </a>
        </td>
        <td class="text-nowrap">
          {% if listing.price %}
          {{ "{:,}".format(listing.price).replace(",", " ") }} Kč
          {% else %}
          <span class="text-muted">—</span>
          {% endif %}
        </td>
        <td>{{ listing.size_category or "—" }}</td>
        <td class="small text-muted">{{ listing.location or "—" }}</td>
        <td><code class="small">{{ listing.source }}</code></td>
        <td class="small text-muted text-nowrap">{{ (listing.first_seen_at | string)[:16] if listing.first_seen_at else "—" }}</td>
        <td class="text-center">
          {% if listing.notified_at %}
          <span class="text-success">✓</span>
          {% else %}
          <span class="text-muted">—</span>
          {% endif %}
        </td>
      </tr>
      {% else %}
      <tr><td colspan="8" class="text-center text-muted py-4">Žádné inzeráty</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% if total_pages > 1 %}
<nav>
  <ul class="pagination pagination-sm">
    {% for p in range(1, total_pages + 1) %}
    <li class="page-item {% if p == page %}active{% endif %}">
      <a class="page-link" href="?source={{ filters.source }}&disposition={{ filters.disposition }}&max_price={{ filters.max_price or '' }}&unnotified={{ 'true' if filters.unnotified else '' }}&page={{ p }}">{{ p }}</a>
    </li>
    {% endfor %}
  </ul>
</nav>
{% endif %}

{% endblock %}
```

**Step 5: Run full test suite to verify nothing broken**

```bash
pytest -v
```

Expected: All tests pass (existing + new).

**Step 6: Commit**

```bash
git add web/templates/
git commit -m "feat(web): HTML templates for login, dashboard, and listings"
```

---

### Task 6: Update .env and verify

**Files:**
- Modify: `.env`
- Modify: `README.md` (add dashboard section)

**Step 1: Add dashboard vars to .env**

Append to `.env`:
```
# Dashboard
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=changeme
SECRET_KEY=change-this-to-a-random-string
```

> **Important:** Change `DASHBOARD_PASSWORD` and `SECRET_KEY` to real values before deploying.

**Step 2: Run full test suite**

```bash
pytest -v
```

Expected: All tests pass.

**Step 3: Start the dashboard locally and verify in browser**

```bash
uvicorn web.app:app --reload --port 8000
```

Visit `http://localhost:8000` — should redirect to `/login`. Log in with credentials from `.env`. Verify:
- Dashboard shows stats cards and scrape logs
- Listings page shows table with filters
- Logout works

**Step 4: Commit**

```bash
git add .env README.md
git commit -m "feat(web): dashboard credentials in .env, README updated"
```

---

## Running the Dashboard

```bash
# Terminal 1: scraper daemon
python main.py --daemon

# Terminal 2: web dashboard
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

## Deploy (Railway / Fly.io)

Add env vars: `DASHBOARD_USER`, `DASHBOARD_PASSWORD`, `SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
Start command: `uvicorn web.app:app --host 0.0.0.0 --port $PORT`
