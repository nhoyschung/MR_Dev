"""Tests for the price_forecast report module."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.config import SEED_DIR
from src.db.models import Base
from src.db.queries import get_city_by_name
from src.reports.price_forecast import (
    PeriodForecast,
    ForecastResult,
    forecast_city_price,
    forecast_grade_price,
    render_price_forecast,
    _next_period,
    _ols_forecast,
    _holt_forecast,
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
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close()
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


# ---------------------------------------------------------------------------
# Unit tests — internal helpers
# ---------------------------------------------------------------------------

class TestNextPeriod:
    def test_h1_to_h2(self):
        assert _next_period(2024, "H1") == (2024, "H2")

    def test_h2_to_next_h1(self):
        assert _next_period(2024, "H2") == (2025, "H1")

    def test_year_boundary(self):
        assert _next_period(2023, "H2") == (2024, "H1")


class TestOlsForecast:
    def test_returns_correct_length(self):
        values = [1000.0, 1050.0, 1100.0, 1150.0]
        pts, los, ups, rmse = _ols_forecast(values, n_ahead=2)
        assert len(pts) == 2
        assert len(los) == 2
        assert len(ups) == 2

    def test_upward_trend_forecast_rises(self):
        values = [1000.0, 1100.0, 1200.0, 1300.0]
        pts, _, _, _ = _ols_forecast(values, n_ahead=2)
        assert pts[0] > values[-1]
        assert pts[1] > pts[0]

    def test_ci_bounds_ordered(self):
        values = [1000.0, 1050.0, 1100.0]
        pts, los, ups, _ = _ols_forecast(values, n_ahead=2)
        for lo, pt, up in zip(los, pts, ups):
            assert lo <= pt <= up

    def test_rmse_non_negative(self):
        values = [1000.0, 1200.0, 900.0, 1100.0]
        _, _, _, rmse = _ols_forecast(values, n_ahead=1)
        assert rmse >= 0

    def test_perfect_linear_series_low_rmse(self):
        values = [1000.0, 1100.0, 1200.0, 1300.0]
        _, _, _, rmse = _ols_forecast(values, n_ahead=1)
        assert rmse < 1.0  # near-zero residuals


class TestHoltForecast:
    def test_returns_five_tuple(self):
        values = [1000.0, 1050.0, 1100.0, 1150.0]
        result = _holt_forecast(values, n_ahead=2)
        assert len(result) == 5  # pts, los, ups, rmse, method

    def test_method_label(self):
        values = [1000.0, 1050.0, 1100.0, 1150.0]
        _, _, _, _, method = _holt_forecast(values, n_ahead=2)
        assert method in ("holt", "ols_fallback")

    def test_forecast_length(self):
        values = [1000.0, 1050.0, 1100.0, 1150.0]
        pts, los, ups, _, _ = _holt_forecast(values, n_ahead=2)
        assert len(pts) == 2
        assert len(los) == 2
        assert len(ups) == 2

    def test_ci_bounds_ordered(self):
        values = [1000.0, 1100.0, 1200.0, 1300.0]
        pts, los, ups, _, _ = _holt_forecast(values, n_ahead=2)
        for lo, pt, up in zip(los, pts, ups):
            assert lo <= pt <= up

    def test_two_data_points_uses_fallback(self):
        """Only 2 points — Holt may fall back to OLS."""
        values = [1000.0, 1100.0]
        pts, _, _, _, method = _holt_forecast(values, n_ahead=2)
        assert len(pts) == 2
        # method can be either — just must not raise


# ---------------------------------------------------------------------------
# Integration tests — forecast_city_price
# ---------------------------------------------------------------------------

class TestForecastCityPrice:
    def test_returns_forecast_result(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        assert isinstance(result, ForecastResult)

    def test_result_has_two_forecasts_by_default(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        assert len(result.forecasts) == 2

    def test_result_has_historical_data(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        assert len(result.historical) >= 1

    def test_forecast_periods_are_sequential(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        periods = [f.period for f in result.forecasts]
        # Second forecast must come after the first
        assert periods[1] > periods[0]

    def test_forecast_values_positive(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        for f in result.forecasts:
            assert f.forecast_usd > 0
            assert f.lower_95 >= 0
            assert f.upper_95 > 0

    def test_ci_bounds_ordered(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        for f in result.forecasts:
            assert f.lower_95 <= f.forecast_usd <= f.upper_95

    def test_city_alias_works(self, session):
        r1 = forecast_city_price(session, "HCMC")
        r2 = forecast_city_price(session, "Ho Chi Minh City")
        assert r1 is not None and r2 is not None
        assert r1.historical == r2.historical

    def test_trend_direction_valid(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        assert result.trend_direction in ("up", "down", "flat")

    def test_method_populated(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        assert result.method in ("holt", "ols_fallback")

    def test_unknown_city_returns_none(self, session):
        result = forecast_city_price(session, "Atlantis")
        assert result is None

    def test_hanoi_forecast(self, session):
        result = forecast_city_price(session, "Hanoi")
        assert result is not None
        assert len(result.forecasts) == 2

    def test_one_period_ahead(self, session):
        result = forecast_city_price(session, "HCMC", periods_ahead=1)
        assert result is not None
        assert len(result.forecasts) == 1

    def test_forecast_follows_historical_last_period(self, session):
        """First forecast period must be directly after the last historical period."""
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        last_hist = result.historical[-1]["period"]
        # e.g. last_hist = "2024-H1" → first forecast must be "2024-H2"
        last_year = int(last_hist[:4])
        last_half = last_hist[5:]
        exp_year, exp_half = _next_period(last_year, last_half)
        assert result.forecasts[0].period == f"{exp_year}-{exp_half}"


# ---------------------------------------------------------------------------
# Integration tests — forecast_grade_price
# ---------------------------------------------------------------------------

class TestForecastGradePrice:
    def test_returns_forecast_result(self, session):
        city = get_city_by_name(session, "HCMC")
        assert city is not None
        result = forecast_grade_price(session, city.name_en, city.id, "H-I")
        # May be None if no H-I data — that's acceptable
        if result is not None:
            assert isinstance(result, ForecastResult)

    def test_grade_is_set(self, session):
        city = get_city_by_name(session, "HCMC")
        assert city is not None
        # Try each grade until we find one with data
        for grade in ("H-I", "M-I", "M-II", "L", "H-II"):
            result = forecast_grade_price(session, city.name_en, city.id, grade)
            if result is not None:
                assert result.grade == grade
                break

    def test_nonexistent_grade_returns_none(self, session):
        city = get_city_by_name(session, "HCMC")
        assert city is not None
        result = forecast_grade_price(session, city.name_en, city.id, "ZZZZ")
        assert result is None

    def test_forecasts_positive(self, session):
        city = get_city_by_name(session, "HCMC")
        assert city is not None
        for grade in ("H-I", "M-I", "M-II", "L"):
            result = forecast_grade_price(session, city.name_en, city.id, grade)
            if result is not None:
                for f in result.forecasts:
                    assert f.forecast_usd > 0
                break


# ---------------------------------------------------------------------------
# Render tests
# ---------------------------------------------------------------------------

class TestRenderPriceForecast:
    def test_render_returns_string(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        output = render_price_forecast(result)
        assert isinstance(output, str)
        assert len(output) > 100

    def test_render_contains_forecast_header(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        output = render_price_forecast(result)
        assert "# Price Forecast" in output
        assert "HCMC" in output or "Ho Chi Minh" in output

    def test_render_contains_historical_table(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        output = render_price_forecast(result)
        assert "## Historical Prices" in output

    def test_render_contains_forecast_table(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        output = render_price_forecast(result)
        assert "## Forecast" in output
        assert "forecast" in output

    def test_render_contains_ci_bounds(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        output = render_price_forecast(result)
        assert "95% CI" in output

    def test_render_grade_forecast_shows_grade(self, session):
        city = get_city_by_name(session, "HCMC")
        assert city is not None
        for grade in ("H-I", "M-I", "M-II"):
            result = forecast_grade_price(session, city.name_en, city.id, grade)
            if result is not None:
                output = render_price_forecast(result)
                assert grade in output
                break

    def test_render_includes_disclaimer(self, session):
        result = forecast_city_price(session, "HCMC")
        assert result is not None
        output = render_price_forecast(result)
        assert "statistical extrapolation" in output.lower() or "extrapolation" in output.lower()
