"""Seeder for supply/inventory data."""

from pydantic import BaseModel
from typing import Optional

from src.db.models import SupplyRecord, ReportPeriod
from src.seeders.base_seeder import BaseSeeder


class SupplySchema(BaseModel):
    district_id: int
    period_year: int
    period_half: str
    total_inventory: Optional[int] = None
    new_supply: Optional[int] = None
    sold_units: Optional[int] = None
    absorption_rate_pct: Optional[float] = None
    remaining_inventory: Optional[int] = None


class SupplySeeder(BaseSeeder):
    """Seeds supply/inventory records (district-level, no project_id)."""

    def _get_period_id(self, year: int, half: str) -> int:
        period = (
            self.session.query(ReportPeriod)
            .filter_by(year=year, half=half)
            .first()
        )
        if not period:
            raise ValueError(f"Period {year}-{half} not found. Run GradeSeeder first.")
        return period.id

    def validate(self) -> bool:
        records = self.load_json("supply.json")
        for r in records:
            SupplySchema(**r)
        return True

    def seed(self) -> int:
        count = 0
        records = self.load_json("supply.json")
        for s_data in records:
            validated = SupplySchema(**s_data)
            period_id = self._get_period_id(validated.period_year, validated.period_half)
            _, created = self._get_or_create(
                SupplyRecord,
                period_id=period_id,
                district_id=validated.district_id,
                project_id=None,
                defaults={
                    "total_inventory": validated.total_inventory,
                    "new_supply": validated.new_supply,
                    "sold_units": validated.sold_units,
                    "absorption_rate_pct": validated.absorption_rate_pct,
                    "remaining_inventory": validated.remaining_inventory,
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
