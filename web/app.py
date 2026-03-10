# web/app.py
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.database import Database
from web.auth import check_credentials, get_current_user, make_session_cookie

app = FastAPI(title="BytoHled Dashboard")
_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _from_json(value: str | None) -> list:
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
        request, "login.html", {"next": next, "error": None}
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
        request, "login.html",
        {"next": next, "error": "Nesprávné jméno nebo heslo"},
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
        request, "dashboard.html",
        {"stats": stats, "per_source": per_source, "logs": logs},
    )


@app.get("/listings", response_class=HTMLResponse)
async def listings(
    request: Request,
    source: str = "",
    disposition: str = "",
    max_price: Optional[int] = Query(default=None, ge=0),
    unnotified: bool = False,
    page: int = Query(default=1, ge=1),
):
    if not get_current_user(request):
        return RedirectResponse("/login?next=/listings", status_code=302)
    db = _get_db()
    try:
        all_sources = db.get_all_sources()
        all_dispositions = db.get_all_dispositions()
        per_page = 50
        items, total = db.get_listings_filtered(
            source=source or None,
            disposition=disposition or None,
            max_price=max_price,
            unnotified_only=unnotified,
            page=page,
            per_page=per_page,
        )
    finally:
        db.close()
    total_pages = max(1, (total + per_page - 1) // per_page)
    return templates.TemplateResponse(
        request, "listings.html",
        {
            "listings": items,
            "sources": all_sources,
            "dispositions": all_dispositions,
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
