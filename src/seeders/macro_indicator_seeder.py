"""Seeder for macro_indicators table.

Loads Vietnam macroeconomic indicators (GDP, CPI, interest rates, FDI)
from data/seed/macro_indicators.json and inserts them into the database.

Each record is keyed on (period_id, indicator_type, city_id) for idempotency.
City is optional — None means a national-level indicator.
"""

from typing import Any

from src.db.models import MacroIndicator, ReportPeriod, City
from src.seeders.base_seeder import BaseSeeder


class MacroIndicatorSeeder(BaseSeeder):
    """Seeds macro_indicators from data/seed/macro_indicators.json."""

    SEED_FILE = "macro_indicators.json"

    def validate(self) -> bool:
        """Verify seed file exists and contains valid records."""
        data = self.load_json(self.SEED_FILE)
        if not data:
            raise ValueError("macro_indicators.json is empty")
        required = {"period_year", "period_half", "indicator_type", "value"}
        for record in data:
            missing = required - record.keys()
            if missing:
                raise ValueError(f"Macro indicator record missing fields: {missing}")
        return True

    def seed(self) -> int:
        """Insert macro indicator records. Returns number of new records created."""
        data = self.load_json(self.SEED_FILE)
        count = 0

        for record in data:
            period = (
                self.session.query(ReportPeriod)
                .filter_by(year=record["period_year"], half=record["period_half"])
                .first()
            )
            if period is None:
                # Auto-create the period if it doesn't exist
                period = ReportPeriod(
                    year=record["period_year"],
                    half=record["period_half"],
                )
                self.session.add(period)
                self.session.flush()

            # Resolve optional city (None = national indicator)
            city_id: int | None = None
            if record.get("city"):
                city = (
                    self.session.query(City)
                    .filter_by(name_en=record["city"])
                    .first()
                )
                if city:
                    city_id = city.id

            _, created = self._get_or_create(
                MacroIndicator,
                period_id=period.id,
                indicator_type=record["indicator_type"],
                city_id=city_id,
                defaults={
                    "value": float(record["value"]),
                    "source": record.get("source"),
                    "notes": record.get("notes"),
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
