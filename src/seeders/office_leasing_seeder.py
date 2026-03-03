"""Seeder for office_leasing_records table.

Loads leasing data from data/seed/office_leasing_records.json.
Each record is keyed on (office_project_id, period_id) for idempotency.
"""

from typing import Any

from src.db.models import OfficeProject, OfficeLeasingRecord, ReportPeriod
from src.seeders.base_seeder import BaseSeeder


class OfficeLeasingSeeder(BaseSeeder):
    """Seeds office_leasing_records from data/seed/office_leasing_records.json."""

    SEED_FILE = "office_leasing_records.json"

    def validate(self) -> bool:
        data = self.load_json(self.SEED_FILE)
        if not data:
            raise ValueError("office_leasing_records.json is empty")
        required = {"office_project_name", "period_year", "period_half"}
        for record in data:
            missing = required - record.keys()
            if missing:
                raise ValueError(f"Office leasing record missing fields: {missing}")
        return True

    def seed(self) -> int:
        data = self.load_json(self.SEED_FILE)
        count = 0

        for record in data:
            project = (
                self.session.query(OfficeProject)
                .filter_by(name=record["office_project_name"])
                .first()
            )
            if project is None:
                continue  # skip if parent project not seeded yet

            period = (
                self.session.query(ReportPeriod)
                .filter_by(year=record["period_year"], half=record["period_half"])
                .first()
            )
            if period is None:
                period = ReportPeriod(
                    year=record["period_year"],
                    half=record["period_half"],
                )
                self.session.add(period)
                self.session.flush()

            _, created = self._get_or_create(
                OfficeLeasingRecord,
                office_project_id=project.id,
                period_id=period.id,
                defaults={
                    "rent_min_usd": record.get("rent_min_usd"),
                    "rent_max_usd": record.get("rent_max_usd"),
                    "management_fee_usd": record.get("management_fee_usd"),
                    "occupancy_rate_pct": record.get("occupancy_rate_pct"),
                    "area_basis": record.get("area_basis"),
                    "notes": record.get("notes"),
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
