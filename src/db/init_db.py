"""Initialize the database: create all tables."""

from src.db.models import Base
from src.db.connection import engine


def init_database() -> None:
    """Create all tables defined in models.py."""
    Base.metadata.create_all(engine)
    print(f"Database initialized with {len(Base.metadata.tables)} tables.")
    for table_name in sorted(Base.metadata.tables):
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_database()
