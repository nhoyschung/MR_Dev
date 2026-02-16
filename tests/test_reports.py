"""Tests for report renderers."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.config import SEED_DIR
from src.db.models import Base
from src.seeders.city_seeder import CitySeeder
from src.seeders.grade_seeder import GradeSeeder
from src.seeders.developer_seeder import DeveloperSeeder
from src.seeders.project_seeder import ProjectSeeder
from src.seeders.price_seeder import PriceSeeder
from src.seeders.supply_seeder import SupplySeeder
from src.reports.renderer import render_template
from src.reports.market_briefing import render_market_briefing
from src.reports.project_profile import render_project_profile
from src.reports.zone_analysis import render_zone_analysis


@pytest.fixture
def session():
    """In-memory seeded session."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close(),
    )
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()

    CitySeeder(s, SEED_DIR).seed()
    GradeSeeder(s, SEED_DIR).seed()
    DeveloperSeeder(s, SEED_DIR).seed()
    ProjectSeeder(s, SEED_DIR).seed()
    PriceSeeder(s, SEED_DIR).seed()
    SupplySeeder(s, SEED_DIR).seed()

    yield s
    s.close()


class TestRenderer:
    def test_render_template(self):
        result = render_template(
            "market_briefing.md.j2",
            city_name="Test City",
            period="2024-H1",
            generated_date="2024-01-01",
            project_count=10,
            active_selling=5,
            under_construction=2,
            avg_price_usd=3000,
            avg_absorption=65.5,
            grades=[],
            top_districts_by_price=[],
            top_districts_by_supply=[],
            price_changes=[],
            supply_pipeline=[],
            takeaways=["Test takeaway"],
        )
        assert "Test City Market Briefing" in result
        assert "2024-H1" in result
        assert "$3000" in result


class TestMarketBriefing:
    def test_render_hcmc(self, session):
        result = render_market_briefing(session, "HCMC", 2024, "H1")
        assert result is not None
        assert "Ho Chi Minh City" in result
        assert "Market Snapshot" in result
        assert "Grade Distribution" in result
        assert "District Highlights" in result

    def test_render_hanoi(self, session):
        result = render_market_briefing(session, "Hanoi", 2024, "H1")
        assert result is not None
        assert "Hanoi" in result

    def test_render_alias(self, session):
        result = render_market_briefing(session, "Saigon", 2024, "H1")
        assert result is not None
        assert "Ho Chi Minh City" in result

    def test_city_not_found(self, session):
        result = render_market_briefing(session, "Nonexistent", 2024, "H1")
        assert result is None

    def test_period_not_found(self, session):
        result = render_market_briefing(session, "HCMC", 2099, "H1")
        assert result is None


class TestProjectProfile:
    def test_render_exact_name(self, session):
        result = render_project_profile(session, "Masteri Thao Dien")
        assert result is not None
        assert "Masteri Thao Dien" in result
        assert "Masterise Homes" in result
        assert "District 2" in result

    def test_render_substring(self, session):
        result = render_project_profile(session, "Masteri")
        assert result is not None

    def test_project_not_found(self, session):
        result = render_project_profile(session, "ZZZZZ Nonexistent")
        assert result is None

    def test_grade_peers_present(self, session):
        result = render_project_profile(session, "Masteri Thao Dien")
        assert "Grade Peers" in result

    def test_developer_hq_not_repr(self, session):
        """Developer HQ should show city name, not <City ...> repr."""
        result = render_project_profile(session, "Masteri Thao Dien")
        assert "<City" not in result


class TestZoneAnalysis:
    def test_render_zone_analysis_hcmc(self, session):
        result = render_zone_analysis(session, "District 2", "HCMC", 2024, "H1")
        assert result is not None
        assert "Zone Analysis: District 2, Ho Chi Minh City" in result
        assert "Supply Analysis" in result
        assert "Project Roster" in result

    def test_render_zone_analysis_alias_city(self, session):
        result = render_zone_analysis(session, "District 2", "Saigon", 2024, "H1")
        assert result is not None
        assert "Ho Chi Minh City" in result

    def test_render_zone_analysis_district_not_found(self, session):
        result = render_zone_analysis(session, "NoSuchDistrict", "HCMC", 2024, "H1")
        assert result is None

    def test_render_zone_analysis_period_not_found(self, session):
        result = render_zone_analysis(session, "District 2", "HCMC", 2099, "H1")
        assert result is None
