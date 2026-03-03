"""Seeder for office_market_summaries table.

Loads city/district-level office market statistics from
data/seed/office_market_summaries.json.
Each record is keyed on (city_id, district_id, period_id) for idempotency.
"""

from typing import Any

from src.db.models import City, District, OfficeMarketSummary, ReportPeriod
from src.seeders.base_seeder import BaseSeeder


class OfficeMarketSummarySeeder(BaseSeeder):
    """Seeds office_market_summaries from data/seed/office_market_summaries.json."""

    SEED_FILE = "office_market_summaries.json"

    def validate(self) -> bool:
        data = self.load_json(self.SEED_FILE)
        if not data:
            raise ValueError("office_market_summaries.json is empty")
        required = {"city", "period_year", "period_half"}
        for record in data:
            missing = required - record.keys()
            if missing:
                raise ValueError(f"Office market summary missing fields: {missing}")
        return True

    def seed(self) -> int:
        data = self.load_json(self.SEED_FILE)
        count = 0

        for record in data:
            city = (
                self.session.query(City)
                .filter_by(name_en=record["city"])
                .first()
            )
            if city is None:
                continue

            district_id: int | None = None
            if record.get("district"):
                district = (
                    self.session.query(District)
                    .filter_by(name_en=record["district"], city_id=city.id)
                    .first()
                )
                if district:
                    district_id = district.id

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
                OfficeMarketSummary,
                city_id=city.id,
                district_id=district_id,
                period_id=period.id,
                defaults={
                    "total_stock_nla_m2": record.get("total_stock_nla_m2"),
                    "grade_a_stock_m2": record.get("grade_a_stock_m2"),
                    "grade_b_stock_m2": record.get("grade_b_stock_m2"),
                    "grade_c_stock_m2": record.get("grade_c_stock_m2"),
                    "num_projects_total": record.get("num_projects_total"),
                    "num_projects_grade_a": record.get("num_projects_grade_a"),
                    "avg_rent_usd_grade_a": record.get("avg_rent_usd_grade_a"),
                    "avg_rent_usd_grade_b": record.get("avg_rent_usd_grade_b"),
                    "avg_rent_usd_grade_c": record.get("avg_rent_usd_grade_c"),
                    "avg_occupancy_grade_a_pct": record.get("avg_occupancy_grade_a_pct"),
                    "avg_occupancy_grade_b_pct": record.get("avg_occupancy_grade_b_pct"),
                    "avg_occupancy_grade_c_pct": record.get("avg_occupancy_grade_c_pct"),
                    "net_absorption_m2": record.get("net_absorption_m2"),
                    "new_supply_m2": record.get("new_supply_m2"),
                    "notes": record.get("notes"),
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
