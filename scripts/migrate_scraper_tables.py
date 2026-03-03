"""Migration script to add scraper tables and columns."""

from sqlalchemy import text
from src.db.connection import engine


def migrate_scraper_tables() -> None:
    """Create scrape_jobs and scraped_listings tables, add bds columns to projects."""
    with engine.connect() as conn:
        existing_tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }

        # --- scrape_jobs table ---
        if "scrape_jobs" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE scrape_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type VARCHAR(50) NOT NULL,
                    target_url VARCHAR(500),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    started_at DATETIME,
                    completed_at DATETIME,
                    items_found INTEGER DEFAULT 0,
                    items_saved INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """))
            print("Created table: scrape_jobs")
        else:
            print("Table already exists: scrape_jobs")

        # --- scraped_listings table ---
        if "scraped_listings" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE scraped_listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scrape_job_id INTEGER NOT NULL REFERENCES scrape_jobs(id),
                    bds_listing_id VARCHAR(100) UNIQUE,
                    project_name VARCHAR(300),
                    district_name VARCHAR(100),
                    city_name VARCHAR(100),
                    price_raw VARCHAR(100),
                    price_vnd REAL,
                    price_per_sqm REAL,
                    area_sqm REAL,
                    bedrooms INTEGER,
                    bathrooms INTEGER,
                    floor VARCHAR(20),
                    direction VARCHAR(30),
                    listing_url VARCHAR(500),
                    scraped_at DATETIME,
                    matched_project_id INTEGER REFERENCES projects(id),
                    promoted BOOLEAN DEFAULT 0
                )
            """))
            conn.execute(text(
                "CREATE INDEX idx_scraped_listings_job ON scraped_listings(scrape_job_id)"
            ))
            conn.execute(text(
                "CREATE INDEX idx_scraped_listings_project ON scraped_listings(matched_project_id)"
            ))
            print("Created table: scraped_listings")
        else:
            print("Table already exists: scraped_listings")

        # --- Add bds_slug and bds_url to projects ---
        project_cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(projects)"))
        }

        for col_name, col_type in [("bds_slug", "VARCHAR(200)"), ("bds_url", "VARCHAR(500)")]:
            if col_name not in project_cols:
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}"))
                print(f"Added column: projects.{col_name}")
            else:
                print(f"Column already exists: projects.{col_name}")

        conn.commit()
        print("\nMigration complete.")


if __name__ == "__main__":
    migrate_scraper_tables()
