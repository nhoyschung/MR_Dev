"""Tests for database models: table creation, relationships, basic CRUD."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import (
    Base, City, District, Ward, ReportPeriod, GradeDefinition,
    Developer, Project, ProjectBlock, UnitType, PriceRecord,
    PriceChangeFactor, SupplyRecord, SalesStatus, ProjectFacility,
    ProjectSalesPoint, CompetitorComparison, MarketSegmentSummary,
    SourceReport, DataLineage, DistrictMetric,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close())
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


class TestTableCreation:
    def test_all_tables_created(self, db_session: Session):
        """All 20 tables should be created."""
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "cities", "districts", "wards", "report_periods",
            "grade_definitions", "developers", "projects", "project_blocks",
            "unit_types", "price_records", "price_change_factors",
            "supply_records", "sales_statuses", "project_facilities",
            "project_sales_points", "competitor_comparisons",
            "market_segment_summaries", "source_reports", "data_lineage",
            "district_metrics",
        }
        assert expected == table_names

    def test_table_count(self, db_session: Session):
        assert len(Base.metadata.tables) == 20


class TestCRUD:
    def test_create_city(self, db_session: Session):
        city = City(name_en="Test City", name_vi="TP Test", region="South")
        db_session.add(city)
        db_session.commit()
        assert city.id is not None
        assert city.name_en == "Test City"

    def test_create_district_with_city(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()

        district = District(name_en="District 1", city_id=city.id, district_type="urban")
        db_session.add(district)
        db_session.commit()

        assert district.city.name_en == "HCMC"
        assert len(city.districts) == 1

    def test_create_ward(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()
        district = District(name_en="D1", city_id=city.id)
        db_session.add(district)
        db_session.flush()
        ward = Ward(name_en="Ben Nghe", district_id=district.id)
        db_session.add(ward)
        db_session.commit()

        assert ward.district.name_en == "D1"

    def test_create_developer(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()

        dev = Developer(name_en="Test Dev", stock_code="TST", hq_city_id=city.id)
        db_session.add(dev)
        db_session.commit()

        assert dev.hq_city.name_en == "HCMC"

    def test_create_project_with_relationships(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()

        district = District(name_en="D2", city_id=city.id)
        db_session.add(district)
        db_session.flush()

        dev = Developer(name_en="Builder Co", hq_city_id=city.id)
        db_session.add(dev)
        db_session.flush()

        project = Project(
            name="Test Project",
            developer_id=dev.id,
            district_id=district.id,
            total_units=500,
            project_type="apartment",
            status="selling",
            grade_primary="M-I",
        )
        db_session.add(project)
        db_session.commit()

        assert project.developer.name_en == "Builder Co"
        assert project.district.name_en == "D2"
        assert len(dev.projects) == 1

    def test_create_project_block(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()
        district = District(name_en="D7", city_id=city.id)
        db_session.add(district)
        db_session.flush()
        project = Project(name="Block Test", district_id=district.id)
        db_session.add(project)
        db_session.flush()

        block = ProjectBlock(project_id=project.id, block_name="Block A", floors=30, total_units=300)
        db_session.add(block)
        db_session.commit()

        assert block.project.name == "Block Test"
        assert len(project.blocks) == 1

    def test_create_price_record(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()
        district = District(name_en="D2", city_id=city.id)
        db_session.add(district)
        db_session.flush()
        project = Project(name="Price Test", district_id=district.id)
        db_session.add(project)
        db_session.flush()
        period = ReportPeriod(year=2024, half="H1")
        db_session.add(period)
        db_session.flush()

        price = PriceRecord(
            project_id=project.id,
            period_id=period.id,
            price_usd_per_m2=3500.0,
            price_vnd_per_m2=87500000.0,
        )
        db_session.add(price)
        db_session.commit()

        assert price.project.name == "Price Test"
        assert price.period.year == 2024

    def test_price_change_factor(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()
        district = District(name_en="D2", city_id=city.id)
        db_session.add(district)
        db_session.flush()
        project = Project(name="Factor Test", district_id=district.id)
        db_session.add(project)
        db_session.flush()
        period = ReportPeriod(year=2024, half="H1")
        db_session.add(period)
        db_session.flush()
        price = PriceRecord(project_id=project.id, period_id=period.id, price_usd_per_m2=3000)
        db_session.add(price)
        db_session.flush()

        factor = PriceChangeFactor(
            price_record_id=price.id,
            factor_type="increase",
            factor_category="location",
            description="Near metro station",
        )
        db_session.add(factor)
        db_session.commit()

        assert len(price.change_factors) == 1
        assert factor.price_record.price_usd_per_m2 == 3000

    def test_competitor_comparison(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()
        district = District(name_en="D2", city_id=city.id)
        db_session.add(district)
        db_session.flush()
        p1 = Project(name="Subject", district_id=district.id)
        p2 = Project(name="Competitor", district_id=district.id)
        db_session.add_all([p1, p2])
        db_session.flush()
        period = ReportPeriod(year=2024, half="H1")
        db_session.add(period)
        db_session.flush()

        comp = CompetitorComparison(
            subject_project_id=p1.id,
            competitor_project_id=p2.id,
            period_id=period.id,
            dimension="location",
            subject_score=8.0,
            competitor_score=7.0,
        )
        db_session.add(comp)
        db_session.commit()

        assert comp.subject_project.name == "Subject"
        assert comp.competitor_project.name == "Competitor"

    def test_source_report_and_lineage(self, db_session: Session):
        report = SourceReport(filename="test.pdf", report_type="market_analysis")
        db_session.add(report)
        db_session.flush()

        lineage = DataLineage(
            table_name="projects",
            record_id=1,
            source_report_id=report.id,
            page_number=5,
            confidence_score=0.95,
        )
        db_session.add(lineage)
        db_session.commit()

        assert len(report.data_lineage_records) == 1
        assert lineage.source_report.filename == "test.pdf"

    def test_grade_definition(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()
        period = ReportPeriod(year=2024, half="H1")
        db_session.add(period)
        db_session.flush()

        grade = GradeDefinition(
            city_id=city.id,
            grade_code="H-I",
            min_price_usd=4000,
            max_price_usd=6000,
            segment="high-end",
            period_id=period.id,
        )
        db_session.add(grade)
        db_session.commit()

        assert grade.city.name_en == "HCMC"
        assert grade.segment == "high-end"

    def test_district_metric(self, db_session: Session):
        city = City(name_en="HCMC", region="South")
        db_session.add(city)
        db_session.flush()
        district = District(name_en="D7", city_id=city.id)
        db_session.add(district)
        db_session.flush()
        period = ReportPeriod(year=2024, half="H1")
        db_session.add(period)
        db_session.flush()

        metric = DistrictMetric(
            district_id=district.id,
            period_id=period.id,
            metric_type="avg_price",
            value_numeric=3200.0,
        )
        db_session.add(metric)
        db_session.commit()

        assert metric.district.name_en == "D7"
        assert metric.value_numeric == 3200.0
