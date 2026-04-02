-- BytoHled v2 schema
-- Spustit v Supabase: Dashboard → SQL Editor → New query

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
  images          TEXT[] DEFAULT '{}',
  is_active       BOOLEAN DEFAULT true,
  first_seen_at   TIMESTAMPTZ DEFAULT now(),
  last_checked_at TIMESTAMPTZ DEFAULT now(),
  notified_at     TIMESTAMPTZ,
  is_favorite     BOOLEAN DEFAULT false,
  note            TEXT,

  UNIQUE (external_id, source)
);

-- Indexy
CREATE INDEX idx_listings_active_date ON listings (is_active, first_seen_at DESC);
CREATE INDEX idx_listings_source ON listings (source);
CREATE INDEX idx_listings_favorite ON listings (is_favorite) WHERE is_favorite = true;

-- Row Level Security
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;

-- Veřejné čtení přes anon key (dashboard používá session auth, ne Supabase auth)
CREATE POLICY "allow_select" ON listings
  FOR SELECT USING (true);

-- Zápis a update jen přes service role key (scrapery + dashboard API routes)
-- Service role automaticky obchází RLS — žádná další policy není potřeba.

-- ---------------------------------------------------------------------------
-- Tabulka pro historii scrapingu
-- ---------------------------------------------------------------------------
CREATE TABLE scrape_logs (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scraped_at       TIMESTAMPTZ DEFAULT now(),
  added_count      INTEGER DEFAULT 0,
  deactivated_count INTEGER DEFAULT 0
);

CREATE INDEX idx_scrape_logs_scraped_at ON scrape_logs (scraped_at DESC);

-- Veřejné čtení přes anon key (dashboard)
ALTER TABLE scrape_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_select_scrape_logs" ON scrape_logs FOR SELECT USING (true);
