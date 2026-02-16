"""Update project coordinates from seed data."""

import json
from pathlib import Path

from src.db.connection import get_session
from src.db.models import Project
from src.config import SEED_DIR


def update_project_coordinates():
    """Update latitude/longitude for projects from seed file."""
    # Load projects from seed file
    projects_file = SEED_DIR / "projects.json"
    with open(projects_file, "r", encoding="utf-8") as f:
        projects_data = json.load(f)

    # Create lookup by project ID
    coords_by_id = {}
    for proj_data in projects_data:
        proj_id = proj_data.get("id")
        lat = proj_data.get("latitude")
        lon = proj_data.get("longitude")
        if proj_id and lat is not None and lon is not None:
            coords_by_id[proj_id] = (lat, lon)

    print(f"Found {len(coords_by_id)} projects with coordinates in seed file")

    # Update database
    updated_count = 0
    with get_session() as session:
        for proj_id, (lat, lon) in coords_by_id.items():
            project = session.query(Project).filter_by(id=proj_id).first()
            if project:
                project.latitude = lat
                project.longitude = lon
                updated_count += 1

        session.commit()

    print(f"Updated {updated_count} projects with coordinates")


if __name__ == "__main__":
    update_project_coordinates()
