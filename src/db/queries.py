"""Common query helpers for the MR-System database."""

import math
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.models import (
    City, District, Project, Developer, PriceRecord, UnitType,
    GradeDefinition, ReportPeriod, SupplyRecord, MarketSegmentSummary,
    DistrictMetric, MacroIndicator,
    OfficeProject, OfficeLeasingRecord, OfficeMarketSummary,
    HotelProject, HotelRoomType, HotelPerformanceRecord,
)


# ---------------------------------------------------------------------------
# City name aliases
# ---------------------------------------------------------------------------

_CITY_ALIASES: dict[str, str] = {
    "hcmc": "ho chi minh city",
    "hcm": "ho chi minh city",
    "saigon": "ho chi minh city",
    "sai gon": "ho chi minh city",
    "ho chi minh": "ho chi minh city",
    "tp hcm": "ho chi minh city",
    "ha noi": "hanoi",
    "binh duong": "binh duong",
    "bd": "binh duong",
    "vung tau": "ba ria - vung tau",
    "brvt": "ba ria - vung tau",
    "dong nai": "dong nai",
    "nhon trach": "dong nai",
    "binh dinh": "binh dinh",
    "quy nhon": "binh dinh",
}


def resolve_city_name(name: str) -> str:
    """Resolve common aliases to canonical city name."""
    return _CITY_ALIASES.get(name.strip().lower(), name.strip().lower())


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_city_by_name(session: Session, name: str) -> Optional[City]:
    """Find a city by English name or alias (case-insensitive)."""
    resolved = resolve_city_name(name)
    stmt = select(City).where(func.lower(City.name_en) == resolved)
    return session.execute(stmt).scalar_one_or_none()


def get_district_by_name(session: Session, name: str, city_id: Optional[int] = None) -> Optional[District]:
    """Find a district by English name, optionally filtered by city."""
    stmt = select(District).where(func.lower(District.name_en) == name.lower())
    if city_id is not None:
        stmt = stmt.where(District.city_id == city_id)
    return session.execute(stmt).scalar_one_or_none()


def get_developer_by_name(session: Session, name: str) -> Optional[Developer]:
    """Find a developer by English name (case-insensitive)."""
    stmt = select(Developer).where(func.lower(Developer.name_en) == name.lower())
    return session.execute(stmt).scalar_one_or_none()


def get_period(session: Session, year: int, half: str) -> Optional[ReportPeriod]:
    """Find a report period by year and half."""
    stmt = select(ReportPeriod).where(
        ReportPeriod.year == year, ReportPeriod.half == half
    )
    return session.execute(stmt).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Project queries
# ---------------------------------------------------------------------------

def list_projects_by_city(session: Session, city_name: str) -> list[Project]:
    """Get all projects in a city, ordered by name."""
    resolved = resolve_city_name(city_name)
    stmt = (
        select(Project)
        .join(District)
        .join(City)
        .where(func.lower(City.name_en) == resolved)
        .order_by(Project.name)
    )
    return list(session.execute(stmt).scalars().all())


def list_projects_by_grade(session: Session, grade_code: str) -> list[Project]:
    """Get all projects with a given primary grade."""
    stmt = (
        select(Project)
        .where(Project.grade_primary == grade_code)
        .order_by(Project.name)
    )
    return list(session.execute(stmt).scalars().all())


def list_projects_by_developer(session: Session, developer_name: str) -> list[Project]:
    """Get all projects by a developer (English name, case-insensitive)."""
    stmt = (
        select(Project)
        .join(Developer)
        .where(func.lower(Developer.name_en) == developer_name.lower())
        .order_by(Project.name)
    )
    return list(session.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# Price queries
# ---------------------------------------------------------------------------

def get_latest_price(
    session: Session,
    project_id: int,
    data_source: Optional[str] = None,
) -> Optional[PriceRecord]:
    """Get the most recent price record for a project.

    Args:
        data_source: Filter by source — 'nho_pdf', 'bds_scrape', or None for all.
    """
    stmt = (
        select(PriceRecord)
        .join(ReportPeriod)
        .where(PriceRecord.project_id == project_id)
    )
    if data_source:
        stmt = stmt.where(PriceRecord.data_source == data_source)
    stmt = stmt.order_by(ReportPeriod.year.desc(), ReportPeriod.half.desc()).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def get_price_history(
    session: Session,
    project_id: int,
    data_source: Optional[str] = None,
) -> list[PriceRecord]:
    """Get all price records for a project, ordered chronologically.

    Args:
        data_source: Filter by source — 'nho_pdf', 'bds_scrape', or None for all.
    """
    stmt = (
        select(PriceRecord)
        .join(ReportPeriod)
        .where(PriceRecord.project_id == project_id)
    )
    if data_source:
        stmt = stmt.where(PriceRecord.data_source == data_source)
    stmt = stmt.order_by(ReportPeriod.year, ReportPeriod.half)
    return list(session.execute(stmt).scalars().all())


def get_price_comparison(
    session: Session,
    project_id: int,
) -> dict:
    """Compare NHO PDF vs BDS scrape prices for a project.

    Returns dict with keys: nho_latest, bds_latest, divergence_pct.
    """
    nho = get_latest_price(session, project_id, data_source="nho_pdf")
    bds = get_latest_price(session, project_id, data_source="bds_scrape")

    divergence_pct = None
    if nho and bds and nho.price_vnd_per_m2 and bds.price_vnd_per_m2:
        divergence_pct = round(
            (bds.price_vnd_per_m2 - nho.price_vnd_per_m2) / nho.price_vnd_per_m2 * 100, 1
        )

    return {
        "project_id": project_id,
        "nho_latest": nho,
        "bds_latest": bds,
        "divergence_pct": divergence_pct,
    }


def get_grade_for_price(
    session: Session, city_id: int, price_usd: float
) -> Optional[GradeDefinition]:
    """Determine the grade for a given USD price in a city."""
    stmt = (
        select(GradeDefinition)
        .where(
            GradeDefinition.city_id == city_id,
            GradeDefinition.min_price_usd <= price_usd,
            GradeDefinition.max_price_usd > price_usd,
        )
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Supply & market queries
# ---------------------------------------------------------------------------

def get_district_supply(
    session: Session, district_id: int, year: int, half: str
) -> list[SupplyRecord]:
    """Get supply records for a district in a given period."""
    stmt = (
        select(SupplyRecord)
        .join(ReportPeriod)
        .where(
            SupplyRecord.district_id == district_id,
            SupplyRecord.project_id.is_(None),
            ReportPeriod.year == year,
            ReportPeriod.half == half,
        )
    )
    return list(session.execute(stmt).scalars().all())


def get_market_summary(
    session: Session, city_id: int, year: int, half: str
) -> list[MarketSegmentSummary]:
    """Get market segment summaries for a city/period."""
    stmt = (
        select(MarketSegmentSummary)
        .join(ReportPeriod)
        .where(
            MarketSegmentSummary.city_id == city_id,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
        )
        .order_by(MarketSegmentSummary.grade_code)
    )
    return list(session.execute(stmt).scalars().all())


def get_district_metrics(
    session: Session, district_id: int, year: int, half: str
) -> list[DistrictMetric]:
    """Get all metrics for a district in a period."""
    stmt = (
        select(DistrictMetric)
        .join(ReportPeriod)
        .where(
            DistrictMetric.district_id == district_id,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
        )
    )
    return list(session.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def count_projects_by_city(session: Session) -> list[tuple[str, int]]:
    """Count projects per city."""
    stmt = (
        select(City.name_en, func.count(Project.id))
        .join(District, City.id == District.city_id)
        .join(Project, District.id == Project.district_id)
        .group_by(City.name_en)
        .order_by(func.count(Project.id).desc())
    )
    return list(session.execute(stmt).all())


def avg_price_by_district(
    session: Session, city_id: int, year: int, half: str
) -> list[tuple[str, float]]:
    """Average USD price per district for a city/period."""
    stmt = (
        select(District.name_en, func.avg(PriceRecord.price_usd_per_m2))
        .join(Project, District.id == Project.district_id)
        .join(PriceRecord, Project.id == PriceRecord.project_id)
        .join(ReportPeriod, PriceRecord.period_id == ReportPeriod.id)
        .where(
            District.city_id == city_id,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
        )
        .group_by(District.name_en)
        .order_by(func.avg(PriceRecord.price_usd_per_m2).desc())
    )
    return list(session.execute(stmt).all())


# ---------------------------------------------------------------------------
# Price trend analysis
# ---------------------------------------------------------------------------

def get_city_price_trend(
    session: Session, city_name: str,
) -> list[tuple[int, str, float, int]]:
    """Average price per period for a city.

    Returns list of (year, half, avg_price_usd, project_count) ordered chronologically.
    """
    resolved = resolve_city_name(city_name)
    stmt = (
        select(
            ReportPeriod.year,
            ReportPeriod.half,
            func.avg(PriceRecord.price_usd_per_m2),
            func.count(PriceRecord.id),
        )
        .join(PriceRecord, ReportPeriod.id == PriceRecord.period_id)
        .join(Project, PriceRecord.project_id == Project.id)
        .join(District, Project.district_id == District.id)
        .join(City, District.city_id == City.id)
        .where(
            func.lower(City.name_en) == resolved,
            PriceRecord.price_usd_per_m2.isnot(None),
        )
        .group_by(ReportPeriod.year, ReportPeriod.half)
        .order_by(ReportPeriod.year, ReportPeriod.half)
    )
    return list(session.execute(stmt).all())


def get_grade_price_summary(
    session: Session, city_id: int, year: int, half: str,
) -> list[tuple[str, float, float, float, int]]:
    """Price stats per grade for a city/period.

    Returns list of (grade_code, avg_price, min_price, max_price, count)
    ordered by avg_price desc.
    """
    stmt = (
        select(
            Project.grade_primary,
            func.avg(PriceRecord.price_usd_per_m2),
            func.min(PriceRecord.price_usd_per_m2),
            func.max(PriceRecord.price_usd_per_m2),
            func.count(PriceRecord.id),
        )
        .join(PriceRecord, Project.id == PriceRecord.project_id)
        .join(ReportPeriod, PriceRecord.period_id == ReportPeriod.id)
        .join(District, Project.district_id == District.id)
        .where(
            District.city_id == city_id,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
            PriceRecord.price_usd_per_m2.isnot(None),
            Project.grade_primary.isnot(None),
        )
        .group_by(Project.grade_primary)
        .order_by(func.avg(PriceRecord.price_usd_per_m2).desc())
    )
    return list(session.execute(stmt).all())


def get_project_price_changes(
    session: Session, city_id: int,
) -> list[dict]:
    """Find projects with prices in multiple periods to show trends.

    Returns list of dicts with project_name, periods with prices, and changes.
    """
    # Get all prices for city projects, ordered by project and time
    stmt = (
        select(
            Project.name,
            ReportPeriod.year,
            ReportPeriod.half,
            PriceRecord.price_usd_per_m2,
        )
        .join(PriceRecord, Project.id == PriceRecord.project_id)
        .join(ReportPeriod, PriceRecord.period_id == ReportPeriod.id)
        .join(District, Project.district_id == District.id)
        .where(
            District.city_id == city_id,
            PriceRecord.price_usd_per_m2.isnot(None),
        )
        .order_by(Project.name, ReportPeriod.year, ReportPeriod.half)
    )
    rows = session.execute(stmt).all()

    # Group by project
    projects: dict[str, list] = {}
    for name, year, half, price in rows:
        projects.setdefault(name, []).append({
            "period": f"{year}-{half}",
            "price": price,
        })

    # Only return projects with 2+ periods
    results = []
    for name, prices in projects.items():
        if len(prices) < 2:
            continue
        first = prices[0]["price"]
        last = prices[-1]["price"]
        change_pct = ((last - first) / first) * 100 if first else 0
        results.append({
            "project_name": name,
            "first_price": first,
            "last_price": last,
            "change_pct": change_pct,
            "periods": prices,
        })

    return sorted(results, key=lambda x: abs(x["change_pct"]), reverse=True)


def get_price_range_by_city(
    session: Session, city_name: str, year: int, half: str,
) -> Optional[tuple[float, float, float]]:
    """Get min, avg, max price for a city in a period.

    Returns (min_price, avg_price, max_price) or None if no data.
    """
    resolved = resolve_city_name(city_name)
    stmt = (
        select(
            func.min(PriceRecord.price_usd_per_m2),
            func.avg(PriceRecord.price_usd_per_m2),
            func.max(PriceRecord.price_usd_per_m2),
        )
        .join(Project, PriceRecord.project_id == Project.id)
        .join(District, Project.district_id == District.id)
        .join(City, District.city_id == City.id)
        .join(ReportPeriod, PriceRecord.period_id == ReportPeriod.id)
        .where(
            func.lower(City.name_en) == resolved,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
            PriceRecord.price_usd_per_m2.isnot(None),
        )
    )
    row = session.execute(stmt).one_or_none()
    if row and row[0] is not None:
        return (row[0], row[1], row[2])
    return None


# ---------------------------------------------------------------------------
# Macro indicator queries
# ---------------------------------------------------------------------------

def get_macro_indicators(
    session: Session,
    year: int,
    half: str,
    city_id: Optional[int] = None,
) -> list[MacroIndicator]:
    """Return all macro indicators for a given period.

    Pass city_id to filter city-specific indicators, or leave None for
    national-level indicators only.
    """
    stmt = (
        select(MacroIndicator)
        .join(ReportPeriod, MacroIndicator.period_id == ReportPeriod.id)
        .where(
            ReportPeriod.year == year,
            ReportPeriod.half == half,
            MacroIndicator.city_id == city_id,
        )
        .order_by(MacroIndicator.indicator_type)
    )
    return list(session.execute(stmt).scalars().all())


def get_macro_indicator(
    session: Session,
    year: int,
    half: str,
    indicator_type: str,
    city_id: Optional[int] = None,
) -> Optional[MacroIndicator]:
    """Return a single macro indicator by type and period."""
    stmt = (
        select(MacroIndicator)
        .join(ReportPeriod, MacroIndicator.period_id == ReportPeriod.id)
        .where(
            ReportPeriod.year == year,
            ReportPeriod.half == half,
            MacroIndicator.indicator_type == indicator_type,
            MacroIndicator.city_id == city_id,
        )
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_macro_trend(
    session: Session,
    indicator_type: str,
    city_id: Optional[int] = None,
) -> list[dict]:
    """Return the full history of a single indicator type, ordered chronologically.

    Returns list of dicts: {period, year, half, value, source}
    """
    stmt = (
        select(
            ReportPeriod.year,
            ReportPeriod.half,
            MacroIndicator.value,
            MacroIndicator.source,
        )
        .join(ReportPeriod, MacroIndicator.period_id == ReportPeriod.id)
        .where(
            MacroIndicator.indicator_type == indicator_type,
            MacroIndicator.city_id == city_id,
        )
        .order_by(ReportPeriod.year, ReportPeriod.half)
    )
    rows = session.execute(stmt).all()
    return [
        {
            "period": f"{yr}-{hf}",
            "year": yr,
            "half": hf,
            "value": val,
            "source": src,
        }
        for yr, hf, val, src in rows
    ]


def get_macro_context_for_period(
    session: Session,
    year: int,
    half: str,
) -> dict:
    """Return a context dict with key macro indicators for a period.

    Useful for injecting macro context into market briefing reports.
    Returns dict with keys: gdp_growth_pct, cpi_pct, mortgage_rate_pct,
    policy_rate_pct, fdi_usd_billion, exchange_rate_vnd
    (values are floats or None if unavailable).
    """
    indicators = get_macro_indicators(session, year, half)
    context = {ind.indicator_type: ind.value for ind in indicators}

    key_indicators = [
        "gdp_growth_pct", "cpi_pct", "mortgage_rate_pct",
        "policy_rate_pct", "fdi_usd_billion", "exchange_rate_vnd",
    ]
    return {k: context.get(k) for k in key_indicators}


# ---------------------------------------------------------------------------
# Temporal trend analysis
# ---------------------------------------------------------------------------

def get_price_momentum(
    session: Session, city_name: str,
) -> list[dict]:
    """Price momentum analysis: period-over-period change and acceleration.

    Acceleration = change in the change rate (second derivative of price).
    Positive acceleration means price growth is speeding up.

    Returns list of dicts ordered chronologically:
        period, avg_price_usd, project_count, change_pct, acceleration
    """
    trend = get_city_price_trend(session, city_name)
    if not trend:
        return []

    results: list[dict] = []
    for i, (year, half, avg_price, count) in enumerate(trend):
        prev_price = trend[i - 1][2] if i > 0 else None
        change_pct = (
            round((avg_price - prev_price) / prev_price * 100, 2)
            if prev_price is not None and prev_price > 0
            else None
        )
        prev_change = results[i - 1]["change_pct"] if i > 1 else None
        acceleration = (
            round(change_pct - prev_change, 2)
            if change_pct is not None and prev_change is not None
            else None
        )
        results.append({
            "period": f"{year}-{half}",
            "avg_price_usd": round(avg_price, 0),
            "project_count": count,
            "change_pct": change_pct,
            "acceleration": acceleration,
            "momentum": (
                "accelerating" if acceleration and acceleration > 0
                else "decelerating" if acceleration and acceleration < 0
                else "steady"
            ),
        })
    return results


def get_supply_demand_ratio_by_period(
    session: Session, city_name: str,
) -> list[dict]:
    """Supply vs. demand balance per period at city level.

    supply_demand_ratio = new_supply / sold_units
      > 1.2  → oversupply risk
      < 0.8  → shortage signal
      else   → balanced

    Returns list of dicts ordered chronologically:
        period, new_supply, sold_units, supply_demand_ratio, avg_absorption_pct, signal
    """
    resolved = resolve_city_name(city_name)
    stmt = (
        select(
            ReportPeriod.year,
            ReportPeriod.half,
            func.sum(SupplyRecord.new_supply),
            func.sum(SupplyRecord.sold_units),
            func.avg(SupplyRecord.absorption_rate_pct),
        )
        .join(ReportPeriod, SupplyRecord.period_id == ReportPeriod.id)
        .join(District, SupplyRecord.district_id == District.id)
        .join(City, District.city_id == City.id)
        .where(
            func.lower(City.name_en) == resolved,
            SupplyRecord.district_id.isnot(None),
            SupplyRecord.new_supply.isnot(None),
        )
        .group_by(ReportPeriod.year, ReportPeriod.half)
        .order_by(ReportPeriod.year, ReportPeriod.half)
    )
    rows = session.execute(stmt).all()

    results: list[dict] = []
    for year, half, new_supply, sold_units, avg_absorption in rows:
        ratio = (
            round(new_supply / sold_units, 2)
            if sold_units and sold_units > 0
            else None
        )
        if ratio is None:
            signal = "no_data"
        elif ratio > 1.2:
            signal = "oversupply"
        elif ratio < 0.8:
            signal = "shortage"
        else:
            signal = "balanced"
        results.append({
            "period": f"{year}-{half}",
            "new_supply": new_supply,
            "sold_units": sold_units,
            "supply_demand_ratio": ratio,
            "avg_absorption_pct": round(avg_absorption, 1) if avg_absorption else None,
            "signal": signal,
        })
    return results


def get_grade_migration_cohort(
    session: Session, city_id: int,
) -> list[dict]:
    """Detect projects whose implied grade changed across periods.

    Classifies each price record against the city's grade thresholds.
    A project has migrated if its implied grade changed between its
    earliest and latest price records.

    Returns list of dicts with migration details, ordered by latest period desc.
    """
    # Load grade thresholds for this city (descending by min price)
    grade_stmt = (
        select(GradeDefinition)
        .where(GradeDefinition.city_id == city_id)
        .order_by(GradeDefinition.min_price_usd.desc())
    )
    grades = list(session.execute(grade_stmt).scalars().all())

    def classify_price(price_usd: float) -> Optional[str]:
        if price_usd is None:
            return None
        for g in grades:
            lo = g.min_price_usd or 0.0
            hi = g.max_price_usd or float("inf")
            if lo <= price_usd < hi:
                return g.grade_code
        return None

    # Fetch all price history for projects in this city
    stmt = (
        select(
            Project.id,
            Project.name,
            Project.grade_primary,
            ReportPeriod.year,
            ReportPeriod.half,
            PriceRecord.price_usd_per_m2,
        )
        .join(PriceRecord, Project.id == PriceRecord.project_id)
        .join(ReportPeriod, PriceRecord.period_id == ReportPeriod.id)
        .join(District, Project.district_id == District.id)
        .where(
            District.city_id == city_id,
            PriceRecord.price_usd_per_m2.isnot(None),
        )
        .order_by(Project.id, ReportPeriod.year, ReportPeriod.half)
    )
    rows = session.execute(stmt).all()

    # Group by project
    projects: dict[int, dict] = {}
    for proj_id, name, grade_primary, year, half, price in rows:
        entry = projects.setdefault(proj_id, {
            "name": name,
            "grade_primary": grade_primary,
            "prices": [],
        })
        entry["prices"].append({
            "period": f"{year}-{half}",
            "price_usd": price,
            "implied_grade": classify_price(price),
        })

    # Find projects with grade migration
    migrations: list[dict] = []
    for proj_id, data in projects.items():
        prices = data["prices"]
        if len(prices) < 2:
            continue
        implied = [p["implied_grade"] for p in prices if p["implied_grade"]]
        if len(set(implied)) > 1:
            migrations.append({
                "project_id": proj_id,
                "project_name": data["name"],
                "stored_grade": data["grade_primary"],
                "grade_history": prices,
                "migrated_from": implied[0],
                "migrated_to": implied[-1],
                "direction": "upgrade" if implied[-1] < implied[0] else "downgrade",
            })

    return sorted(migrations, key=lambda x: x["grade_history"][-1]["period"], reverse=True)


def get_price_volatility_by_grade(
    session: Session, city_id: int, year: int, half: str,
) -> list[dict]:
    """Price dispersion within each grade tier for a city/period.

    Computes standard deviation and coefficient of variation (CV).
    High CV (>20%) indicates a heterogeneous grade tier.

    Returns list of dicts ordered by grade tier (SL → A-II):
        grade_code, avg_price_usd, std_dev_usd, cv_pct, project_count
    """
    stmt = (
        select(
            Project.grade_primary,
            PriceRecord.price_usd_per_m2,
        )
        .join(PriceRecord, Project.id == PriceRecord.project_id)
        .join(ReportPeriod, PriceRecord.period_id == ReportPeriod.id)
        .join(District, Project.district_id == District.id)
        .where(
            District.city_id == city_id,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
            PriceRecord.price_usd_per_m2.isnot(None),
            Project.grade_primary.isnot(None),
        )
    )
    rows = session.execute(stmt).all()

    # Group prices by grade
    by_grade: dict[str, list[float]] = {}
    for grade, price in rows:
        by_grade.setdefault(grade, []).append(price)

    _GRADE_ORDER = {
        "SL": 0, "L": 1, "H-I": 2, "H-II": 3,
        "M-I": 4, "M-II": 5, "M-III": 6, "A-I": 7, "A-II": 8,
    }

    results: list[dict] = []
    for grade, prices in by_grade.items():
        n = len(prices)
        avg = sum(prices) / n
        variance = sum((p - avg) ** 2 for p in prices) / n if n > 1 else 0.0
        std_dev = math.sqrt(variance)
        cv_pct = (std_dev / avg * 100) if avg else 0.0
        results.append({
            "grade_code": grade,
            "avg_price_usd": round(avg, 0),
            "std_dev_usd": round(std_dev, 0),
            "cv_pct": round(cv_pct, 1),
            "project_count": n,
            "volatility": (
                "high" if cv_pct > 20
                else "moderate" if cv_pct > 10
                else "low"
            ),
        })

    return sorted(results, key=lambda x: _GRADE_ORDER.get(x["grade_code"], 99))


def get_district_ranking_change(
    session: Session,
    city_id: int,
    year_a: int,
    half_a: str,
    year_b: int,
    half_b: str,
) -> list[dict]:
    """Compare district price rankings between two periods.

    Shows which districts rose or fell in the price hierarchy.
    rank_change > 0  → district rose (became more expensive relative to peers)
    rank_change < 0  → district fell

    Returns list of dicts ordered by rank_change desc (biggest risers first).
    """
    def _district_avg_prices(year: int, half: str) -> dict[int, tuple[str, float]]:
        """Return {district_id: (name, avg_price)} for the given period."""
        stmt = (
            select(
                District.id,
                District.name_en,
                func.avg(PriceRecord.price_usd_per_m2),
            )
            .join(Project, District.id == Project.district_id)
            .join(PriceRecord, Project.id == PriceRecord.project_id)
            .join(ReportPeriod, PriceRecord.period_id == ReportPeriod.id)
            .where(
                District.city_id == city_id,
                ReportPeriod.year == year,
                ReportPeriod.half == half,
                PriceRecord.price_usd_per_m2.isnot(None),
            )
            .group_by(District.id, District.name_en)
        )
        return {row[0]: (row[1], row[2]) for row in session.execute(stmt).all()}

    prices_a = _district_avg_prices(year_a, half_a)
    prices_b = _district_avg_prices(year_b, half_b)

    # Rank districts within each period (rank 1 = highest price)
    ranked_a = sorted(prices_a.items(), key=lambda x: x[1][1] or 0, reverse=True)
    ranked_b = sorted(prices_b.items(), key=lambda x: x[1][1] or 0, reverse=True)
    rank_a = {did: rank + 1 for rank, (did, _) in enumerate(ranked_a)}
    rank_b = {did: rank + 1 for rank, (did, _) in enumerate(ranked_b)}

    # Only compare districts present in both periods
    common = set(prices_a.keys()) & set(prices_b.keys())
    results: list[dict] = []
    for did in common:
        name = prices_a[did][0]
        p_a = prices_a[did][1]
        p_b = prices_b[did][1]
        ra = rank_a.get(did)
        rb = rank_b.get(did)
        # rank_change > 0 means rank number decreased (rose closer to #1)
        rank_change = (ra - rb) if ra is not None and rb is not None else None
        price_change_pct = (
            round((p_b - p_a) / p_a * 100, 1) if p_a and p_a > 0 else None
        )
        results.append({
            "district_name": name,
            f"avg_price_{year_a}_{half_a}": round(p_a, 0) if p_a else None,
            f"avg_price_{year_b}_{half_b}": round(p_b, 0) if p_b else None,
            "price_change_pct": price_change_pct,
            f"rank_{year_a}_{half_a}": ra,
            f"rank_{year_b}_{half_b}": rb,
            "rank_change": rank_change,
            "movement": (
                "risen" if rank_change and rank_change > 0
                else "fallen" if rank_change and rank_change < 0
                else "stable"
            ),
        })

    return sorted(results, key=lambda x: x["rank_change"] or 0, reverse=True)


# ---------------------------------------------------------------------------
# Office market queries
# ---------------------------------------------------------------------------

def get_office_projects(
    session: Session,
    city_name: Optional[str] = None,
    grade: Optional[str] = None,
    district_name: Optional[str] = None,
) -> list[OfficeProject]:
    """List office projects, optionally filtered by city, grade, or district.

    grade values: A / B+ / B / C
    """
    stmt = select(OfficeProject).order_by(OfficeProject.name)
    if city_name:
        resolved = resolve_city_name(city_name)
        stmt = stmt.join(City, OfficeProject.city_id == City.id).where(
            func.lower(City.name_en) == resolved
        )
    if grade:
        stmt = stmt.where(OfficeProject.office_grade == grade)
    if district_name:
        stmt = stmt.join(District, OfficeProject.district_id == District.id).where(
            func.lower(District.name_en) == district_name.lower()
        )
    return list(session.execute(stmt).scalars().all())


def get_office_project_by_name(session: Session, name: str) -> Optional[OfficeProject]:
    """Find a single office project by name (case-insensitive)."""
    stmt = select(OfficeProject).where(
        func.lower(OfficeProject.name) == name.lower()
    )
    return session.execute(stmt).scalar_one_or_none()


def get_office_leasing_history(
    session: Session, office_project_id: int
) -> list[OfficeLeasingRecord]:
    """Get all leasing records for an office building, ordered chronologically."""
    stmt = (
        select(OfficeLeasingRecord)
        .join(ReportPeriod, OfficeLeasingRecord.period_id == ReportPeriod.id)
        .where(OfficeLeasingRecord.office_project_id == office_project_id)
        .order_by(ReportPeriod.year, ReportPeriod.half)
    )
    return list(session.execute(stmt).scalars().all())


def get_office_market_summary(
    session: Session,
    city_name: str,
    year: int,
    half: str,
    district_name: Optional[str] = None,
) -> Optional[OfficeMarketSummary]:
    """Get the office market summary for a city (and optional district) in a period."""
    resolved = resolve_city_name(city_name)
    stmt = (
        select(OfficeMarketSummary)
        .join(City, OfficeMarketSummary.city_id == City.id)
        .join(ReportPeriod, OfficeMarketSummary.period_id == ReportPeriod.id)
        .where(
            func.lower(City.name_en) == resolved,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
        )
    )
    if district_name:
        stmt = stmt.join(District, OfficeMarketSummary.district_id == District.id).where(
            func.lower(District.name_en) == district_name.lower()
        )
    else:
        stmt = stmt.where(OfficeMarketSummary.district_id.is_(None))
    return session.execute(stmt).scalar_one_or_none()


def get_office_rent_comparison(
    session: Session,
    city_name: str,
    year: int,
    half: str,
) -> list[dict]:
    """Compare office rents across buildings for a city/period.

    Returns list of dicts ordered by midpoint rent descending:
        name, office_grade, address, rent_min_usd, rent_max_usd,
        management_fee_usd, occupancy_rate_pct, green_certificate
    """
    resolved = resolve_city_name(city_name)
    stmt = (
        select(
            OfficeProject.name,
            OfficeProject.office_grade,
            OfficeProject.address,
            OfficeLeasingRecord.rent_min_usd,
            OfficeLeasingRecord.rent_max_usd,
            OfficeLeasingRecord.management_fee_usd,
            OfficeLeasingRecord.occupancy_rate_pct,
            OfficeProject.green_certificate,
        )
        .join(OfficeLeasingRecord, OfficeProject.id == OfficeLeasingRecord.office_project_id)
        .join(ReportPeriod, OfficeLeasingRecord.period_id == ReportPeriod.id)
        .join(City, OfficeProject.city_id == City.id)
        .where(
            func.lower(City.name_en) == resolved,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
        )
        .order_by(OfficeLeasingRecord.rent_max_usd.desc())
    )
    rows = session.execute(stmt).all()
    return [
        {
            "name": row[0],
            "office_grade": row[1],
            "address": row[2],
            "rent_min_usd": row[3],
            "rent_max_usd": row[4],
            "rent_midpoint_usd": round((row[3] + row[4]) / 2, 1) if row[3] and row[4] else None,
            "management_fee_usd": row[5],
            "occupancy_rate_pct": row[6],
            "green_certificate": row[7],
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Hotel market queries
# ---------------------------------------------------------------------------

def get_hotel_projects(
    session: Session,
    city_name: Optional[str] = None,
    district_name: Optional[str] = None,
    min_stars: Optional[int] = None,
) -> list[HotelProject]:
    """List hotel projects, optionally filtered by city, district, or star rating."""
    stmt = select(HotelProject).order_by(HotelProject.name)
    if city_name:
        resolved = resolve_city_name(city_name)
        stmt = stmt.join(City, HotelProject.city_id == City.id).where(
            func.lower(City.name_en) == resolved
        )
    if district_name:
        stmt = stmt.join(District, HotelProject.district_id == District.id).where(
            func.lower(District.name_en) == district_name.lower()
        )
    if min_stars is not None:
        stmt = stmt.where(HotelProject.star_rating >= min_stars)
    return list(session.execute(stmt).scalars().all())


def get_hotel_room_breakdown(session: Session, hotel_project_id: int) -> list[HotelRoomType]:
    """Get room type breakdown for a hotel, ordered by area ascending."""
    stmt = (
        select(HotelRoomType)
        .where(HotelRoomType.hotel_project_id == hotel_project_id)
        .order_by(HotelRoomType.area_m2)
    )
    return list(session.execute(stmt).scalars().all())


def get_hotel_market_performance(
    session: Session,
    city_name: str,
    year: int,
    half: str,
    district_name: Optional[str] = None,
) -> Optional[HotelPerformanceRecord]:
    """Get market-aggregate hotel performance (occupancy, ADR, RevPAR) for a period.

    Returns the citywide or district-level aggregate record (hotel_project_id IS NULL).
    """
    resolved = resolve_city_name(city_name)
    stmt = (
        select(HotelPerformanceRecord)
        .join(City, HotelPerformanceRecord.city_id == City.id)
        .join(ReportPeriod, HotelPerformanceRecord.period_id == ReportPeriod.id)
        .where(
            func.lower(City.name_en) == resolved,
            ReportPeriod.year == year,
            ReportPeriod.half == half,
            HotelPerformanceRecord.hotel_project_id.is_(None),
        )
    )
    if district_name:
        stmt = stmt.join(District, HotelPerformanceRecord.district_id == District.id).where(
            func.lower(District.name_en) == district_name.lower()
        )
    else:
        stmt = stmt.where(HotelPerformanceRecord.district_id.is_(None))
    return session.execute(stmt).scalar_one_or_none()


def get_hotel_kpi_trend(
    session: Session,
    city_name: str,
    district_name: Optional[str] = None,
) -> list[dict]:
    """Hotel market occupancy, ADR, RevPAR trend over time.

    Returns list of dicts ordered chronologically:
        period, year, half, occupancy_rate_pct, adr_vnd, revpar_vnd, international_visitor_count
    """
    resolved = resolve_city_name(city_name)
    stmt = (
        select(
            ReportPeriod.year,
            ReportPeriod.half,
            HotelPerformanceRecord.occupancy_rate_pct,
            HotelPerformanceRecord.adr_vnd,
            HotelPerformanceRecord.revpar_vnd,
            HotelPerformanceRecord.international_visitor_count,
        )
        .join(City, HotelPerformanceRecord.city_id == City.id)
        .join(ReportPeriod, HotelPerformanceRecord.period_id == ReportPeriod.id)
        .where(
            func.lower(City.name_en) == resolved,
            HotelPerformanceRecord.hotel_project_id.is_(None),
        )
    )
    if district_name:
        stmt = stmt.join(District, HotelPerformanceRecord.district_id == District.id).where(
            func.lower(District.name_en) == district_name.lower()
        )
    else:
        stmt = stmt.where(HotelPerformanceRecord.district_id.is_(None))
    stmt = stmt.order_by(ReportPeriod.year, ReportPeriod.half)
    rows = session.execute(stmt).all()
    return [
        {
            "period": f"{yr}-{hf}",
            "year": yr,
            "half": hf,
            "occupancy_rate_pct": occ,
            "adr_vnd": adr,
            "revpar_vnd": revpar,
            "international_visitor_count": intl,
        }
        for yr, hf, occ, adr, revpar, intl in rows
    ]


# ---------------------------------------------------------------------------
# Unit-type price structure analysis
# ---------------------------------------------------------------------------

def get_unit_type_prices(
    session: Session,
    project_id: int,
    period_id: Optional[int] = None,
) -> list[dict]:
    """Get unit-type-level prices for a project, sorted by area ascending.

    Returns list of dicts: unit_type_id, type_name, net_area_m2,
    price_usd_per_m2, price_vnd_per_m2.
    """
    stmt = (
        select(
            UnitType.id,
            UnitType.type_name,
            UnitType.net_area_m2,
            PriceRecord.price_usd_per_m2,
            PriceRecord.price_vnd_per_m2,
        )
        .join(PriceRecord, PriceRecord.unit_type_id == UnitType.id)
        .where(
            PriceRecord.project_id == project_id,
            PriceRecord.unit_type_id.isnot(None),
        )
    )
    if period_id is not None:
        stmt = stmt.where(PriceRecord.period_id == period_id)
    else:
        # Auto-select latest period for this project
        latest = (
            select(func.max(ReportPeriod.id))
            .join(PriceRecord, PriceRecord.period_id == ReportPeriod.id)
            .where(
                PriceRecord.project_id == project_id,
                PriceRecord.unit_type_id.isnot(None),
            )
            .scalar_subquery()
        )
        stmt = stmt.where(PriceRecord.period_id == latest)

    stmt = stmt.order_by(UnitType.net_area_m2)
    rows = session.execute(stmt).all()
    return [
        {
            "unit_type_id": r[0],
            "type_name": r[1],
            "net_area_m2": r[2],
            "price_usd_per_m2": r[3],
            "price_vnd_per_m2": r[4],
        }
        for r in rows
    ]


def get_unit_type_price_variance(
    session: Session,
    project_id: int,
    period_id: Optional[int] = None,
) -> Optional[dict]:
    """Compute unit-type price dispersion and detect inverted structures.

    Returns dict with avg_price_usd, min, max, range, std_dev, cv_pct,
    is_inverted (True if larger units cost MORE per m2), price_area_correlation.
    Returns None if fewer than 2 unit-type prices exist.
    """
    prices = get_unit_type_prices(session, project_id, period_id)
    if len(prices) < 2:
        return None

    usd_prices = [p["price_usd_per_m2"] for p in prices if p["price_usd_per_m2"]]
    areas = [p["net_area_m2"] for p in prices if p["price_usd_per_m2"] and p["net_area_m2"]]

    if len(usd_prices) < 2 or len(areas) < 2:
        return None

    n = len(usd_prices)
    avg = sum(usd_prices) / n
    min_p = min(usd_prices)
    max_p = max(usd_prices)
    variance = sum((p - avg) ** 2 for p in usd_prices) / n
    std_dev = math.sqrt(variance)
    cv_pct = (std_dev / avg * 100) if avg else 0.0

    # Pearson correlation: area vs price
    mean_area = sum(areas) / len(areas)
    mean_price = sum(usd_prices) / len(usd_prices)
    cov = sum((a - mean_area) * (p - mean_price) for a, p in zip(areas, usd_prices)) / len(areas)
    std_area = math.sqrt(sum((a - mean_area) ** 2 for a in areas) / len(areas))
    std_price = math.sqrt(sum((p - mean_price) ** 2 for p in usd_prices) / len(usd_prices))
    correlation = cov / (std_area * std_price) if std_area > 0 and std_price > 0 else 0.0

    # r > +0.3 → inverted (larger units cost more per m2 — abnormal)
    is_inverted = correlation > 0.3

    return {
        "project_id": project_id,
        "unit_count": n,
        "avg_price_usd": round(avg, 0),
        "min_price_usd": round(min_p, 0),
        "max_price_usd": round(max_p, 0),
        "range_usd": round(max_p - min_p, 0),
        "std_dev": round(std_dev, 1),
        "cv_pct": round(cv_pct, 1),
        "is_inverted": is_inverted,
        "price_area_correlation": round(correlation, 3),
    }


def compare_unit_type_structures(
    session: Session,
    subject_id: int,
    competitor_ids: list[int],
    period_id: Optional[int] = None,
) -> dict:
    """Compare unit-type price structures between subject and competitors.

    Returns dict with subject, competitors, market averages, and anomalies.
    """
    subject_var = get_unit_type_price_variance(session, subject_id, period_id)
    subject_prices = get_unit_type_prices(session, subject_id, period_id)

    comp_results = []
    valid_cvs = []
    valid_avgs = []

    for cid in competitor_ids:
        var = get_unit_type_price_variance(session, cid, period_id)
        if var:
            comp_results.append(var)
            valid_cvs.append(var["cv_pct"])
            valid_avgs.append(var["avg_price_usd"])

    market_avg_cv = sum(valid_cvs) / len(valid_cvs) if valid_cvs else 0.0
    market_avg_price = sum(valid_avgs) / len(valid_avgs) if valid_avgs else 0.0

    subject_cv_premium = 0.0
    subject_price_gap_pct = 0.0
    anomalies: list[str] = []

    if subject_var:
        if market_avg_cv > 0:
            subject_cv_premium = round(subject_var["cv_pct"] - market_avg_cv, 1)
        if market_avg_price > 0:
            subject_price_gap_pct = round(
                (subject_var["avg_price_usd"] - market_avg_price)
                / market_avg_price * 100, 1
            )

        # Anomaly detection
        if subject_var["is_inverted"]:
            anomalies.append(
                f"INVERTED: Larger units cost MORE per m2 "
                f"(correlation={subject_var['price_area_correlation']:+.2f})"
            )
        if market_avg_cv > 0 and subject_var["cv_pct"] > 2 * market_avg_cv:
            anomalies.append(
                f"HIGH VARIANCE: CV {subject_var['cv_pct']:.1f}% "
                f"exceeds 2x market avg ({market_avg_cv:.1f}%)"
            )
        if abs(subject_price_gap_pct) > 15:
            direction = "above" if subject_price_gap_pct > 0 else "below"
            anomalies.append(
                f"PRICE GAP: {abs(subject_price_gap_pct):.1f}% {direction} market avg"
            )

    return {
        "subject": subject_var,
        "subject_prices": subject_prices,
        "competitors": comp_results,
        "market_avg_cv_pct": round(market_avg_cv, 1),
        "subject_cv_premium": subject_cv_premium,
        "market_avg_price_usd": round(market_avg_price, 0),
        "subject_price_gap_pct": subject_price_gap_pct,
        "anomalies": anomalies,
    }
