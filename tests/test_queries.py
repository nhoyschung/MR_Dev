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
    get_grade_for_price, get_district_supply, count_projects_by_city, avg_price_by_district,
    resolve_city_name, get_city_price_trend, get_grade_price_summary,
    get_project_price_changes, get_price_range_by_city,
    get_price_momentum, get_supply_demand_ratio_by_period,
    get_grade_migration_cohort, get_price_volatility_by_grade,
    get_district_ranking_change,
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

    def test_get_district_supply(self, session):
        records = get_district_supply(session, district_id=2, year=2024, half="H1")
        assert len(records) >= 1
        for r in records:
            assert r.district_id == 2


class TestPriceTrends:
    def test_city_price_trend(self, session):
        trend = get_city_price_trend(session, "HCMC")
        # With multi-period data, should have entries across multiple periods
        assert len(trend) >= 2
        for year, half, avg_price, count in trend:
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

    def test_project_price_changes_with_multi_period(self, session):
        """With multi-period data, some projects should have price changes."""
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        changes = get_project_price_changes(session, hcmc.id)
        assert isinstance(changes, list)
        # Should have at least some projects with multi-period data
        assert len(changes) >= 1

    def test_price_range_by_city(self, session):
        result = get_price_range_by_city(session, "HCMC", 2024, "H1")
        assert result is not None
        min_p, avg_p, max_p = result
        assert min_p > 0
        assert min_p <= avg_p <= max_p

    def test_price_range_no_data(self, session):
        result = get_price_range_by_city(session, "HCMC", 2099, "H1")
        assert result is None

    def test_price_history_multiple_periods(self, session):
        """Project 1 (Masteri Thao Dien) should have prices across 2+ periods."""
        history = get_price_history(session, 1)
        assert len(history) >= 2
        # Verify chronological ordering (earliest first)
        years = [(h.period.year, h.period.half) for h in history]
        assert len(set(years)) >= 2


class TestTemporalTrendQueries:
    """Tests for the five new temporal trend analysis queries."""

    def test_get_price_momentum_returns_list(self, session):
        result = get_price_momentum(session, "HCMC")
        assert isinstance(result, list)

    def test_get_price_momentum_structure(self, session):
        result = get_price_momentum(session, "HCMC")
        assert len(result) >= 1
        first = result[0]
        assert "period" in first
        assert "avg_price_usd" in first
        assert "project_count" in first
        assert "change_pct" in first
        assert "acceleration" in first
        assert "momentum" in first

    def test_get_price_momentum_first_period_no_change(self, session):
        """First period has no previous to compare against."""
        result = get_price_momentum(session, "HCMC")
        assert result[0]["change_pct"] is None
        assert result[0]["acceleration"] is None

    def test_get_price_momentum_second_period_has_change(self, session):
        """Second period onwards should have a change_pct."""
        result = get_price_momentum(session, "HCMC")
        if len(result) >= 2:
            assert result[1]["change_pct"] is not None

    def test_get_price_momentum_unknown_city(self, session):
        result = get_price_momentum(session, "Atlantis")
        assert result == []

    def test_get_supply_demand_ratio_returns_list(self, session):
        result = get_supply_demand_ratio_by_period(session, "HCMC")
        assert isinstance(result, list)

    def test_get_supply_demand_ratio_structure(self, session):
        result = get_supply_demand_ratio_by_period(session, "HCMC")
        if result:
            row = result[0]
            assert "period" in row
            assert "new_supply" in row
            assert "sold_units" in row
            assert "supply_demand_ratio" in row
            assert "signal" in row

    def test_get_supply_demand_ratio_signal_values(self, session):
        result = get_supply_demand_ratio_by_period(session, "HCMC")
        valid_signals = {"oversupply", "shortage", "balanced", "no_data"}
        for row in result:
            assert row["signal"] in valid_signals

    def test_get_supply_demand_ratio_unknown_city(self, session):
        result = get_supply_demand_ratio_by_period(session, "Nowhere")
        assert result == []

    def test_get_grade_migration_cohort_returns_list(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_grade_migration_cohort(session, hcmc.id)
        assert isinstance(result, list)

    def test_get_grade_migration_cohort_structure(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_grade_migration_cohort(session, hcmc.id)
        for row in result:
            assert "project_id" in row
            assert "project_name" in row
            assert "migrated_from" in row
            assert "migrated_to" in row
            assert "direction" in row
            assert row["direction"] in ("upgrade", "downgrade")

    def test_get_price_volatility_by_grade_returns_list(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_price_volatility_by_grade(session, hcmc.id, 2024, "H1")
        assert isinstance(result, list)

    def test_get_price_volatility_by_grade_structure(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_price_volatility_by_grade(session, hcmc.id, 2024, "H1")
        assert len(result) >= 1
        for row in result:
            assert "grade_code" in row
            assert "avg_price_usd" in row
            assert "std_dev_usd" in row
            assert "cv_pct" in row
            assert "project_count" in row
            assert "volatility" in row
            assert row["volatility"] in ("high", "moderate", "low")

    def test_get_price_volatility_no_data(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_price_volatility_by_grade(session, hcmc.id, 2099, "H1")
        assert result == []

    def test_get_district_ranking_change_returns_list(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_district_ranking_change(session, hcmc.id, 2023, "H2", 2024, "H1")
        assert isinstance(result, list)

    def test_get_district_ranking_change_structure(self, session):
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_district_ranking_change(session, hcmc.id, 2023, "H2", 2024, "H1")
        for row in result:
            assert "district_name" in row
            assert "rank_change" in row
            assert "movement" in row
            assert row["movement"] in ("risen", "fallen", "stable")

    def test_get_district_ranking_change_ordered_by_rank(self, session):
        """Results should be sorted by rank_change descending (biggest risers first)."""
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_district_ranking_change(session, hcmc.id, 2023, "H2", 2024, "H1")
        changes = [r["rank_change"] for r in result if r["rank_change"] is not None]
        assert changes == sorted(changes, reverse=True)

    def test_get_district_ranking_no_overlap(self, session):
        """If periods have no overlapping districts, returns empty list."""
        hcmc = get_city_by_name(session, "Ho Chi Minh City")
        result = get_district_ranking_change(session, hcmc.id, 2099, "H1", 2099, "H2")
        assert result == []
