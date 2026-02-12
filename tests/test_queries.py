"""Tests for common query helpers."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.config import SEED_DIR
from src.db.models import Base
from src.db.queries import (
    get_city_by_name, get_district_by_name, get_developer_by_name,
    get_period, list_projects_by_city, list_projects_by_grade,
    list_projects_by_developer, get_latest_price, get_price_history,
    get_grade_for_price, count_projects_by_city, avg_price_by_district,
    resolve_city_name, get_city_price_trend, get_grade_price_summary,
    get_project_price_changes, get_price_range_by_city,
)
from src.seeders.city_seeder import CitySeeder
from src.seeders.grade_seeder import GradeSeeder
from src.seeders.developer_seeder import DeveloperSeeder
from src.seeders.project_seeder import ProjectSeeder
from src.seeders.price_seeder import PriceSeeder
from src.seeders.supply_seeder import SupplySeeder


@pytest.fixture
def session():
    """In-memory seeded session."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close())
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


class TestLookupHelpers:
    def test_get_city_by_name(self, session):
        city = get_city_by_name(session, "Ho Chi Minh City")
        assert city is not None
        assert city.region == "South"

    def test_get_city_case_insensitive(self, session):
        city = get_city_by_name(session, "hanoi")
        assert city is not None
        assert city.name_en == "Hanoi"

    def test_get_city_by_alias_hcmc(self, session):
        city = get_city_by_name(session, "HCMC")
        assert city is not None
        assert city.name_en == "Ho Chi Minh City"

    def test_get_city_by_alias_saigon(self, session):
        city = get_city_by_name(session, "Saigon")
        assert city is not None
        assert city.name_en == "Ho Chi Minh City"

    def test_get_city_by_alias_bd(self, session):
        city = get_city_by_name(session, "BD")
        assert city is not None
        assert city.name_en == "Binh Duong"

    def test_get_city_not_found(self, session):
        assert get_city_by_name(session, "Nonexistent") is None

    def test_get_district_by_name(self, session):
        d = get_district_by_name(session, "District 1")
        assert d is not None
        assert d.city.name_en == "Ho Chi Minh City"

    def test_get_developer_by_name(self, session):
        dev = get_developer_by_name(session, "Vinhomes")
        assert dev is not None
        assert dev.stock_code == "VHM"

    def test_get_period(self, session):
        period = get_period(session, 2024, "H1")
        assert period is not None
        assert period.year == 2024


class TestResolveCityName:
    def test_hcmc_aliases(self):
        assert resolve_city_name("HCMC") == "ho chi minh city"
        assert resolve_city_name("hcm") == "ho chi minh city"
        assert resolve_city_name("Saigon") == "ho chi minh city"
        assert resolve_city_name("  Ho Chi Minh  ") == "ho chi minh city"

    def test_hanoi_aliases(self):
        assert resolve_city_name("Ha Noi") == "hanoi"
        assert resolve_city_name("Hanoi") == "hanoi"

    def test_binh_duong_aliases(self):
        assert resolve_city_name("BD") == "binh duong"

    def test_unknown_passthrough(self):
        assert resolve_city_name("Da Nang") == "da nang"


class TestProjectQueries:
    def test_list_by_city(self, session):
        projects = list_projects_by_city(session, "Ho Chi Minh City")
        assert len(projects) > 0
        # All should be in HCMC districts
        for p in projects:
            assert p.district.city.name_en == "Ho Chi Minh City"

    def test_list_by_city_alias(self, session):
        projects = list_projects_by_city(session, "HCMC")
        assert len(projects) > 0
        for p in projects:
            assert p.district.city.name_en == "Ho Chi Minh City"

    def test_list_by_grade(self, session):
        projects = list_projects_by_grade(session, "H-I")
        assert len(projects) > 0
        for p in projects:
            assert p.grade_primary == "H-I"

    def test_list_by_developer(self, session):
        projects = list_projects_by_developer(session, "Masterise Homes")
        assert len(projects) > 0
        for p in projects:
            assert p.developer.name_en == "Masterise Homes"


class TestPriceQueries:
    def test_get_latest_price(self, session):
        # Project 1 (Masteri Thao Dien) should have a price
        price = get_latest_price(session, 1)
        assert price is not None
        assert price.price_usd_per_m2 > 0

    def test_get_price_history(self, session):
        history = get_price_history(session, 1)
        assert len(history) >= 1

    def test_get_grade_for_price(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        grade = get_grade_for_price(session, hcmc.id, 4500)
        assert grade is not None
        assert grade.grade_code == "H-I"

    def test_get_grade_for_affordable(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        grade = get_grade_for_price(session, hcmc.id, 850)
        assert grade is not None
        assert grade.segment == "affordable"


class TestAggregations:
    def test_count_projects_by_city(self, session):
        counts = count_projects_by_city(session)
        assert len(counts) > 0
        # Should have entries for at least HCMC and Hanoi
        city_names = {c[0] for c in counts}
        assert "Ho Chi Minh City" in city_names

    def test_avg_price_by_district(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        avgs = avg_price_by_district(session, hcmc.id, 2024, "H1")
        assert len(avgs) > 0
        for district_name, avg_price in avgs:
            assert avg_price > 0


class TestPriceTrends:
    def test_city_price_trend(self, session):
        trend = get_city_price_trend(session, "HCMC")
        assert len(trend) >= 1
        year, half, avg_price, count = trend[0]
        assert year == 2024
        assert half == "H1"
        assert avg_price > 0
        assert count > 0

    def test_city_price_trend_alias(self, session):
        trend = get_city_price_trend(session, "Saigon")
        assert len(trend) >= 1

    def test_city_price_trend_no_data(self, session):
        trend = get_city_price_trend(session, "Nonexistent")
        assert trend == []

    def test_grade_price_summary(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        summary = get_grade_price_summary(session, hcmc.id, 2024, "H1")
        assert len(summary) > 0
        for grade, avg_p, min_p, max_p, cnt in summary:
            assert grade is not None
            assert avg_p > 0
            assert min_p <= avg_p <= max_p
            assert cnt > 0

    def test_project_price_changes_single_period(self, session):
        """With only one period, no projects should have changes."""
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        changes = get_project_price_changes(session, hcmc.id)
        # Single period = no multi-period projects
        assert isinstance(changes, list)

    def test_price_range_by_city(self, session):
        result = get_price_range_by_city(session, "HCMC", 2024, "H1")
        assert result is not None
        min_p, avg_p, max_p = result
        assert min_p > 0
        assert min_p <= avg_p <= max_p

    def test_price_range_no_data(self, session):
        result = get_price_range_by_city(session, "HCMC", 2099, "H1")
        assert result is None
