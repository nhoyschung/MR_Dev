"""Seeder for projects from PDF data."""

from pydantic import BaseModel
from typing import Optional

from src.db.models import Project
from src.seeders.base_seeder import BaseSeeder


class ProjectSchema(BaseModel):
    id: int
    name: str
    developer_id: Optional[int] = None
    district_id: Optional[int] = None
    ward_id: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_area_m2: Optional[float] = None
    total_units: Optional[int] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    launch_date: Optional[str] = None
    completion_date: Optional[str] = None
    grade_primary: Optional[str] = None
    grade_secondary: Optional[str] = None


class ProjectSeeder(BaseSeeder):
    """Seeds project records."""

    def validate(self) -> bool:
        projects = self.load_json("projects.json")
        for p in projects:
            ProjectSchema(**p)
        return True

    def seed(self) -> int:
        count = 0
        projects = self.load_json("projects.json")
        for p_data in projects:
            validated = ProjectSchema(**p_data)
            _, created = self._get_or_create(
                Project,
                name=validated.name,
                defaults={
                    "developer_id": validated.developer_id,
                    "district_id": validated.district_id,
                    "ward_id": validated.ward_id,
                    "address": validated.address,
                    "latitude": validated.latitude,
                    "longitude": validated.longitude,
                    "total_area_m2": validated.total_area_m2,
                    "total_units": validated.total_units,
                    "project_type": validated.project_type,
                    "status": validated.status,
                    "launch_date": validated.launch_date,
                    "completion_date": validated.completion_date,
                    "grade_primary": validated.grade_primary,
                    "grade_secondary": validated.grade_secondary,
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
