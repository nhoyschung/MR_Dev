"""Seeder for price history records."""

from pydantic import BaseModel
from typing import Optional

from src.db.models import PriceRecord, ReportPeriod
from src.seeders.base_seeder import BaseSeeder


class PriceSchema(BaseModel):
    project_id: int
    period_year: int
    period_half: str
    price_vnd_per_m2: Optional[float] = None
    price_usd_per_m2: Optional[float] = None
    price_change_pct: Optional[float] = None
    price_incl_vat: Optional[bool] = True
    source_report: Optional[str] = None


class PriceSeeder(BaseSeeder):
    """Seeds price records for projects."""

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
        prices = self.load_json("prices.json")
        for p in prices:
            PriceSchema(**p)
        return True

    def seed(self) -> int:
        count = 0
        prices = self.load_json("prices.json")
        for p_data in prices:
            validated = PriceSchema(**p_data)
            period_id = self._get_period_id(validated.period_year, validated.period_half)
            _, created = self._get_or_create(
                PriceRecord,
                project_id=validated.project_id,
                period_id=period_id,
                defaults={
                    "price_vnd_per_m2": validated.price_vnd_per_m2,
                    "price_usd_per_m2": validated.price_usd_per_m2,
                    "price_change_pct": validated.price_change_pct,
                    "price_incl_vat": validated.price_incl_vat,
                    "source_report": validated.source_report,
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
