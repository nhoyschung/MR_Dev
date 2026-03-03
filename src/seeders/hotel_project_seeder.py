"""Seeder for hotel_projects table.

Loads hotel property profiles from data/seed/hotel_projects.json.
Each record is keyed on (name, city_id) for idempotency.
"""

from typing import Any

from src.db.models import City, District, HotelProject
from src.seeders.base_seeder import BaseSeeder


class HotelProjectSeeder(BaseSeeder):
    """Seeds hotel_projects from data/seed/hotel_projects.json."""

    SEED_FILE = "hotel_projects.json"

    def validate(self) -> bool:
        data = self.load_json(self.SEED_FILE)
        if not data:
            raise ValueError("hotel_projects.json is empty")
        required = {"name"}
        for record in data:
            missing = required - record.keys()
            if missing:
                raise ValueError(f"Hotel project record missing fields: {missing}")
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
                HotelProject,
                name=record["name"],
                city_id=city_id,
                defaults={
                    "brand": record.get("brand"),
                    "operator": record.get("operator"),
                    "investor_name": record.get("investor_name"),
                    "developer_name": record.get("developer_name"),
                    "district_id": district_id,
                    "address": record.get("address"),
                    "star_rating": record.get("star_rating"),
                    "hotel_type": record.get("hotel_type"),
                    "total_rooms": record.get("total_rooms"),
                    "operation_year": record.get("operation_year"),
                    "operation_quarter": record.get("operation_quarter"),
                    "total_floors": record.get("total_floors"),
                    "num_basements": record.get("num_basements"),
                    "land_area_m2": record.get("land_area_m2"),
                    "total_gfa_m2": record.get("total_gfa_m2"),
                    "has_pool": record.get("has_pool", False),
                    "has_gym": record.get("has_gym", False),
                    "has_spa": record.get("has_spa", False),
                    "has_restaurant": record.get("has_restaurant", False),
                    "has_ballroom": record.get("has_ballroom", False),
                    "has_sky_bar": record.get("has_sky_bar", False),
                    "has_conference": record.get("has_conference", False),
                    "has_coworking": record.get("has_coworking", False),
                    "notes": record.get("notes"),
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
