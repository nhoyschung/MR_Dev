"""Seeder for cities, districts, and wards."""

from pydantic import BaseModel, field_validator
from typing import Optional

from src.db.models import City, District, Ward
from src.seeders.base_seeder import BaseSeeder


class CitySchema(BaseModel):
    id: int
    name_en: str
    name_vi: Optional[str] = None
    name_ko: Optional[str] = None
    region: str

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        if v not in ("South", "North", "Central"):
            raise ValueError(f"Invalid region: {v}")
        return v


class DistrictSchema(BaseModel):
    id: int
    city_id: int
    name_en: str
    name_vi: Optional[str] = None
    name_ko: Optional[str] = None
    district_type: Optional[str] = None


class CitySeeder(BaseSeeder):
    """Seeds cities, districts, and wards."""

    def validate(self) -> bool:
        cities = self.load_json("cities.json")
        for c in cities:
            CitySchema(**c)
        districts = self.load_json("districts.json")
        for d in districts:
            DistrictSchema(**d)
        return True

    def seed(self) -> int:
        count = 0
        cities = self.load_json("cities.json")
        for c_data in cities:
            validated = CitySchema(**c_data)
            _, created = self._get_or_create(
                City,
                name_en=validated.name_en,
                defaults={
                    "name_vi": validated.name_vi,
                    "name_ko": validated.name_ko,
                    "region": validated.region,
                },
            )
            if created:
                count += 1

        districts = self.load_json("districts.json")
        for d_data in districts:
            validated = DistrictSchema(**d_data)
            _, created = self._get_or_create(
                District,
                name_en=validated.name_en,
                city_id=validated.city_id,
                defaults={
                    "name_vi": validated.name_vi,
                    "name_ko": validated.name_ko,
                    "district_type": validated.district_type,
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
