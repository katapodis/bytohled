# core/database.py
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from loguru import logger


@dataclass
class Listing:
    source: str
    external_id: str
    url: str
    title: Optional[str] = None
    price: Optional[int] = None
    size_category: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    images_json: Optional[str] = None
    raw_data: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None
    is_active: bool = True


class Database:
    def __init__(self, db_path: str = "listings.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                price INTEGER,
                size_category TEXT,
                location TEXT,
                description TEXT,
                images_json TEXT,
                raw_data TEXT,
                first_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notified_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(source, external_id)
            );

            CREATE INDEX IF NOT EXISTS idx_listings_unnotified ON listings (notified_at, is_active);

            CREATE TABLE IF NOT EXISTS scrape_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                started_at DATETIME,
                finished_at DATETIME,
                listings_found INTEGER DEFAULT 0,
                new_listings INTEGER DEFAULT 0,
                error TEXT
            );
        """)
        self.conn.commit()

    def get_table_names(self) -> List[str]:
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row[0] for row in cursor.fetchall()]

    def insert_listing(self, listing: Listing) -> bool:
        """Insert listing. Returns True if new, False if duplicate."""
        try:
            now = datetime.now().isoformat()
            cursor = self.conn.execute(
                """INSERT OR IGNORE INTO listings
                   (source, external_id, url, title, price, size_category,
                    location, description, images_json, raw_data,
                    first_seen_at, last_seen_at, is_active)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    listing.source, listing.external_id, listing.url,
                    listing.title, listing.price, listing.size_category,
                    listing.location, listing.description,
                    listing.images_json, listing.raw_data,
                    now, now, int(listing.is_active),
                ),
            )
            is_new = cursor.rowcount > 0
            # Update last_seen_at for existing entries
            self.conn.execute(
                "UPDATE listings SET last_seen_at=?, is_active=1 "
                "WHERE source=? AND external_id=?",
                (now, listing.source, listing.external_id),
            )
            self.conn.commit()
            return is_new
        except Exception as e:
            logger.error(f"DB insert error: {e}")
            return False

    def get_listing_by_external_id(self, source: str, external_id: str) -> Optional[Listing]:
        row = self.conn.execute(
            "SELECT * FROM listings WHERE source=? AND external_id=?",
            (source, external_id),
        ).fetchone()
        return self._row_to_listing(row) if row else None

    def get_listings_by_source(self, source: str) -> List[Listing]:
        rows = self.conn.execute(
            "SELECT * FROM listings WHERE source=?", (source,)
        ).fetchall()
        return [self._row_to_listing(r) for r in rows]

    def get_unnotified_listings(self) -> List[Listing]:
        rows = self.conn.execute(
            "SELECT * FROM listings WHERE notified_at IS NULL AND is_active=1"
        ).fetchall()
        return [self._row_to_listing(r) for r in rows]

    def mark_notified(self, source: str, external_id: str) -> None:
        self.conn.execute(
            "UPDATE listings SET notified_at=? WHERE source=? AND external_id=?",
            (datetime.now().isoformat(), source, external_id),
        )
        self.conn.commit()

    def log_scrape(self, source: str, started_at: datetime,
                   finished_at: datetime, listings_found: int,
                   new_listings: int, error: Optional[str]) -> None:
        self.conn.execute(
            """INSERT INTO scrape_log
               (source, started_at, finished_at, listings_found, new_listings, error)
               VALUES (?,?,?,?,?,?)""",
            (source, started_at.isoformat(), finished_at.isoformat(),
             listings_found, new_listings, error),
        )
        self.conn.commit()

    def get_scrape_logs(self, source: str, limit: int = 10) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM scrape_log WHERE source=? ORDER BY id DESC LIMIT ?",
            (source, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _parse_dt(self, value) -> Optional[datetime]:
        if value is None:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None

    def _row_to_listing(self, row: sqlite3.Row) -> Listing:
        return Listing(
            source=row["source"],
            external_id=row["external_id"],
            url=row["url"],
            title=row["title"],
            price=row["price"],
            size_category=row["size_category"],
            location=row["location"],
            description=row["description"],
            images_json=row["images_json"],
            raw_data=row["raw_data"],
            first_seen_at=self._parse_dt(row["first_seen_at"]),
            last_seen_at=self._parse_dt(row["last_seen_at"]),
            notified_at=self._parse_dt(row["notified_at"]),
            is_active=bool(row["is_active"]),
        )

    def close(self) -> None:
        self.conn.close()
