"""Seeder for hotel_performance_records table.

Loads hotel occupancy/ADR/RevPAR data from data/seed/hotel_performance_records.json.
hotel_project_name == null means a market-aggregate (city/district-level) record.
Each record is keyed on (hotel_project_id, city_id, district_id, period_id).
"""

from typing import Any

from src.db.models import (
    City, District, HotelPerformanceRecord, HotelProject, ReportPeriod
)
from src.seeders.base_seeder import BaseSeeder


class HotelPerformanceSeeder(BaseSeeder):
    """Seeds hotel_performance_records from data/seed/hotel_performance_records.json."""

    SEED_FILE = "hotel_performance_records.json"

    def validate(self) -> bool:
        data = self.load_json(self.SEED_FILE)
        if not data:
            raise ValueError("hotel_performance_records.json is empty")
        required = {"period_year", "period_half"}
        for record in data:
            missing = required - record.keys()
            if missing:
                raise ValueError(f"Hotel performance record missing fields: {missing}")
        return True

    def seed(self) -> int:
        data = self.load_json(self.SEED_FILE)
        count = 0

        for record in data:
            hotel_project_id: int | None = None
            if record.get("hotel_project_name"):
                hotel = (
                    self.session.query(HotelProject)
                    .filter_by(name=record["hotel_project_name"])
                    .first()
                )
                if hotel:
                    hotel_project_id = hotel.id

            city_id: int | None = None
            if record.get("city"):
                city = (
                    self.session.query(City)
                    .filter_by(name_en=record["city"])
                    .first()
                )
                if city:
                    city_id = city.id

            district_id: int | None = None
            if record.get("district") and city_id is not None:
                district = (
                    self.session.query(District)
                    .filter_by(name_en=record["district"], city_id=city_id)
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
                HotelPerformanceRecord,
                hotel_project_id=hotel_project_id,
                city_id=city_id,
                district_id=district_id,
                period_id=period.id,
                defaults={
                    "occupancy_rate_pct": record.get("occupancy_rate_pct"),
                    "adr_vnd": record.get("adr_vnd"),
                    "revpar_vnd": record.get("revpar_vnd"),
                    "adr_usd": record.get("adr_usd"),
                    "international_visitor_count": record.get("international_visitor_count"),
                    "domestic_visitor_count": record.get("domestic_visitor_count"),
                    "notes": record.get("notes"),
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
