"""Migration script to add new columns to source_reports table."""

from sqlalchemy import text
from src.db.connection import engine


def migrate_source_reports():
    """Add new columns to source_reports table."""
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(source_reports)"))
        existing_columns = {row[1] for row in result}

        columns_to_add = {
            "pdf_path": "TEXT",
            "file_size_mb": "REAL",
            "pdf_created_at": "DATETIME",
            "extraction_started_at": "DATETIME",
            "extraction_completed_at": "DATETIME",
            "extraction_time_sec": "REAL",
            "quality_score": "REAL",
            "extracted_text_length": "INTEGER",
        }

        added_columns = []
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                sql = text(f"ALTER TABLE source_reports ADD COLUMN {column_name} {column_type}")
                conn.execute(sql)
                added_columns.append(column_name)
                print(f"Added column: {column_name} ({column_type})")
            else:
                print(f"Column already exists: {column_name}")

        conn.commit()

        if added_columns:
            print(f"\n✅ Migration complete: Added {len(added_columns)} column(s)")
        else:
            print("\n✅ No migration needed: All columns already exist")


if __name__ == "__main__":
    migrate_source_reports()
