"""Common query helpers for the MR-System database."""

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.models import (
    City, District, Project, Developer, PriceRecord,
    GradeDefinition, ReportPeriod, SupplyRecord, MarketSegmentSummary,
    DistrictMetric,
)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_city_by_name(session: Session, name: str) -> Optional[City]:
    """Find a city by English name (case-insensitive)."""
    stmt = select(City).where(func.lower(City.name_en) == name.lower())
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
    stmt = (
        select(Project)
        .join(District)
        .join(City)
        .where(func.lower(City.name_en) == city_name.lower())
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

def get_latest_price(session: Session, project_id: int) -> Optional[PriceRecord]:
    """Get the most recent price record for a project."""
    stmt = (
        select(PriceRecord)
        .join(ReportPeriod)
        .where(PriceRecord.project_id == project_id)
        .order_by(ReportPeriod.year.desc(), ReportPeriod.half.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_price_history(session: Session, project_id: int) -> list[PriceRecord]:
    """Get all price records for a project, ordered chronologically."""
    stmt = (
        select(PriceRecord)
        .join(ReportPeriod)
        .where(PriceRecord.project_id == project_id)
        .order_by(ReportPeriod.year, ReportPeriod.half)
    )
    return list(session.execute(stmt).scalars().all())


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
        .join(Project)
        .join(ReportPeriod)
        .where(
            Project.district_id == district_id,
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
