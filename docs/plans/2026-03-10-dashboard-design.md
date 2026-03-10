# BytoHled Web Dashboard — Design

**Goal:** Add a FastAPI web dashboard to BytoHled for browsing scraped listings, viewing statistics, and monitoring scrape activity. Deployed online with single-user authentication.

**Architecture:** FastAPI + Jinja2 server-rendered HTML. Bootstrap 5 via CDN. Session cookie auth using itsdangerous. Reads from existing `listings.db` SQLite via existing `core/database.py`.

**Tech Stack:** FastAPI, Uvicorn, Jinja2, itsdangerous, Bootstrap 5 (CDN)

---

## File Structure

```
bytohled/
├── web/
│   ├── __init__.py
│   ├── app.py              # FastAPI app, all routes
│   ├── auth.py             # session cookie helpers, login check
│   └── templates/
│       ├── base.html       # layout: navbar, Bootstrap 5 CDN
│       ├── login.html      # username/password form
│       ├── dashboard.html  # stats cards + scrape log table
│       └── listings.html   # listings table with filters
├── requirements.txt        # + fastapi, uvicorn, jinja2, itsdangerous
└── .env                    # + DASHBOARD_USER, DASHBOARD_PASSWORD
```

## Authentication

- Hardcoded single user via `.env`: `DASHBOARD_USER`, `DASHBOARD_PASSWORD`
- POST `/login` verifies credentials, sets signed session cookie (itsdangerous `URLSafeSerializer`)
- All routes check cookie; redirect to `/login` if missing/invalid
- POST `/logout` clears cookie, redirects to `/login`
- No registration, no password hashing needed (single trusted user, private app)

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/login` | Login form |
| POST | `/login` | Verify credentials, set cookie, redirect `/dashboard` |
| POST | `/logout` | Clear cookie, redirect `/login` |
| GET | `/` | Redirect to `/dashboard` |
| GET | `/dashboard` | Stats cards + scrape logs |
| GET | `/listings` | Listings table with filters |

## Pages

### `/dashboard`
- **Stats cards (top row):** Total listings | Notified | Active | Sources count
- **Per-source breakdown table:** source name | total | notified | last scraped
- **Recent scrape logs table:** source | started_at | finished_at | found | new | error

### `/listings`
- **Filter bar (GET params):**
  - `source` — dropdown (all sources from DB)
  - `disposition` — dropdown (1+1, 1+kk, empty=all)
  - `max_price` — number input
  - `notified` — checkbox (only unnotified)
- **Table columns:** thumbnail | title | price | disposition | location | source | first_seen | notified ✓/✗ | link
- **Pagination:** 50 per page, `?page=N`

### `/login`
- Username + password form
- Error message on failed login
- Redirect to original URL after login (via `next` param)

## Deployment

- Run with: `uvicorn web.app:app --host 0.0.0.0 --port 8000`
- Deploy to Railway / Fly.io / any VPS with Python
- Scraper (`main.py --daemon`) and web server run as separate processes
- Both share `listings.db` (WAL mode already enabled)

## New Dependencies

```
fastapi==0.115.12
uvicorn==0.34.0
jinja2==3.1.6
itsdangerous==2.2.0
python-multipart==0.0.20
```
