"""Initialize the database: create all tables."""

from sqlalchemy import inspect, text

from src.db.models import Base
from src.db.connection import engine


def ensure_schema_compatibility() -> None:
    """Apply lightweight, idempotent schema upgrades for existing DB files."""
    inspector = inspect(engine)

    # Added in v2: district-level supply support.
    if "supply_records" in inspector.get_table_names():
        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("supply_records")}
        if "district_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE supply_records ADD COLUMN district_id INTEGER"))
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_supply_records_district_period "
                        "ON supply_records(district_id, period_id)"
                    )
                )
            print("Schema upgraded: added supply_records.district_id")

        cols = {c["name"] for c in inspector.get_columns("supply_records")}

        # Remove legacy rows created before district_id support.
        # These rows have neither project_id nor district_id and are unusable.
        if "district_id" in cols:
            with engine.begin() as conn:
                removed = conn.execute(
                    text(
                        "DELETE FROM supply_records "
                        "WHERE project_id IS NULL AND district_id IS NULL"
                    )
                ).rowcount
            if removed:
                print(f"Schema cleanup: removed {removed} legacy supply rows")


def init_database() -> None:
    """Create all tables defined in models.py."""
    Base.metadata.create_all(engine)
    ensure_schema_compatibility()
    print(f"Database initialized with {len(Base.metadata.tables)} tables.")
    for table_name in sorted(Base.metadata.tables):
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_database()
