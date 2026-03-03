"""Tests for macro indicators — model, seeder, and query helpers."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.config import SEED_DIR
from src.db.models import Base, MacroIndicator, ReportPeriod
from src.db.queries import (
    get_macro_context_for_period,
    get_macro_indicator,
    get_macro_indicators,
    get_macro_trend,
)
from src.seeders.city_seeder import CitySeeder
from src.seeders.grade_seeder import GradeSeeder
from src.seeders.macro_indicator_seeder import MacroIndicatorSeeder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    """In-memory session with cities + grade periods pre-seeded."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close(),
    )
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()

    CitySeeder(s, SEED_DIR).seed()
    GradeSeeder(s, SEED_DIR).seed()   # creates report_periods

    yield s
    s.close()


@pytest.fixture
def seeded_session(session):
    """Session with macro indicators seeded from the real JSON file."""
    MacroIndicatorSeeder(session, SEED_DIR).seed()
    return session


# ---------------------------------------------------------------------------
# Seeder tests
# ---------------------------------------------------------------------------

class TestMacroIndicatorSeeder:
    def test_validate_passes(self, session):
        seeder = MacroIndicatorSeeder(session, SEED_DIR)
        assert seeder.validate() is True

    def test_seed_returns_positive_count(self, session):
        seeder = MacroIndicatorSeeder(session, SEED_DIR)
        count = seeder.seed()
        assert count > 0

    def test_seed_idempotent(self, session):
        seeder = MacroIndicatorSeeder(session, SEED_DIR)
        first = seeder.seed()
        second = seeder.seed()
        assert first > 0
        assert second == 0  # no new records on second run

    def test_expected_record_count(self, seeded_session):
        """JSON file has 36 records (6 indicators × 6 periods = 2022-H1 to 2024-H2)."""
        total = seeded_session.query(MacroIndicator).count()
        assert total == 36

    def test_creates_periods_if_missing(self):
        """Seeder auto-creates ReportPeriod records for years not in DB."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        s = sessionmaker(bind=engine)()
        # No GradeSeeder → no periods pre-created
        count = MacroIndicatorSeeder(s, SEED_DIR).seed()
        assert count > 0
        periods = s.query(ReportPeriod).all()
        assert len(periods) >= 6   # 2022-H1 … 2024-H2
        s.close()

    def test_all_indicator_types_present(self, seeded_session):
        expected_types = {
            "gdp_growth_pct", "cpi_pct", "mortgage_rate_pct",
            "policy_rate_pct", "fdi_usd_billion", "exchange_rate_vnd",
        }
        stored = {
            r.indicator_type
            for r in seeded_session.query(MacroIndicator).all()
        }
        assert expected_types == stored

    def test_all_periods_covered(self, seeded_session):
        from sqlalchemy import select
        from src.db.models import ReportPeriod
        periods = (
            seeded_session.execute(
                select(ReportPeriod.year, ReportPeriod.half)
                .join(MacroIndicator, MacroIndicator.period_id == ReportPeriod.id)
                .distinct()
                .order_by(ReportPeriod.year, ReportPeriod.half)
            ).all()
        )
        labels = [f"{y}-{h}" for y, h in periods]
        assert "2022-H1" in labels
        assert "2024-H2" in labels
        assert len(labels) == 6

    def test_values_are_positive(self, seeded_session):
        records = seeded_session.query(MacroIndicator).all()
        for r in records:
            assert r.value > 0, f"{r.indicator_type} has non-positive value {r.value}"

    def test_source_field_populated(self, seeded_session):
        records = seeded_session.query(MacroIndicator).all()
        for r in records:
            assert r.source is not None and len(r.source) > 0

    def test_city_id_is_none_for_national(self, seeded_session):
        """All seed records are national (no city specified)."""
        records = seeded_session.query(MacroIndicator).all()
        for r in records:
            assert r.city_id is None


# ---------------------------------------------------------------------------
# Query helper tests
# ---------------------------------------------------------------------------

class TestGetMacroIndicators:
    def test_returns_list(self, seeded_session):
        result = get_macro_indicators(seeded_session, 2024, "H1")
        assert isinstance(result, list)

    def test_returns_correct_period(self, seeded_session):
        result = get_macro_indicators(seeded_session, 2024, "H1")
        assert len(result) == 6   # 6 indicator types

    def test_empty_for_unknown_period(self, seeded_session):
        result = get_macro_indicators(seeded_session, 2099, "H1")
        assert result == []

    def test_ordered_by_type(self, seeded_session):
        result = get_macro_indicators(seeded_session, 2024, "H1")
        types = [r.indicator_type for r in result]
        assert types == sorted(types)


class TestGetMacroIndicator:
    def test_returns_single_record(self, seeded_session):
        result = get_macro_indicator(seeded_session, 2024, "H1", "gdp_growth_pct")
        assert result is not None
        assert isinstance(result, MacroIndicator)
        assert result.indicator_type == "gdp_growth_pct"

    def test_correct_value_2024_h1_gdp(self, seeded_session):
        result = get_macro_indicator(seeded_session, 2024, "H1", "gdp_growth_pct")
        assert result is not None
        assert result.value == pytest.approx(6.93)

    def test_correct_value_2023_h1_mortgage(self, seeded_session):
        result = get_macro_indicator(seeded_session, 2023, "H1", "mortgage_rate_pct")
        assert result is not None
        assert result.value == pytest.approx(10.0)

    def test_correct_value_2022_h2_policy_rate(self, seeded_session):
        result = get_macro_indicator(seeded_session, 2022, "H2", "policy_rate_pct")
        assert result is not None
        assert result.value == pytest.approx(6.0)

    def test_none_for_missing_indicator(self, seeded_session):
        result = get_macro_indicator(seeded_session, 2024, "H1", "nonexistent_indicator")
        assert result is None

    def test_none_for_missing_period(self, seeded_session):
        result = get_macro_indicator(seeded_session, 2099, "H1", "gdp_growth_pct")
        assert result is None


class TestGetMacroTrend:
    def test_returns_list(self, seeded_session):
        result = get_macro_trend(seeded_session, "gdp_growth_pct")
        assert isinstance(result, list)

    def test_returns_six_periods(self, seeded_session):
        result = get_macro_trend(seeded_session, "gdp_growth_pct")
        assert len(result) == 6

    def test_ordered_chronologically(self, seeded_session):
        result = get_macro_trend(seeded_session, "gdp_growth_pct")
        periods = [r["period"] for r in result]
        assert periods == sorted(periods)

    def test_first_period_is_2022_h1(self, seeded_session):
        result = get_macro_trend(seeded_session, "gdp_growth_pct")
        assert result[0]["period"] == "2022-H1"

    def test_last_period_is_2024_h2(self, seeded_session):
        result = get_macro_trend(seeded_session, "cpi_pct")
        assert result[-1]["period"] == "2024-H2"

    def test_structure_has_required_keys(self, seeded_session):
        result = get_macro_trend(seeded_session, "fdi_usd_billion")
        for row in result:
            assert "period" in row
            assert "year" in row
            assert "half" in row
            assert "value" in row
            assert "source" in row

    def test_fdi_values_are_reasonable(self, seeded_session):
        """FDI should be in range 5–20 USD billion per half-year."""
        result = get_macro_trend(seeded_session, "fdi_usd_billion")
        for row in result:
            assert 5 <= row["value"] <= 20, f"FDI out of range: {row}"

    def test_empty_for_nonexistent_type(self, seeded_session):
        result = get_macro_trend(seeded_session, "nonexistent_xyz")
        assert result == []


class TestGetMacroContextForPeriod:
    def test_returns_dict(self, seeded_session):
        result = get_macro_context_for_period(seeded_session, 2024, "H1")
        assert isinstance(result, dict)

    def test_contains_all_key_indicators(self, seeded_session):
        result = get_macro_context_for_period(seeded_session, 2024, "H1")
        expected_keys = {
            "gdp_growth_pct", "cpi_pct", "mortgage_rate_pct",
            "policy_rate_pct", "fdi_usd_billion", "exchange_rate_vnd",
        }
        assert expected_keys == set(result.keys())

    def test_values_not_none_for_seeded_period(self, seeded_session):
        result = get_macro_context_for_period(seeded_session, 2024, "H1")
        for key, val in result.items():
            assert val is not None, f"{key} is None for 2024-H1"

    def test_2024_h1_gdp(self, seeded_session):
        result = get_macro_context_for_period(seeded_session, 2024, "H1")
        assert result["gdp_growth_pct"] == pytest.approx(6.93)

    def test_2022_h2_policy_rate_high(self, seeded_session):
        """Policy rate was 6.0% in 2022-H2 (SBV hiking cycle)."""
        result = get_macro_context_for_period(seeded_session, 2022, "H2")
        assert result["policy_rate_pct"] == pytest.approx(6.0)

    def test_none_values_for_unknown_period(self, seeded_session):
        result = get_macro_context_for_period(seeded_session, 2099, "H1")
        for val in result.values():
            assert val is None

    def test_mortgage_rates_declined_2022_to_2023(self, seeded_session):
        """SBV easing in 2023 should have reduced mortgage rates."""
        ctx_2022_h2 = get_macro_context_for_period(seeded_session, 2022, "H2")
        ctx_2023_h2 = get_macro_context_for_period(seeded_session, 2023, "H2")
        assert ctx_2023_h2["mortgage_rate_pct"] < ctx_2022_h2["mortgage_rate_pct"]

    def test_fdi_growth_2022_to_2024(self, seeded_session):
        """FDI should be growing over the 2022–2024 period."""
        ctx_2022_h1 = get_macro_context_for_period(seeded_session, 2022, "H1")
        ctx_2024_h2 = get_macro_context_for_period(seeded_session, 2024, "H2")
        assert ctx_2024_h2["fdi_usd_billion"] > ctx_2022_h1["fdi_usd_billion"]
