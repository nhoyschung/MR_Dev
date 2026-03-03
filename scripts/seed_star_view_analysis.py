"""Seed Star View unit-type analysis data: projects, unit types, and price records.

Creates new projects (Starview, Emerald 68, Symlife, etc.) if not present,
then populates UnitType + PriceRecord with unit_type_id FK.

Usage:
    python -m scripts.seed_star_view_analysis
"""

import json
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SEED_DIR
from src.db.models import Base, Project, UnitType, PriceRecord, ReportPeriod, District
from src.db.connection import engine, get_session
from src.db.init_db import ensure_schema_compatibility

# Project definitions (created only if not already in DB)
PROJECT_DEFS = [
    {
        "name": "Starview",
        "district_name": "Thuan An",
        "grade_primary": "H-II",
        "project_type": "mixed-use",
        "status": "planning",
        "launch_date": "2026",
        "completion_date": "2029",
    },
    {
        "name": "The Emerald 68",
        "district_name": "Thuan An",
        "grade_primary": "H-II",
        "project_type": "apartment",
        "status": "selling",
        "launch_date": "2025-Q2",
        "completion_date": "2026-Q3",
    },
    {
        "name": "Symlife",
        "district_name": "Thuan An",
        "grade_primary": "M-I",
        "project_type": "apartment",
        "status": "selling",
        "launch_date": "2025-Q3",
        "completion_date": "2027-Q4",
    },
    {
        "name": "Emerald Boulevard",
        "district_name": "Di An",
        "grade_primary": "H-II",
        "project_type": "apartment",
        "status": "planning",
        "launch_date": "2027",
    },
    {
        "name": "Happy One Mori",
        "district_name": "Thuan An",
        "grade_primary": "M-I",
        "project_type": "apartment",
        "status": "selling",
    },
]


def _get_or_create_project(session, name: str, district_name: str, **kwargs) -> Project:
    """Get existing project or create new one."""
    existing = session.query(Project).filter(
        Project.name.ilike(name)
    ).first()
    if existing:
        print(f"  [exists] Project '{name}' (id={existing.id})")
        return existing

    # Find district
    district = session.query(District).filter(
        District.name_en.ilike(district_name)
    ).first()
    district_id = district.id if district else None

    project = Project(name=name, district_id=district_id, **kwargs)
    session.add(project)
    session.flush()
    print(f"  [created] Project '{name}' (id={project.id})")
    return project


def _get_or_create_period(session, year: int = 2025, half: str = "H2") -> ReportPeriod:
    """Get or create report period."""
    period = session.query(ReportPeriod).filter_by(year=year, half=half).first()
    if period:
        return period
    period = ReportPeriod(year=year, half=half)
    session.add(period)
    session.flush()
    return period


def seed_star_view_analysis() -> dict[str, int]:
    """Main seeding function. Returns {metric: count} dict."""
    Base.metadata.create_all(engine)
    ensure_schema_compatibility()
    session = get_session()

    stats = {"projects_created": 0, "unit_types_created": 0, "price_records_created": 0}

    try:
        # 1. Ensure projects exist
        projects_map: dict[str, Project] = {}
        for pdef in PROJECT_DEFS:
            name = pdef.pop("name")
            district_name = pdef.pop("district_name")
            proj = _get_or_create_project(session, name, district_name, **pdef)
            projects_map[name.lower()] = proj
            # Restore for next run
            pdef["name"] = name
            pdef["district_name"] = district_name

        # A&T Saigon Riverside should already exist (id=17)
        at_sg = session.query(Project).filter(
            Project.name.ilike("%A&T Saigon%")
        ).first()
        if at_sg:
            projects_map["a&t saigon riverside"] = at_sg
            print(f"  [exists] A&T Saigon Riverside (id={at_sg.id})")

        # 2. Load seed data
        seed_path = SEED_DIR / "unit_type_prices.json"
        if not seed_path.exists():
            print(f"ERROR: Seed file not found: {seed_path}")
            return stats

        with open(seed_path, encoding="utf-8") as f:
            seed_data = json.load(f)

        # 3. Get/create period
        period = _get_or_create_period(session, 2025, "H2")

        # 4. Process each project's unit types
        for proj_data in seed_data:
            proj_name = proj_data["project_name"]
            proj = projects_map.get(proj_name.lower())
            if not proj:
                # Try fuzzy match
                for key, p in projects_map.items():
                    if proj_name.lower() in key or key in proj_name.lower():
                        proj = p
                        break
            if not proj:
                print(f"  [skip] Project '{proj_name}' not found in DB")
                continue

            for ut_data in proj_data.get("unit_types", []):
                type_name = ut_data["type_name"]
                net_area = ut_data["net_area_m2"]
                price_usd = ut_data["price_usd_per_m2"]
                price_vnd = ut_data["price_vnd_per_m2"]

                # Check if UnitType already exists for this project + type_name
                existing_ut = session.query(UnitType).filter_by(
                    project_id=proj.id, type_name=type_name
                ).first()

                if existing_ut:
                    ut = existing_ut
                else:
                    ut = UnitType(
                        project_id=proj.id,
                        type_name=type_name,
                        net_area_m2=net_area,
                    )
                    session.add(ut)
                    session.flush()
                    stats["unit_types_created"] += 1

                # Check if PriceRecord with this unit_type_id already exists
                existing_pr = session.query(PriceRecord).filter_by(
                    project_id=proj.id,
                    unit_type_id=ut.id,
                    period_id=period.id,
                ).first()

                if not existing_pr:
                    pr = PriceRecord(
                        project_id=proj.id,
                        unit_type_id=ut.id,
                        period_id=period.id,
                        price_usd_per_m2=price_usd,
                        price_vnd_per_m2=price_vnd,
                        data_source="nho_internal",
                    )
                    session.add(pr)
                    stats["price_records_created"] += 1

            session.flush()

        session.commit()
        print(f"\nSeeding complete: {stats}")
        return stats

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_star_view_analysis()
