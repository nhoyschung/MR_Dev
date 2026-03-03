"""Migration: add reconcile_status/reconcile_detail to scraped_listings,
and create scraped_office_listings table.

Idempotent — safe to run multiple times.

Run with:
    python -m scripts.migrate_reconcile_columns
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "mr_system.db"


def run_migration() -> None:
    print(f"DB: {DB_PATH}")
    if not DB_PATH.exists():
        print("ERROR: Database not found. Run `python -m src.db.init_db` first.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")

    # ── 1. Add reconcile columns to scraped_listings ─────────────────────────
    existing_cols = {row[1] for row in cur.execute("PRAGMA table_info(scraped_listings)")}

    for col_name, col_def in [
        ("reconcile_status", "VARCHAR(30)"),
        ("reconcile_detail", "TEXT"),
    ]:
        if col_name not in existing_cols:
            cur.execute(f"ALTER TABLE scraped_listings ADD COLUMN {col_name} {col_def}")
            print(f"  [OK] Added column: scraped_listings.{col_name}")
        else:
            print(f"  [--] Already exists: scraped_listings.{col_name}")

    # ── 2. scraped_office_listings table ─────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scraped_office_listings (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            scrape_job_id               INTEGER NOT NULL REFERENCES scrape_jobs(id),
            listing_id                  VARCHAR(100) UNIQUE,
            building_name               VARCHAR(300),
            address                     VARCHAR(300),
            district_name               VARCHAR(100),
            city_name                   VARCHAR(100),
            rent_raw                    VARCHAR(200),
            rent_vnd_per_m2_month       REAL,
            rent_usd_per_m2_month       REAL,
            area_m2                     REAL,
            floor                       VARCHAR(30),
            listing_url                 VARCHAR(500),
            scraped_at                  DATETIME,
            matched_office_project_id   INTEGER REFERENCES office_projects(id),
            promoted                    BOOLEAN DEFAULT 0,
            reconcile_status            VARCHAR(30),
            reconcile_detail            TEXT
        )
    """)
    print("  [OK] scraped_office_listings table ensured")

    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_scraped_office_job ON scraped_office_listings(scrape_job_id)",
        "CREATE INDEX IF NOT EXISTS idx_scraped_office_project ON scraped_office_listings(matched_office_project_id)",
        "CREATE INDEX IF NOT EXISTS idx_scraped_office_promoted ON scraped_office_listings(promoted)",
    ]:
        cur.execute(idx_sql)
    print("  [OK] Indexes ensured")

    conn.commit()
    conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    run_migration()
