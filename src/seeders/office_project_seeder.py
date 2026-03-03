"""Seeder for office_projects table.

Loads office building profiles from data/seed/office_projects.json.
Each record is keyed on (name, city_id) for idempotency.
"""

from typing import Any

from src.db.models import City, District, OfficeProject
from src.seeders.base_seeder import BaseSeeder


class OfficeProjectSeeder(BaseSeeder):
    """Seeds office_projects from data/seed/office_projects.json."""

    SEED_FILE = "office_projects.json"

    def validate(self) -> bool:
        data = self.load_json(self.SEED_FILE)
        if not data:
            raise ValueError("office_projects.json is empty")
        required = {"name", "office_grade"}
        for record in data:
            missing = required - record.keys()
            if missing:
                raise ValueError(f"Office project record missing fields: {missing}")
        return True

    def seed(self) -> int:
        data = self.load_json(self.SEED_FILE)
        count = 0

        for record in data:
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

            _, created = self._get_or_create(
                OfficeProject,
                name=record["name"],
                city_id=city_id,
                defaults={
                    "developer_name": record.get("developer_name"),
                    "investor_name": record.get("investor_name"),
                    "management_company": record.get("management_company"),
                    "district_id": district_id,
                    "address": record.get("address"),
                    "office_grade": record.get("office_grade"),
                    "operation_year": record.get("operation_year"),
                    "operation_quarter": record.get("operation_quarter"),
                    "total_floors": record.get("total_floors"),
                    "num_office_floors": record.get("num_office_floors"),
                    "num_basements": record.get("num_basements"),
                    "total_leasing_area_m2": record.get("total_leasing_area_m2"),
                    "total_gfa_m2": record.get("total_gfa_m2"),
                    "avg_floor_area_m2": record.get("avg_floor_area_m2"),
                    "ceiling_height_m": record.get("ceiling_height_m"),
                    "raised_floor_cm": record.get("raised_floor_cm"),
                    "lift_passenger": record.get("lift_passenger"),
                    "lift_service": record.get("lift_service"),
                    "green_certificate": record.get("green_certificate"),
                    "area_calculation_basis": record.get("area_calculation_basis"),
                    "has_conference": record.get("has_conference", False),
                    "has_sky_terrace": record.get("has_sky_terrace", False),
                    "has_gym": record.get("has_gym", False),
                    "has_coworking": record.get("has_coworking", False),
                    "has_retail": record.get("has_retail", False),
                    "notes": record.get("notes"),
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
