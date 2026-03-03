"""Migration: add data_source column to price_records and backfill.

data_source values:
  'nho_pdf'   — from NHO-PD professional research reports (PDF ingestion)
  'bds_scrape' — from batdongsan.com.vn web scraping
  'manual'    — manually entered data

Backfill logic:
  - Records linked via data_lineage → source_reports.report_type='web_scrape' → 'bds_scrape'
  - All others → 'nho_pdf'

Idempotent — safe to run multiple times.

Run with:
    python -m scripts.migrate_data_source
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "mr_system.db"


def run_migration() -> None:
    print(f"DB: {DB_PATH}")
    if not DB_PATH.exists():
        print("ERROR: Database not found.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── 1. Add column if missing ──────────────────────────────────────────────
    existing_cols = {row[1] for row in cur.execute("PRAGMA table_info(price_records)")}
    if "data_source" not in existing_cols:
        cur.execute("ALTER TABLE price_records ADD COLUMN data_source VARCHAR(20) DEFAULT 'nho_pdf'")
        print("  [OK] Added column: price_records.data_source")
    else:
        print("  [--] Column already exists: price_records.data_source")

    # ── 2. Backfill NULL → 'nho_pdf' (default) ───────────────────────────────
    cur.execute("UPDATE price_records SET data_source = 'nho_pdf' WHERE data_source IS NULL")
    print(f"  [OK] Set NULL → 'nho_pdf': {cur.rowcount} rows")

    # ── 3. Backfill BDS scrape records via data_lineage ───────────────────────
    # Find price_record IDs linked to web_scrape source_reports
    cur.execute("""
        UPDATE price_records
        SET data_source = 'bds_scrape'
        WHERE id IN (
            SELECT dl.record_id
            FROM data_lineage dl
            JOIN source_reports sr ON dl.source_report_id = sr.id
            WHERE dl.table_name = 'price_records'
              AND sr.report_type = 'web_scrape'
        )
    """)
    bds_count = cur.rowcount
    print(f"  [OK] Backfilled 'bds_scrape': {bds_count} rows")

    # ── 4. Show final distribution ────────────────────────────────────────────
    print()
    print("  Final data_source distribution:")
    for row in cur.execute(
        "SELECT data_source, COUNT(*) FROM price_records GROUP BY data_source ORDER BY COUNT(*) DESC"
    ):
        print(f"    {row[0] or 'NULL':15s}: {row[1]} records")

    conn.commit()
    conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    run_migration()
