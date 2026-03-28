# BytoHled v2 — Design

**Datum:** 2026-03-28
**Cíl:** Modulární scraper realitních inzerátů s unified datovým modelem, veřejným Next.js dashboardem na Vercelu a Telegram notifikacemi.

> **Poznámka:** Toto je kompletní přepis. Žádná migrace starých dat. SQLite a předchozí kód jsou smazány.

---

## Architektura systému

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions (cron)               │
│                                                      │
│  scrapers/                                           │
│    sreality/   bezrealitky/   bazos/   [další...]    │
│         │            │          │                    │
│         └────────────┴──────────┘                   │
│                      │                               │
│              Normalizace → Listing                   │
│                      │                               │
│              Zápis do Supabase                       │
│              Telegram notifikace                     │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │    Supabase     │
              │  PostgreSQL DB  │
              │  Storage (foto) │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │     Vercel      │
              │  Next.js app    │
              │  Dashboard UI   │
              └─────────────────┘
```

**Tři nezávislé části:**
- `scrapers/` — Python, GitHub Actions, bez závislosti na dashboardu
- `supabase/` — schéma DB, SQL migrace
- `dashboard/` — Next.js 15 / TypeScript, Vercel, čte ze Supabase

**Tok dat:**
1. GitHub Actions spouští scrapery každých 30 minut
2. Každý scraper vrací seznam `Listing` objektů (jednotný formát)
3. Runner porovná s DB — nové záznamy uloží + stáhne fotky + pošle Telegram
4. Existující záznamy — zkontroluje aktivitu (HTTP HEAD na URL) pokud `last_checked_at` > 24h
5. Next.js dashboard čte ze Supabase přes server-side API routes

---

## Infrastruktura

| Komponenta | Platforma | Cena |
|---|---|---|
| Scrapery | GitHub Actions (cron) | zdarma |
| Databáze | Supabase PostgreSQL | zdarma (500 MB) |
| Fotografie | Supabase Storage | zdarma (1 GB) |
| Dashboard | Vercel (Next.js 15) | zdarma |
| Notifikace | Telegram Bot API | zdarma |

### Environment proměnné

**GitHub Actions secrets:**
| Proměnná | Popis |
|---|---|
| `SUPABASE_URL` | URL Supabase projektu |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (plný přístup pro scrapery) |
| `TELEGRAM_BOT_TOKEN` | Token od @BotFather |
| `TELEGRAM_CHAT_ID` | ID chatu pro notifikace |

**Vercel env proměnné:**
| Proměnná | Popis |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL Supabase projektu (veřejná) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key (read-only pro klienta) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (pro server-side PATCH) |
| `DASHBOARD_USER` | Login username |
| `DASHBOARD_PASSWORD` | Login heslo |
| `AUTH_SECRET` | Náhodný string pro podpis session cookie (min. 32 znaků) |

> **Důležité:** `SUPABASE_SERVICE_ROLE_KEY` se nikdy neposílá do browseru — jen server-side (`/api/` routes). Dashboard čte data přes `NEXT_PUBLIC_SUPABASE_ANON_KEY` (Row Level Security na Supabase: SELECT povolen všem autentizovaným přes session).

### GitHub Actions workflow

```yaml
name: Scraper

on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: python scrapers/runner.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

**Cron schedule:** `*/30 * * * *` + `workflow_dispatch` pro ruční spuštění.
Žádný cache pro soubory — stav je v Supabase.

---

## Datový model

### Tabulka `listings`

```sql
CREATE TABLE listings (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id     TEXT NOT NULL,
  source          TEXT NOT NULL,         -- 'sreality' | 'bezrealitky' | 'bazos' | ...
  url             TEXT NOT NULL,
  title           TEXT,
  price           INTEGER,               -- v Kč, NULL = neuvedena
  price_type      TEXT CHECK (price_type IN ('sale', 'rent')),
  disposition     TEXT,                  -- '1+1' | '1+kk' | '2+1' | ...
  area_m2         INTEGER,
  address         TEXT,
  description     TEXT,
  images          TEXT[],                -- Supabase Storage public URLs (po stažení)
  is_active       BOOLEAN DEFAULT true,
  first_seen_at   TIMESTAMPTZ DEFAULT now(),
  last_checked_at TIMESTAMPTZ DEFAULT now(),
  notified_at     TIMESTAMPTZ,
  is_favorite     BOOLEAN DEFAULT false,
  note            TEXT,

  UNIQUE (external_id, source)
);

-- Row Level Security
-- Povolit přihlášeným uživatelům SELECT (anon key používá RLS)
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "select_authenticated" ON listings
  FOR SELECT USING (true);  -- veřejné čtení přes anon key; zápis jen přes service role

-- Indexy
CREATE INDEX idx_listings_active_date ON listings (is_active, first_seen_at DESC);
CREATE INDEX idx_listings_source ON listings (source);
CREATE INDEX idx_listings_favorite ON listings (is_favorite) WHERE is_favorite = true;
```

**Klíčová rozhodnutí:**
- `external_id + source` = unikátní klíč pro deduplikaci
- `images` — runner stáhne fotky do Supabase Storage a uloží jejich Storage public URL (ne původní URL webu)
- `is_active` — runner kontroluje inzeráty kde `last_checked_at < now() - interval '24 hours'` (HTTP HEAD request)
- `is_favorite` a `note` — editovatelné z dashboardu (PATCH `/api/listing/[id]`)
- `price_type` — nastavuje každý scraper dle svého `config.yaml`
- `raw_data` — záměrně vynecháno (v2 je čistý start; debugging přes logy GitHub Actions)

### Supabase Storage

- Bucket: `listing-images` (public)
- Cesta: `{source}/{external_id}/{index}.jpg`
- Při selhání stažení fotky: uloží prázdné pole `images = []`, inzerát se nevynechá
- Runner aktualizuje `images` v DB až po úspěšném nahrání do Storage

---

## Architektura scraperů

### Struktura složek

```
scrapers/
├── base.py                  # BaseScraper + Listing dataclass
├── runner.py                # orchestrátor
├── db.py                    # Supabase client, insert/update/query
├── notifier.py              # Telegram notifikace
├── sreality/
│   ├── scraper.py           # fetch_listings() → list[Listing]
│   ├── parser.py            # JSON/HTML → Listing (volitelné oddělení)
│   └── config.yaml          # URL, parametry, lokality, price_type
├── bezrealitky/
│   ├── scraper.py
│   └── config.yaml
├── bazos/
│   ├── scraper.py
│   └── config.yaml
└── [dalsi_web]/
    └── ...
```

> `parser.py` je volitelný — pro jednoduché scrapery lze parsování ponechat v `scraper.py`. Oddělení je doporučené pro weby s komplexním HTML parsováním.

### `Listing` dataclass

```python
@dataclass
class Listing:
    external_id: str
    source: str
    url: str
    title: str
    price: int | None
    price_type: str          # 'sale' | 'rent'
    disposition: str | None
    area_m2: int | None
    address: str | None
    description: str | None
    images: list[str]        # původní URL fotek ze zdroje (runner je stáhne do Storage)
```

### `BaseScraper`

```python
class BaseScraper:
    def fetch_listings(self) -> list[Listing]:
        raise NotImplementedError
```

Retry logika, timeouty, User-Agent rotation — v `BaseScraper`, jednotlivé scrapery se o to nestarají.

### `config.yaml` — formát pro každý scraper

```yaml
source: sreality           # identifikátor zdroje (shoduje se s Listing.source)
price_type: sale           # 'sale' | 'rent' (weby míchající oboje → dva separátní scrapery)
locations:
  - name: "Ostrava"
    params: { ... }        # site-specific parametry
  - name: "Frýdek-Místek"
    params: { ... }
enabled: true
```

### `runner.py` — logika

1. Spustí všechny enabled scrapery (izolovaně, chyba jednoho nezastaví ostatní)
2. Pro každý `Listing`:
   - Zkontroluje `external_id + source` v DB
   - **Nový** → stáhne fotky do Supabase Storage → nahradí `Listing.images` (původní URL) za Storage public URL → uloží do DB → pošle Telegram
   - **Existující** → žádná akce (jen počítání)
3. Kontrola aktivity: dotaz `WHERE last_checked_at < now() - interval '24 hours' AND is_active = true` → HTTP HEAD na každou URL → aktualizace `is_active` a `last_checked_at`

---

## Next.js Dashboard

### Tech stack

- **Next.js 15** (App Router)
- **TypeScript**
- **Tailwind CSS v4.1** (pozor: syntax odlišná od v3, použít Context7 dokumentaci)
- **@supabase/supabase-js** pro komunikaci se Supabase
- **iron-session** pro session cookie autentizaci

### Struktura

```
dashboard/
├── app/
│   ├── page.tsx                          # redirect → /listings
│   ├── login/
│   │   └── page.tsx                      # login formulář
│   ├── listings/
│   │   └── page.tsx                      # hlavní přehled (server component)
│   ├── listing/[id]/
│   │   └── page.tsx                      # detail inzerátu
│   └── api/
│       ├── auth/
│       │   ├── login/route.ts            # POST: ověř credentials, nastav session
│       │   └── logout/route.ts           # POST: smaž session
│       ├── listings/route.ts             # GET: filtry + stránkování
│       └── listing/[id]/route.ts         # PATCH: is_favorite, note
├── components/
│   ├── ListingCard.tsx
│   ├── ListingTable.tsx
│   ├── FilterBar.tsx
│   └── FavoriteButton.tsx
├── lib/
│   ├── supabase.ts                       # server-side Supabase client
│   ├── supabase-browser.ts              # browser Supabase client (anon key)
│   └── session.ts                        # iron-session config
└── middleware.ts                          # redirect nepřihlášených → /login
```

### Autentizace (iron-session)

- `DASHBOARD_USER` + `DASHBOARD_PASSWORD` v env proměnných (single user)
- POST `/api/auth/login` ověří credentials, nastaví iron-session cookie
- `middleware.ts` chrání všechny routes kromě `/login` a `/api/auth/*`
- API routes (`/api/listing/[id]`) také ověří session před PATCH operacemi
- Cookie expiry: 7 dní, HttpOnly, Secure

### Stránka `/listings`

- **Filtrační lišta:** zdroj | dispozice | typ (prodej/pronájem) | max. cena | pouze aktivní | pouze oblíbené
- **Zobrazení:** karty (foto, název, cena, dispozice, plocha, adresa, zdroj, datum, aktivní ✓/✗, ⭐)
- **Stránkování:** 50 inzerátů na stránku
- Klik na kartu → detail

### Stránka `/listing/[id]`

- Fotogalerie
- Všechny parametry inzerátu
- Toggle ⭐ oblíbené (PATCH API)
- Textové pole pro poznámku (auto-save `onBlur`, PATCH API)
- Odkaz na původní inzerát (`target="_blank" rel="noopener noreferrer"`)
- Příznak aktivní/neaktivní

### Stránka `/login`

- Username + password formulář
- Chybová hláška při nesprávných credentials
- Redirect na `/listings` po úspěšném přihlášení

---

## Telegram notifikace

**Formát zprávy pro nový inzerát:**

```
🏠 [1+kk | 45m² | 1 850 000 Kč]
Prodej — Ostrava-Poruba

📍 Adresa: ul. Hlavní 12, Ostrava
📐 Plocha: 45 m²
💰 Cena: 1 850 000 Kč
🔗 Zdroj: Sreality.cz

[Zobrazit inzerát] [Dashboard]
```

- Jedna zpráva = jeden inzerát
- Neaktivní inzeráty → žádná notifikace (pouze příznak `is_active = false` v DB)
- Inline buttony: odkaz na původní inzerát + odkaz na dashboard detail (`/listing/{id}`)

---

## Rozšiřitelnost

Přidání nového scraperu:
1. Vytvořit složku `scrapers/<web>/`
2. Implementovat `scraper.py` — dědí `BaseScraper`, implementuje `fetch_listings() -> list[Listing]`
3. Přidat `config.yaml` s `source`, `price_type`, `locations`, `enabled`
4. Volitelně přidat `parser.py` pro oddělení parsovací logiky
5. Zaregistrovat scraper v `runner.py`

Každý scraper lze spustit izolovaně pro ladění:
```bash
python -c "from scrapers.sreality.scraper import SrealityScraper; print(SrealityScraper().fetch_listings())"
```
