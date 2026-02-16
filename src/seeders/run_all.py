"""Orchestrator: run all seeders in dependency order."""

import sys
from pathlib import Path

from src.config import SEED_DIR
from src.db.models import Base
from src.db.connection import engine, get_session
from src.db.init_db import ensure_schema_compatibility
from src.seeders.city_seeder import CitySeeder
from src.seeders.grade_seeder import GradeSeeder
from src.seeders.developer_seeder import DeveloperSeeder
from src.seeders.project_seeder import ProjectSeeder
from src.seeders.price_seeder import PriceSeeder
from src.seeders.supply_seeder import SupplySeeder
from src.seeders.source_report_seeder import SourceReportSeeder
from src.seeders.block_seeder import BlockSeeder
from src.seeders.unit_type_seeder import UnitTypeSeeder
from src.seeders.facility_seeder import FacilitySeeder
from src.seeders.sales_point_seeder import SalesPointSeeder
from src.seeders.price_factor_seeder import PriceFactorSeeder
from src.seeders.sales_status_seeder import SalesStatusSeeder
from src.seeders.market_segment_seeder import MarketSegmentSeeder
from src.seeders.district_metric_seeder import DistrictMetricSeeder
from src.seeders.competitor_seeder import CompetitorSeeder


SEEDERS = [
    # Existing (1-6)
    ("Cities & Districts", CitySeeder),
    ("Grades & Periods", GradeSeeder),
    ("Developers", DeveloperSeeder),
    ("Projects", ProjectSeeder),
    ("Prices", PriceSeeder),
    ("Supply", SupplySeeder),
    # New (7-16) — depend on extracted JSON from run_extractors
    ("Source Reports", SourceReportSeeder),
    ("Blocks", BlockSeeder),
    ("Unit Types", UnitTypeSeeder),
    ("Facilities", FacilitySeeder),
    ("Sales Points", SalesPointSeeder),
    ("Price Factors", PriceFactorSeeder),
    ("Sales Statuses", SalesStatusSeeder),
    ("Market Segments", MarketSegmentSeeder),
    ("District Metrics", DistrictMetricSeeder),
    ("Competitors", CompetitorSeeder),
]


def run_all(seed_dir: Path | None = None) -> dict[str, int]:
    """Run all seeders in dependency order. Returns {name: count} dict."""
    seed_dir = seed_dir or SEED_DIR

    # Ensure tables exist
    Base.metadata.create_all(engine)
    ensure_schema_compatibility()

    session = get_session()
    results: dict[str, int] = {}

    try:
        for name, seeder_class in SEEDERS:
            print(f"Seeding {name}...", end=" ")
            seeder = seeder_class(session, seed_dir)
            try:
                seeder.validate()
                count = seeder.seed()
                results[name] = count
                print(f"{count} records created.")
            except FileNotFoundError:
                results[name] = 0
                print("Skipped (no extracted data yet).")
            except Exception as e:
                results[name] = 0
                print(f"Error: {e}")
    except Exception as e:
        session.rollback()
        print(f"\nError during seeding: {e}")
        raise
    finally:
        session.close()

    print(f"\nSeeding complete. Total: {sum(results.values())} records.")
    return results


if __name__ == "__main__":
    run_all()
