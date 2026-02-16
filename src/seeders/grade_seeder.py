"""Seeder for grade definitions and report periods."""

from pydantic import BaseModel
from typing import Optional

from src.db.models import GradeDefinition, ReportPeriod
from src.seeders.base_seeder import BaseSeeder


class GradeSchema(BaseModel):
    city_id: int
    grade_code: str
    min_price_usd: Optional[float] = None
    max_price_usd: Optional[float] = None
    segment: str
    period_year: int
    period_half: str


class GradeSeeder(BaseSeeder):
    """Seeds report periods and grade definitions."""

    def _ensure_period(self, year: int, half: str) -> ReportPeriod:
        period, _ = self._get_or_create(
            ReportPeriod,
            year=year,
            half=half,
        )
        return period

    def validate(self) -> bool:
        grades = self.load_json("grades.json")
        for g in grades:
            GradeSchema(**g)
        return True

    def seed(self) -> int:
        count = 0

        # Seed standard periods (2021-2025 for historical data)
        for year in range(2021, 2026):
            for half in ("H1", "H2"):
                _, created = self._get_or_create(ReportPeriod, year=year, half=half)
                if created:
                    count += 1

        grades = self.load_json("grades.json")
        for g_data in grades:
            validated = GradeSchema(**g_data)
            period = self._ensure_period(validated.period_year, validated.period_half)
            _, created = self._get_or_create(
                GradeDefinition,
                city_id=validated.city_id,
                grade_code=validated.grade_code,
                period_id=period.id,
                defaults={
                    "min_price_usd": validated.min_price_usd,
                    "max_price_usd": validated.max_price_usd,
                    "segment": validated.segment,
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
