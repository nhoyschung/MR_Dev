"""Seeder for hotel_room_types table.

Loads room type data from data/seed/hotel_room_types.json.
Each record is keyed on (hotel_project_id, room_type) for idempotency.
"""

from typing import Any

from src.db.models import HotelProject, HotelRoomType
from src.seeders.base_seeder import BaseSeeder


class HotelRoomTypeSeeder(BaseSeeder):
    """Seeds hotel_room_types from data/seed/hotel_room_types.json."""

    SEED_FILE = "hotel_room_types.json"

    def validate(self) -> bool:
        data = self.load_json(self.SEED_FILE)
        if not data:
            raise ValueError("hotel_room_types.json is empty")
        required = {"hotel_project_name", "room_type"}
        for record in data:
            missing = required - record.keys()
            if missing:
                raise ValueError(f"Hotel room type record missing fields: {missing}")
        return True

    def seed(self) -> int:
        data = self.load_json(self.SEED_FILE)
        count = 0

        for record in data:
            hotel = (
                self.session.query(HotelProject)
                .filter_by(name=record["hotel_project_name"])
                .first()
            )
            if hotel is None:
                continue  # skip if parent hotel not seeded yet

            _, created = self._get_or_create(
                HotelRoomType,
                hotel_project_id=hotel.id,
                room_type=record["room_type"],
                defaults={
                    "area_m2": record.get("area_m2"),
                    "room_count": record.get("room_count"),
                    "notes": record.get("notes"),
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
