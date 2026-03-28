# BytoHled v2 — Design

**Datum:** 2026-03-28
**Cíl:** Modulární scraper realitních inzerátů s unified datovým modelem, veřejným Next.js dashboardem na Vercelu a Telegram notifikacemi.

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
- `supabase/` — schéma DB, migrace
- `dashboard/` — Next.js/TypeScript, Vercel, čte ze Supabase

**Tok dat:**
1. GitHub Actions spouští scrapery každých 30 minut
2. Každý scraper vrací seznam `Listing` objektů (jednotný formát)
3. Runner porovná s DB — nové záznamy uloží + pošle Telegram notifikaci
4. Existující záznamy — zkontroluje aktivitu (HTTP HEAD na URL inzerátu)
5. Next.js dashboard čte přímo ze Supabase přes API routes

---

## Infrastruktura

| Komponenta | Platforma | Cena |
|---|---|---|
| Scrapery | GitHub Actions (cron) | zdarma |
| Databáze | Supabase PostgreSQL | zdarma (500 MB) |
| Fotografie | Supabase Storage | zdarma (1 GB) |
| Dashboard | Vercel (Next.js) | zdarma |
| Notifikace | Telegram Bot API | zdarma |

**GitHub Actions secrets:** `SUPABASE_URL`, `SUPABASE_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
**Vercel env:** `SUPABASE_URL`, `SUPABASE_KEY`

**Cron schedule:** `*/30 * * * *` + `workflow_dispatch` pro ruční spuštění

---

## Datový model

### Tabulka `listings`

```sql
CREATE TABLE listings (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id     TEXT NOT NULL,
  source          TEXT NOT NULL,
  url             TEXT NOT NULL,
  title           TEXT,
  price           INTEGER,
  price_type      TEXT CHECK (price_type IN ('sale', 'rent')),
  disposition     TEXT,
  area_m2         INTEGER,
  address         TEXT,
  description     TEXT,
  images          TEXT[],
  is_active       BOOLEAN DEFAULT true,
  first_seen_at   TIMESTAMPTZ DEFAULT now(),
  last_checked_at TIMESTAMPTZ DEFAULT now(),
  notified_at     TIMESTAMPTZ,
  is_favorite     BOOLEAN DEFAULT false,
  note            TEXT,

  UNIQUE (external_id, source)
);
```

**Klíčová rozhodnutí:**
- `external_id + source` = unikátní klíč pro deduplikaci
- `images` — fotky se stáhnou a uloží do Supabase Storage (stálé URL)
- `is_active` — runner periodicky kontroluje HTTP status URL inzerátu
- `is_favorite` a `note` — editovatelné z dashboardu (PATCH API)
- `price_type` — rozlišení prodej / pronájem

---

## Architektura scraperů

### Struktura složek

```
scrapers/
├── base.py                  # BaseScraper + Listing dataclass
├── runner.py                # orchestrátor
├── sreality/
│   ├── scraper.py
│   ├── parser.py
│   └── config.yaml
├── bezrealitky/
│   ├── scraper.py
│   ├── parser.py
│   └── config.yaml
├── bazos/
│   ├── scraper.py
│   ├── parser.py
│   └── config.yaml
└── [dalsi_web]/
    └── ...
```

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
    images: list[str]        # původní URL fotek (runner je stáhne do Storage)
```

### `BaseScraper`

```python
class BaseScraper:
    def fetch_listings(self) -> list[Listing]:
        raise NotImplementedError
```

Retry logika, timeouty, User-Agent rotation — v `BaseScraper`, ne v jednotlivých scraperech.

### `runner.py` — logika

1. Spustí všechny enabled scrapery (izolovaně, chyba jednoho nezastaví ostatní)
2. Pro každý `Listing`:
   - Zkontroluje `external_id + source` v DB
   - Nový → uloží, stáhne fotky do Storage, pošle Telegram
   - Existující → aktualizuje `last_checked_at`
3. Periodicky (každých N cyklů) zkontroluje `is_active` starých inzerátů (HTTP HEAD)

### Lokality (config.yaml pro každý scraper)

- Ostrava a okolí
- Frýdek-Místek a okolí
- Frýdlant nad Ostravicí
- Ostravice
- Čeladná

### Typy

- Prodej i pronájem (`price_type: 'sale' | 'rent'`)

---

## Next.js Dashboard

### Struktura

```
dashboard/
├── app/
│   ├── page.tsx                      # redirect → /listings
│   ├── listings/
│   │   └── page.tsx                  # hlavní přehled
│   ├── listing/[id]/
│   │   └── page.tsx                  # detail inzerátu
│   └── api/
│       ├── listings/route.ts         # GET s filtry + stránkování
│       └── listing/[id]/route.ts     # PATCH (hvězdička, poznámka)
├── components/
│   ├── ListingCard.tsx
│   ├── ListingTable.tsx
│   ├── FilterBar.tsx
│   └── FavoriteButton.tsx
└── lib/
    └── supabase.ts                   # Supabase client
```

### Stránka `/listings`

- **Filtrační lišta:** zdroj | dispozice | typ (prodej/pronájem) | max. cena | pouze aktivní | pouze oblíbené
- **Zobrazení:** tabulka nebo karty (foto, název, cena, dispozice, plocha, adresa, zdroj, datum, aktivní ✓/✗, ⭐)
- **Stránkování:** 50 inzerátů na stránku
- Klik na řádek/kartu → detail

### Stránka `/listing/[id]`

- Fotogalerie
- Všechny parametry inzerátu
- Toggle ⭐ oblíbené
- Textové pole pro poznámku (auto-save při opuštění pole)
- Odkaz na původní inzerát (nová záložka)
- Příznak aktivní/neaktivní

### Autentizace

- Username/password přes env proměnné (`DASHBOARD_USER`, `DASHBOARD_PASSWORD`)
- Session cookie (Next.js middleware)
- Redirect na `/login` pro nepřihlášené

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
- Neaktivní inzeráty → žádná notifikace (jen příznak v DB)
- Inline buttony: odkaz na inzerát + odkaz na dashboard detail

---

## Rozšiřitelnost

Přidání nového scraperu:
1. Vytvořit složku `scrapers/<web>/`
2. Implementovat `scraper.py` (dědí `BaseScraper`, implementuje `fetch_listings()`)
3. Implementovat `parser.py` (parsuje odpověď → `Listing`)
4. Vytvořit `config.yaml` s URL a parametry
5. Zaregistrovat v `runner.py`

Každý scraper lze spustit a ladit samostatně bez závislosti na ostatních.
