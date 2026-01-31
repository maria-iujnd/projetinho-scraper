"""
DEPRECATED: This module is no longer used by the bot.

Single source of truth for persistence is now: state_store.py using kiwi_state.db

Reason for deprecation:
- Unified schema in state_store.py eliminates confusion
- Prevents dedupe inconsistencies (scraper and sender use same DB)
- Simplifies code maintenance

If you need to reference old db.py tables, migrate to state_store.py equivalents:
- route_policy → routes_config.py (constants)
- route_date_state → state_store.py (unified OW/RT schema)
- announcements → state_store.py
- offers_history → not actively used (use rt_price_history if needed)
- run_log → not actively used
"""
import sqlite3
import datetime
from date_utils import format_date_for_user  # Regra: toda data exibida ao usuário DEVE passar por esta função

# ATENÇÃO: NUNCA monte datas manualmente para o usuário!
# Sempre use format_date_for_user(dt) para exibir datas em mensagens, logs ou relatórios para o usuário final.
from pathlib import Path
from typing import Optional

# --- Configuration ---
DB_FILE = Path(__file__).parent / "scraper_data.db"

# --- Utility Functions ---

def now_iso() -> str:
    """Returns the current timestamp in ISO 8601 format (UTC)."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def parse_iso(iso_str: Optional[str]) -> Optional[datetime.datetime]:
    """Parses an ISO 8601 string into a datetime object."""
    if not iso_str:
        return None
    try:
        # Handles both timezone-aware and naive ISO strings
        if iso_str.endswith('Z'):
            iso_str = iso_str[:-1] + '+00:00'
        return datetime.datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        return None

# --- Database Connection ---

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

# --- Database Initialization ---

def init_db():
    """
    Initializes the database, creating all necessary tables and indexes
    if they do not already exist. This function is idempotent.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table: route_policy - Defines rules for scraping each route.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_policy (
        origin TEXT NOT NULL,
        dest TEXT NOT NULL,
        trip_type TEXT NOT NULL DEFAULT 'one-way',
        is_active BOOLEAN NOT NULL DEFAULT 1,
        price_ceiling INTEGER,
        cooldown_good_days INTEGER DEFAULT 1,
        cooldown_bad_hours INTEGER DEFAULT 6,
        cooldown_nodata_hours INTEGER DEFAULT 12,
        PRIMARY KEY (origin, dest, trip_type)
    )
    """)

    # Table: route_date_state - Tracks the last known state for a specific route on a specific date.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_date_state (
        origin TEXT NOT NULL,
        dest TEXT NOT NULL,
        depart_date TEXT NOT NULL,
        status TEXT,
        best_price INTEGER,
        last_checked_at TEXT,
        cooldown_until TEXT,
        last_offer_hash TEXT,
        PRIMARY KEY (origin, dest, depart_date)
    )
    """)

    # Table: offers_history - Stores a historical log of all unique offers found.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offers_history (
        offer_hash TEXT PRIMARY KEY,
        origin TEXT NOT NULL,
        dest TEXT NOT NULL,
        depart_date TEXT NOT NULL,
        price INTEGER NOT NULL,
        airline TEXT,
        duration_minutes INTEGER,
        stops INTEGER,
        first_seen_at TEXT,
        last_seen_at TEXT
    )
    """)

    # Table: announcements - Tracks which offers have been sent as notifications.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        offer_hash TEXT PRIMARY KEY,
        announced_at TEXT
    )
    """)

    # Table: run_log - Logs each execution of the scraper.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS run_log (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT,
        checked_routes INTEGER DEFAULT 0,
        new_offers INTEGER DEFAULT 0,
        errors TEXT
    )
    """)

    # --- Indexes ---
    # Index to quickly find routes that are no longer in cooldown.
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cooldown_until ON route_date_state (cooldown_until)")

    conn.commit()
    conn.close()
    print(f"Database initialized successfully at '{DB_FILE}'.")

if __name__ == '__main__':
    # Allows running this script directly to set up the database.
    init_db()