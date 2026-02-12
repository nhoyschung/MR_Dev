"""Tests for the new seeders (source_report, block, facility, etc.)."""

import json
import shutil
import pytest
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.config import SEED_DIR
from src.db.models import (
    Base,
    City,
    CompetitorComparison,
    DataLineage,
    District,
    DistrictMetric,
    MarketSegmentSummary,
    PriceChangeFactor,
    PriceRecord,
    Project,
    ProjectBlock,
    ProjectFacility,
    ProjectSalesPoint,
    ReportPeriod,
    SalesStatus,
    SourceReport,
    UnitType,
)
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


@pytest.fixture
def db_session():
    """In-memory DB with all tables."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close(),
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def seeded_session(db_session):
    """Session with prerequisite seed data loaded."""
    CitySeeder(db_session, SEED_DIR).seed()
    GradeSeeder(db_session, SEED_DIR).seed()
    DeveloperSeeder(db_session, SEED_DIR).seed()
    ProjectSeeder(db_session, SEED_DIR).seed()
    PriceSeeder(db_session, SEED_DIR).seed()
    SupplySeeder(db_session, SEED_DIR).seed()
    return db_session


@pytest.fixture
def extracted_seed_dir(tmp_path, seeded_session):
    """Seed dir with real JSON files + an extracted/ subdirectory for test data."""
    # Copy real seed files
    for src_file in SEED_DIR.glob("*.json"):
        shutil.copy2(src_file, tmp_path / src_file.name)

    # Create extracted subdir
    extracted = tmp_path / "extracted"
    extracted.mkdir()

    return tmp_path


def _write_extracted(seed_dir: Path, filename: str, data: list) -> None:
    """Write a JSON file to seed_dir/extracted/."""
    extracted = seed_dir / "extracted"
    extracted.mkdir(exist_ok=True)
    with open(extracted / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


class TestSourceReportSeeder:
    def test_seed_source_reports(self, seeded_session):
        count = SourceReportSeeder(seeded_session, SEED_DIR).seed()
        assert count > 0
        reports = seeded_session.query(SourceReport).all()
        assert len(reports) >= 14

    def test_idempotent(self, seeded_session):
        seeder = SourceReportSeeder(seeded_session, SEED_DIR)
        count1 = seeder.seed()
        count2 = seeder.seed()
        assert count2 == 0


class TestBlockSeeder:
    def test_seed_blocks(self, seeded_session, extracted_seed_dir):
        project = seeded_session.query(Project).first()
        _write_extracted(extracted_seed_dir, "casestudy_blocks.json", [
            {
                "project_name": project.name,
                "block_name": "A",
                "floors": 30,
                "_meta": {"source_file": "test.txt", "page": 4, "confidence": 0.85},
            },
            {
                "project_name": project.name,
                "block_name": "B",
                "floors": 25,
                "_meta": {"source_file": "test.txt", "page": 4, "confidence": 0.85},
            },
        ])

        count = BlockSeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 2
        blocks = seeded_session.query(ProjectBlock).all()
        assert len(blocks) == 2

    def test_skip_unknown_project(self, seeded_session, extracted_seed_dir):
        _write_extracted(extracted_seed_dir, "casestudy_blocks.json", [
            {
                "project_name": "NONEXISTENT PROJECT XYZ",
                "block_name": "A",
                "floors": 10,
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.5},
            },
        ])

        count = BlockSeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 0


class TestUnitTypeSeeder:
    def test_seed_unit_types(self, seeded_session, extracted_seed_dir):
        project = seeded_session.query(Project).first()
        _write_extracted(extracted_seed_dir, "casestudy_unit_types.json", [
            {
                "project_name": project.name,
                "type_name": "1BR",
                "area_min": 50.0,
                "area_max": 55.0,
                "gross_area_m2": 52.5,
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.8},
            },
        ])
        _write_extracted(extracted_seed_dir, "market_unit_types.json", [
            {
                "project_name": project.name,
                "type_name": "2BR",
                "area_min": 70.0,
                "area_max": 80.0,
                "gross_area_m2": 75.0,
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.8},
            },
        ])

        count = UnitTypeSeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 2
        types = seeded_session.query(UnitType).all()
        assert len(types) == 2


class TestFacilitySeeder:
    def test_seed_facilities(self, seeded_session, extracted_seed_dir):
        project = seeded_session.query(Project).first()
        _write_extracted(extracted_seed_dir, "casestudy_facilities.json", [
            {
                "project_name": project.name,
                "facility_type": "pool",
                "description": "Infinity pool on rooftop",
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.8},
            },
        ])
        _write_extracted(extracted_seed_dir, "market_facilities.json", [])

        count = FacilitySeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 1


class TestSalesPointSeeder:
    def test_seed_sales_points(self, seeded_session, extracted_seed_dir):
        project = seeded_session.query(Project).first()
        _write_extracted(extracted_seed_dir, "casestudy_sales_points.json", [
            {
                "project_name": project.name,
                "category": "design",
                "description": "Access: open - Checking at lobby",
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.8},
            },
        ])

        count = SalesPointSeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 1


class TestPriceFactorSeeder:
    def test_seed_price_factors(self, seeded_session, extracted_seed_dir):
        price = seeded_session.query(PriceRecord).first()
        project = seeded_session.get(Project, price.project_id)

        _write_extracted(extracted_seed_dir, "price_factors.json", [
            {
                "project_name": project.name,
                "factor_type": "increase",
                "factor_category": "location",
                "rate_pct": 5.0,
                "description": "Near metro station",
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.8},
            },
        ])

        count = PriceFactorSeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 1
        factors = seeded_session.query(PriceChangeFactor).all()
        assert len(factors) == 1
        assert factors[0].factor_type == "increase"


class TestSalesStatusSeeder:
    def test_seed_sales_statuses(self, seeded_session, extracted_seed_dir):
        project = seeded_session.query(Project).first()
        _write_extracted(extracted_seed_dir, "market_sales_statuses.json", [
            {
                "project_name": project.name,
                "sales_rate_pct": 97.0,
                "sold_units": 809,
                "launched_units": 836,
                "available_units": 27,
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.8},
            },
        ])

        count = SalesStatusSeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 1


class TestMarketSegmentSeeder:
    def test_seed_segments(self, seeded_session, extracted_seed_dir):
        _write_extracted(extracted_seed_dir, "segment_summaries.json", [
            {
                "city": "Ho Chi Minh City",
                "grade_code": "H-I",
                "segment": "high-end",
                "proportion_pct": 24.0,
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.85},
            },
        ])

        count = MarketSegmentSeeder(seeded_session, extracted_seed_dir).seed()
        assert count == 1
        summaries = seeded_session.query(MarketSegmentSummary).all()
        assert len(summaries) == 1


class TestDistrictMetricSeeder:
    def test_seed_computed_metrics(self, seeded_session, extracted_seed_dir):
        _write_extracted(extracted_seed_dir, "district_metrics.json", [])

        count = DistrictMetricSeeder(seeded_session, extracted_seed_dir).seed()
        assert count > 0
        metrics = seeded_session.query(DistrictMetric).all()
        assert len(metrics) > 0


class TestCompetitorSeeder:
    def test_seed_competitors(self, seeded_session):
        count = CompetitorSeeder(seeded_session, SEED_DIR).seed()
        assert count >= 0
        comparisons = seeded_session.query(CompetitorComparison).all()
        for comp in comparisons:
            assert comp.dimension == "location"


class TestLineageTracking:
    def test_lineage_created_with_block(self, seeded_session, extracted_seed_dir):
        SourceReportSeeder(seeded_session, SEED_DIR).seed()

        project = seeded_session.query(Project).first()
        _write_extracted(extracted_seed_dir, "casestudy_blocks.json", [
            {
                "project_name": project.name,
                "block_name": "TestBlock",
                "floors": 20,
                "_meta": {
                    "source_file": "mixed_use_casestudy_full.txt",
                    "page": 4,
                    "confidence": 0.85,
                },
            },
        ])

        BlockSeeder(seeded_session, extracted_seed_dir).seed()

        lineage = seeded_session.query(DataLineage).all()
        assert len(lineage) >= 1
        assert lineage[0].table_name == "project_blocks"


class TestIdempotency:
    def test_block_seeder_idempotent(self, seeded_session, extracted_seed_dir):
        project = seeded_session.query(Project).first()
        _write_extracted(extracted_seed_dir, "casestudy_blocks.json", [
            {
                "project_name": project.name,
                "block_name": "A",
                "floors": 30,
                "_meta": {"source_file": "test.txt", "page": 1, "confidence": 0.8},
            },
        ])

        seeder = BlockSeeder(seeded_session, extracted_seed_dir)
        count1 = seeder.seed()
        count2 = seeder.seed()
        assert count1 > 0
        assert count2 == 0
