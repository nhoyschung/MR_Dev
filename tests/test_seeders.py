"""Tests for the seeder pipeline."""

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from src.config import SEED_DIR
from src.db.models import (
    Base, City, District, Developer, Project, PriceRecord,
    ReportPeriod, GradeDefinition, SupplyRecord,
)
from src.seeders.city_seeder import CitySeeder
from src.seeders.grade_seeder import GradeSeeder
from src.seeders.developer_seeder import DeveloperSeeder
from src.seeders.project_seeder import ProjectSeeder
from src.seeders.price_seeder import PriceSeeder
from src.seeders.supply_seeder import SupplySeeder


@pytest.fixture
def db_session():
    """In-memory DB with all tables."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close())
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def seeded_session(db_session):
    """Session with all seed data loaded."""
    seed_dir = SEED_DIR

    CitySeeder(db_session, seed_dir).seed()
    GradeSeeder(db_session, seed_dir).seed()
    DeveloperSeeder(db_session, seed_dir).seed()
    ProjectSeeder(db_session, seed_dir).seed()
    PriceSeeder(db_session, seed_dir).seed()
    SupplySeeder(db_session, seed_dir).seed()

    return db_session


class TestCitySeeder:
    def test_seed_cities(self, db_session):
        count = CitySeeder(db_session, SEED_DIR).seed()
        assert count > 0
        cities = db_session.query(City).all()
        assert len(cities) == 3
        names = {c.name_en for c in cities}
        assert "Ho Chi Minh City" in names
        assert "Hanoi" in names
        assert "Binh Duong" in names

    def test_seed_districts(self, db_session):
        CitySeeder(db_session, SEED_DIR).seed()
        districts = db_session.query(District).all()
        assert len(districts) >= 40

    def test_idempotent(self, db_session):
        seeder = CitySeeder(db_session, SEED_DIR)
        count1 = seeder.seed()
        count2 = seeder.seed()
        assert count2 == 0  # No new records on second run


class TestGradeSeeder:
    def test_seed_grades(self, db_session):
        CitySeeder(db_session, SEED_DIR).seed()
        count = GradeSeeder(db_session, SEED_DIR).seed()
        assert count > 0
        grades = db_session.query(GradeDefinition).all()
        assert len(grades) >= 18

    def test_periods_created(self, db_session):
        CitySeeder(db_session, SEED_DIR).seed()
        GradeSeeder(db_session, SEED_DIR).seed()
        periods = db_session.query(ReportPeriod).all()
        assert len(periods) >= 6  # 2023 H1/H2, 2024 H1/H2, 2025 H1/H2


class TestDeveloperSeeder:
    def test_seed_developers(self, db_session):
        CitySeeder(db_session, SEED_DIR).seed()
        count = DeveloperSeeder(db_session, SEED_DIR).seed()
        assert count > 0
        devs = db_session.query(Developer).all()
        assert len(devs) >= 15


class TestProjectSeeder:
    def test_seed_projects(self, db_session):
        CitySeeder(db_session, SEED_DIR).seed()
        GradeSeeder(db_session, SEED_DIR).seed()
        DeveloperSeeder(db_session, SEED_DIR).seed()
        count = ProjectSeeder(db_session, SEED_DIR).seed()
        assert count > 0
        projects = db_session.query(Project).all()
        assert len(projects) >= 40


class TestPriceSeeder:
    def test_seed_prices(self, db_session):
        CitySeeder(db_session, SEED_DIR).seed()
        GradeSeeder(db_session, SEED_DIR).seed()
        DeveloperSeeder(db_session, SEED_DIR).seed()
        ProjectSeeder(db_session, SEED_DIR).seed()
        count = PriceSeeder(db_session, SEED_DIR).seed()
        assert count > 0
        prices = db_session.query(PriceRecord).all()
        assert len(prices) >= 30


class TestSupplySeeder:
    def test_seed_supply(self, db_session):
        CitySeeder(db_session, SEED_DIR).seed()
        GradeSeeder(db_session, SEED_DIR).seed()
        count = SupplySeeder(db_session, SEED_DIR).seed()
        assert count > 0
        records = db_session.query(SupplyRecord).all()
        assert len(records) >= 15


class TestFullPipeline:
    def test_full_seed(self, seeded_session):
        """Run the full pipeline and verify counts."""
        session = seeded_session
        assert session.query(City).count() == 3
        assert session.query(District).count() >= 40
        assert session.query(Developer).count() >= 15
        assert session.query(Project).count() >= 50
        assert session.query(PriceRecord).count() >= 40
        assert session.query(ReportPeriod).count() >= 6
        assert session.query(GradeDefinition).count() >= 18

    def test_city_district_relationship(self, seeded_session):
        hcmc = seeded_session.query(City).filter_by(name_en="Ho Chi Minh City").first()
        assert hcmc is not None
        assert len(hcmc.districts) >= 15

    def test_project_has_price(self, seeded_session):
        """Projects with prices should have valid records."""
        prices = seeded_session.query(PriceRecord).all()
        for price in prices[:5]:
            assert price.project is not None
            assert price.period is not None
            assert price.price_usd_per_m2 > 0
