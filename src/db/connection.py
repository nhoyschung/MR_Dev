"""Database engine and session factory."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from src.config import DATABASE_URL


def _enable_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign key enforcement for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine = create_engine(DATABASE_URL, echo=False)
event.listen(engine, "connect", _enable_foreign_keys)

SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    """Create and return a new database session."""
    return SessionLocal()
