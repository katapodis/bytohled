# BytoHled — RealitníBot Ostrava 🏠

Automatický monitoring realitních inzerátů v Ostravě. Sleduje Sreality.cz, Bezrealitky.cz, Reality.cz, Bazoš.cz a vybrané místní RK. Notifikuje přes Telegram a Email.

## Funkce

- Hledá byty 1+1 a 1+KK v Ostravě do 2 500 000 Kč
- Deduplikace — každý inzerát notifikuje pouze jednou
- Odolné vůči chybám — výpadek jednoho scraperu nezastaví ostatní
- Nasazení zdarma přes GitHub Actions (spouští každých 20 minut)

## Rychlý start

### 1. Forkni/klonuj repozitář

```bash
git clone <repo-url> && cd bytohled
```

### 2. Nastav GitHub Secrets

Přejdi na: `Settings → Secrets and variables → Actions → New repository secret`

| Secret | Popis |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | Token od [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Tvoje chat ID (zjistit přes [@userinfobot](https://t.me/userinfobot)) |
| `SMTP_HOST` | SMTP server (např. `smtp.gmail.com`) |
| `SMTP_PORT` | Port (`587` pro STARTTLS, `465` pro SSL) |
| `SMTP_USER` | Emailová adresa odesílatele |
| `SMTP_PASSWORD` | Heslo nebo [App Password](https://myaccount.google.com/apppasswords) (Gmail) |
| `EMAIL_FROM` | Odesílací adresa |
| `EMAIL_TO` | Adresa pro příjem notifikací |
| `DASHBOARD_USER` | Dashboard login username |
| `DASHBOARD_PASSWORD` | Dashboard login password |
| `SECRET_KEY` | Session cookie signing key (generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`) |

### 3. Uprav config.yaml (volitelné)

Změň kritéria vyhledávání v `config.yaml` — lokalita, dispozice, max. cena.

### 4. První spuštění

Spusť workflow ručně: `Actions → RealitniBot Scraper → Run workflow`

---

## Lokální vývoj

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # vyplň tokeny
python main.py --once  # jeden cyklus
python main.py --daemon  # daemon (každých 20 min)
```

### Testy

```bash
pytest tests/ -v
```

---

## Web Dashboard

Webové rozhraní pro prohlížení nalezených inzerátů.

### Spuštění

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

### Spuštění scraperů i dashboardu současně

```bash
# Terminal 1 – scraper daemon
python main.py --daemon

# Terminal 2 – web dashboard
uvicorn web.app:app --reload --port 8000
```

Otevři prohlížeč na: http://localhost:8000

---

## Struktura projektu

```
bytohled/
├── main.py                  # vstupní bod
├── config.yaml              # kritéria hledání
├── .env.example             # šablona proměnných prostředí
├── requirements.txt
├── .github/workflows/       # GitHub Actions
├── scrapers/                # scrapery (jeden soubor = jeden zdroj)
│   ├── base.py              # abstraktní BaseScraper
│   ├── sreality.py          # Sreality.cz (JSON API)
│   ├── bezrealitky.py       # Bezrealitky.cz (REST API)
│   ├── reality_cz.py        # Reality.cz (HTML)
│   ├── bazos.py             # Bazoš.cz (HTML)
│   ├── facebook.py          # Facebook (stub)
│   └── local_agency.py      # generický scraper pro RK
├── core/
│   ├── database.py          # SQLite persistence
│   ├── filter.py            # filtrování inzerátů
│   └── runner.py            # orchestrace
├── notifications/
│   ├── telegram.py          # Telegram Bot API
│   └── email_notifier.py    # SMTP email
└── web/
    └── app.py               # FastAPI web dashboard
```

## Zdroje dat

| Zdroj | Metoda | Stav |
|-------|--------|------|
| Sreality.cz | JSON API | ✅ Aktivní |
| Bezrealitky.cz | REST API | ✅ Aktivní |
| Reality.cz | HTML scraping | ✅ Aktivní |
| Bazoš.cz | HTML scraping | ✅ Aktivní |
| Lokální RK | HTML scraping (generický) | ✅ Aktivní |
| Facebook | Stub | ⚠️ Není implementováno |

## Omezení

- **GitHub Actions Free:** 2 000 min/měsíc pro soukromé repo. Doporučeno: **veřejné repo** (neomezené minuty; tokeny jsou v Secrets, tedy v bezpečí).
- **Databáze:** SQLite v Actions Cache s TTL 7 dní. Při smazání cache přijdou duplikátní notifikace za starší inzeráty — akceptovatelné chování.
- **Facebook:** Modul je stub — Facebook aktivně blokuje scrapování.
- **HTML scrapery:** Selektory (Reality.cz, Bazoš.cz, RK) mohou přestat fungovat při změně designu stránek.
