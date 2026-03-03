"""Price forecasting module for MR-System.

Uses Holt's double exponential smoothing (level + trend) to project
property prices 1–2 periods ahead with 95% confidence intervals.

Falls back to ordinary least-squares linear trend when fewer than
4 data points are available (statsmodels requires ≥ 3 for Holt).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from src.db.queries import get_city_price_trend, get_grade_price_summary, resolve_city_name


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PeriodForecast:
    """Single-period price forecast with confidence interval."""
    period: str             # e.g. "2025-H1"
    forecast_usd: float     # point estimate (USD/m²)
    lower_95: float         # 95% CI lower bound
    upper_95: float         # 95% CI upper bound
    is_forecast: bool = True


@dataclass
class ForecastResult:
    """Complete forecast result including historical context."""
    city: str
    grade: Optional[str]                # None = whole-city average
    method: str                         # "holt" | "ols"
    historical: list[dict]              # [{period, avg_price_usd, project_count}]
    forecasts: list[PeriodForecast]     # typically 2 periods ahead
    rmse: Optional[float]               # in-sample root mean squared error
    trend_direction: str                # "up" | "down" | "flat"
    trend_pct_per_period: float         # avg % change per period
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _next_period(year: int, half: str) -> tuple[int, str]:
    """Return the period immediately following the given one."""
    if half == "H1":
        return year, "H2"
    return year + 1, "H1"


def _period_label(year: int, half: str) -> str:
    return f"{year}-{half}"


def _ols_forecast(
    values: list[float], n_ahead: int, conf: float = 1.96
) -> tuple[list[float], list[float], list[float], float]:
    """Ordinary least-squares linear trend forecast.

    Returns (point_estimates, lower_bounds, upper_bounds, rmse).
    """
    n = len(values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)

    slope = ss_xy / ss_xx if ss_xx else 0.0
    intercept = y_mean - slope * x_mean

    fitted = [intercept + slope * xi for xi in x]
    residuals = [v - f for v, f in zip(values, fitted)]
    mse = sum(r ** 2 for r in residuals) / n
    rmse = math.sqrt(mse)

    # Forecast
    points, lowers, uppers = [], [], []
    for k in range(1, n_ahead + 1):
        xf = n - 1 + k
        yf = intercept + slope * xf
        # Prediction interval widens with distance from training data
        margin = conf * rmse * math.sqrt(1 + 1 / n + (xf - x_mean) ** 2 / ss_xx)
        points.append(yf)
        lowers.append(yf - margin)
        uppers.append(yf + margin)

    return points, lowers, uppers, rmse


def _holt_forecast(
    values: list[float], n_ahead: int
) -> tuple[list[float], list[float], list[float], float, str]:
    """Holt's double exponential smoothing forecast.

    Returns (point_estimates, lower_bounds, upper_bounds, rmse, method_label).
    Falls back to OLS if statsmodels is unavailable or fitting fails.
    """
    try:
        from statsmodels.tsa.holtwinters import Holt  # type: ignore

        model = Holt(values, exponential=False, damped_trend=len(values) >= 6)
        fit = model.fit(optimized=True, remove_bias=True)

        points = list(fit.forecast(n_ahead))
        pred = fit.get_prediction(start=len(values), end=len(values) + n_ahead - 1)
        ci = pred.conf_int(alpha=0.05)
        lowers = list(ci[:, 0])
        uppers = list(ci[:, 1])

        fitted_vals = fit.fittedvalues
        rmse = math.sqrt(sum((v - fv) ** 2 for v, fv in zip(values, fitted_vals)) / len(values))
        return points, lowers, uppers, rmse, "holt"

    except Exception:
        pts, los, ups, rmse = _ols_forecast(values, n_ahead)
        return pts, los, ups, rmse, "ols_fallback"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def forecast_city_price(
    session: Session,
    city_name: str,
    periods_ahead: int = 2,
) -> Optional[ForecastResult]:
    """Forecast city-wide average price for the next N periods.

    Uses all available historical periods for the city.

    Args:
        session: Active SQLAlchemy session.
        city_name: City name or alias (e.g. "HCMC", "Hanoi").
        periods_ahead: Number of half-year periods to project (default 2).

    Returns:
        ForecastResult or None if there is insufficient historical data.
    """
    trend = get_city_price_trend(session, city_name)
    if len(trend) < 2:
        return None

    years  = [r[0] for r in trend]
    halves = [r[1] for r in trend]
    prices = [r[2] for r in trend]
    counts = [r[3] for r in trend]

    pts, los, ups, rmse, method = _holt_forecast(prices, periods_ahead)

    # Build forecast period labels
    last_year, last_half = years[-1], halves[-1]
    forecast_periods: list[PeriodForecast] = []
    y, h = last_year, last_half
    for i in range(periods_ahead):
        y, h = _next_period(y, h)
        forecast_periods.append(PeriodForecast(
            period=_period_label(y, h),
            forecast_usd=round(pts[i], 0),
            lower_95=round(max(los[i], 0), 0),
            upper_95=round(ups[i], 0),
        ))

    # Trend direction
    if len(prices) >= 2:
        total_change = (prices[-1] - prices[0]) / prices[0] * 100
        per_period = total_change / (len(prices) - 1)
    else:
        total_change = 0.0
        per_period = 0.0

    direction = "up" if per_period > 0.5 else "down" if per_period < -0.5 else "flat"

    historical = [
        {
            "period": _period_label(y_, h_),
            "avg_price_usd": round(p, 0),
            "project_count": c,
        }
        for y_, h_, p, c in zip(years, halves, prices, counts)
    ]

    notes: list[str] = []
    if method != "holt":
        notes.append("Used OLS linear trend (statsmodels unavailable or insufficient data).")
    if len(prices) < 4:
        notes.append("Short history (< 4 periods) — forecast uncertainty is high.")
    if method == "holt" and "damped" in method:
        notes.append("Damped trend applied to reduce long-range over-extrapolation.")

    resolved = resolve_city_name(city_name)
    return ForecastResult(
        city=resolved.title(),
        grade=None,
        method=method,
        historical=historical,
        forecasts=forecast_periods,
        rmse=round(rmse, 0) if rmse else None,
        trend_direction=direction,
        trend_pct_per_period=round(per_period, 2),
        notes=notes,
    )


def forecast_grade_price(
    session: Session,
    city_name: str,
    city_id: int,
    grade_code: str,
    periods_ahead: int = 2,
) -> Optional[ForecastResult]:
    """Forecast average price for a specific grade tier over the next N periods.

    Builds the time series from get_grade_price_summary across all available
    periods, then applies the same Holt / OLS forecasting as forecast_city_price.

    Args:
        session: Active SQLAlchemy session.
        city_name: Display name for the city.
        city_id: Database city.id.
        grade_code: Grade code (e.g. "H-I", "M-II").
        periods_ahead: Number of periods to forecast.

    Returns:
        ForecastResult or None if the grade has fewer than 2 data points.
    """
    from src.db.queries import get_city_price_trend
    from src.db.models import ReportPeriod, PriceRecord, Project, District
    from sqlalchemy import select, func

    # Collect all periods that exist in the DB
    periods_stmt = (
        select(ReportPeriod.year, ReportPeriod.half)
        .order_by(ReportPeriod.year, ReportPeriod.half)
    )
    all_periods = session.execute(periods_stmt).all()

    series: list[tuple[int, str, float, int]] = []
    for yr, hf in all_periods:
        summary = get_grade_price_summary(session, city_id, yr, hf)
        for grade, avg_p, _min, _max, cnt in summary:
            if grade == grade_code and avg_p is not None:
                series.append((yr, hf, avg_p, cnt))
                break

    if len(series) < 2:
        return None

    years  = [r[0] for r in series]
    halves = [r[1] for r in series]
    prices = [r[2] for r in series]
    counts = [r[3] for r in series]

    pts, los, ups, rmse, method = _holt_forecast(prices, periods_ahead)

    y, h = years[-1], halves[-1]
    forecast_periods: list[PeriodForecast] = []
    for i in range(periods_ahead):
        y, h = _next_period(y, h)
        forecast_periods.append(PeriodForecast(
            period=_period_label(y, h),
            forecast_usd=round(pts[i], 0),
            lower_95=round(max(los[i], 0), 0),
            upper_95=round(ups[i], 0),
        ))

    if len(prices) >= 2:
        per_period = (prices[-1] - prices[0]) / prices[0] * 100 / (len(prices) - 1)
    else:
        per_period = 0.0
    direction = "up" if per_period > 0.5 else "down" if per_period < -0.5 else "flat"

    historical = [
        {"period": _period_label(y_, h_), "avg_price_usd": round(p, 0), "project_count": c}
        for y_, h_, p, c in zip(years, halves, prices, counts)
    ]

    notes: list[str] = []
    if method != "holt":
        notes.append("Used OLS linear trend (statsmodels unavailable or insufficient data).")
    if len(prices) < 4:
        notes.append(f"Only {len(prices)} data points for grade {grade_code} — forecast is indicative.")

    resolved = resolve_city_name(city_name)
    return ForecastResult(
        city=resolved.title(),
        grade=grade_code,
        method=method,
        historical=historical,
        forecasts=forecast_periods,
        rmse=round(rmse, 0) if rmse else None,
        trend_direction=direction,
        trend_pct_per_period=round(per_period, 2),
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_price_forecast(result: ForecastResult) -> str:
    """Render a ForecastResult as a Markdown report string."""

    scope = f"Grade {result.grade}" if result.grade else "City Average"
    arrow = {"up": "↑", "down": "↓", "flat": "→"}.get(result.trend_direction, "")
    trend_label = (
        f"{arrow} {abs(result.trend_pct_per_period):.1f}% per period "
        f"({'rising' if result.trend_direction == 'up' else 'falling' if result.trend_direction == 'down' else 'flat'})"
    )

    lines = [
        f"# Price Forecast — {result.city} ({scope})",
        "",
        f"**Trend:** {trend_label}  ",
        f"**Method:** {result.method.upper()}  ",
        f"**In-sample RMSE:** ${result.rmse:,.0f}/m²" if result.rmse else "",
        "",
        "## Historical Prices",
        "",
        "| Period | Avg Price (USD/m²) | Projects |",
        "|--------|-------------------|----------|",
    ]
    for h in result.historical:
        lines.append(f"| {h['period']} | ${h['avg_price_usd']:,.0f} | {h['project_count']} |")

    lines += [
        "",
        "## Forecast",
        "",
        "| Period | Forecast (USD/m²) | 95% CI Lower | 95% CI Upper |",
        "|--------|-------------------|--------------|--------------|",
    ]
    for f in result.forecasts:
        lines.append(
            f"| **{f.period}** *(forecast)* "
            f"| **${f.forecast_usd:,.0f}** "
            f"| ${f.lower_95:,.0f} "
            f"| ${f.upper_95:,.0f} |"
        )

    if result.notes:
        lines += ["", "## Notes", ""]
        for note in result.notes:
            lines.append(f"- {note}")

    lines += [
        "",
        "---",
        "*Forecast generated by MR-System price_forecast module. "
        "Projections are statistical extrapolations and do not account for "
        "regulatory changes, macro shocks, or developer decisions.*",
    ]

    return "\n".join(line for line in lines if line is not None)
