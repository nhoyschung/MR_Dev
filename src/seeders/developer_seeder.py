"""Seeder for developer profiles."""

from pydantic import BaseModel
from typing import Optional

from src.db.models import Developer
from src.seeders.base_seeder import BaseSeeder


class DeveloperSchema(BaseModel):
    id: int
    name_en: str
    name_vi: Optional[str] = None
    stock_code: Optional[str] = None
    market_cap: Optional[float] = None
    hq_city_id: Optional[int] = None
    established_year: Optional[int] = None
    website: Optional[str] = None
    description: Optional[str] = None


class DeveloperSeeder(BaseSeeder):
    """Seeds developer profiles."""

    def validate(self) -> bool:
        devs = self.load_json("developers.json")
        for d in devs:
            DeveloperSchema(**d)
        return True

    def seed(self) -> int:
        count = 0
        devs = self.load_json("developers.json")
        for d_data in devs:
            validated = DeveloperSchema(**d_data)
            _, created = self._get_or_create(
                Developer,
                name_en=validated.name_en,
                defaults={
                    "name_vi": validated.name_vi,
                    "stock_code": validated.stock_code,
                    "market_cap": validated.market_cap,
                    "hq_city_id": validated.hq_city_id,
                    "established_year": validated.established_year,
                    "website": validated.website,
                    "description": validated.description,
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
