"""Abstract base seeder with validation and idempotent insert."""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import DataLineage, SourceReport


class BaseSeeder(ABC):
    """Base class for all data seeders."""

    def __init__(self, session: Session, seed_dir: Path) -> None:
        self.session = session
        self.seed_dir = seed_dir

    def load_json(self, filename: str) -> list[dict[str, Any]]:
        """Load and parse a JSON seed file."""
        path = self.seed_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Seed file not found: {path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Support top-level key wrapping like {"cities": [...]}
            for value in data.values():
                if isinstance(value, list):
                    return value
            return [data]
        return data

    @abstractmethod
    def validate(self) -> bool:
        """Validate seed data before inserting. Return True if valid."""
        ...

    @abstractmethod
    def seed(self) -> int:
        """Insert seed data. Return number of records created."""
        ...

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self.session.rollback()

    def _exists(self, model_class: type, **kwargs: Any) -> bool:
        """Check if a record already exists with the given attributes."""
        query = self.session.query(model_class).filter_by(**kwargs)
        return query.first() is not None

    def _get_or_create(self, model_class: type, defaults: dict[str, Any] | None = None, **kwargs: Any) -> tuple[Any, bool]:
        """Get existing record or create new one. Returns (instance, created)."""
        instance = self.session.query(model_class).filter_by(**kwargs).first()
        if instance:
            return instance, False
        params = {**kwargs, **(defaults or {})}
        instance = model_class(**params)
        self.session.add(instance)
        self.session.flush()
        return instance, True


class LineageAwareSeeder(BaseSeeder):
    """Seeder that tracks data lineage for each inserted record."""

    def _get_or_create_with_lineage(
        self,
        model_class: type,
        table_name: str,
        source_report_id: int,
        page_number: int | None = None,
        confidence: float = 0.8,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[Any, bool]:
        """Get or create a record and also create a DataLineage entry.

        Returns (instance, created).
        """
        instance, created = self._get_or_create(
            model_class, defaults=defaults, **kwargs
        )
        if created:
            lineage = DataLineage(
                table_name=table_name,
                record_id=instance.id,
                source_report_id=source_report_id,
                page_number=page_number,
                confidence_score=confidence,
                extracted_at=datetime.now(timezone.utc),
            )
            self.session.add(lineage)
            self.session.flush()
        return instance, created

    def _get_source_report(self, filename: str) -> SourceReport | None:
        """Look up a SourceReport by filename."""
        return (
            self.session.query(SourceReport)
            .filter_by(filename=filename)
            .first()
        )
