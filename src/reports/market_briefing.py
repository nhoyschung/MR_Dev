"""Market briefing report — assemble data and render template."""

from datetime import date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.models import (
    City, District, Project, PriceRecord, ReportPeriod,
    GradeDefinition, SupplyRecord,
)
from src.db.queries import (
    get_city_by_name, get_period, list_projects_by_city,
    avg_price_by_district,
)
from src.reports.renderer import render_template


def _grade_distribution(
    session: Session, city_id: int, period_id: int, projects: list[Project],
) -> list[dict]:
    """Build grade distribution with project counts and avg prices."""
    grades = (
        session.execute(
            select(GradeDefinition)
            .where(GradeDefinition.city_id == city_id)
            .order_by(GradeDefinition.min_price_usd.desc())
        )
        .scalars()
        .all()
    )

    result = []
    for g in grades:
        matching = [
            p for p in projects if p.grade_primary == g.grade_code
        ]
        if not matching:
            result.append({
                "code": g.grade_code,
                "segment": g.segment,
                "min_price": g.min_price_usd or 0,
                "max_price": g.max_price_usd or 0,
                "project_count": 0,
                "avg_price": 0,
            })
            continue

        prices = []
        for p in matching:
            pr = (
                session.execute(
                    select(PriceRecord)
                    .where(
                        PriceRecord.project_id == p.id,
                        PriceRecord.period_id == period_id,
                    )
                    .limit(1)
                )
                .scalar_one_or_none()
            )
            if pr and pr.price_usd_per_m2:
                prices.append(pr.price_usd_per_m2)

        result.append({
            "code": g.grade_code,
            "segment": g.segment,
            "min_price": g.min_price_usd or 0,
            "max_price": g.max_price_usd or 0,
            "project_count": len(matching),
            "avg_price": sum(prices) / len(prices) if prices else 0,
        })
    return result


def _top_districts_by_price(
    session: Session, city_id: int, year: int, half: str, limit: int = 5,
) -> list[dict]:
    """Top districts ranked by average price."""
    avgs = avg_price_by_district(session, city_id, year, half)
    result = []
    for name, avg_price in avgs[:limit]:
        d = session.execute(
            select(District).where(
                District.city_id == city_id,
                func.lower(District.name_en) == name.lower(),
            )
        ).scalar_one_or_none()
        project_count = (
            session.execute(
                select(func.count(Project.id)).where(
                    Project.district_id == d.id
                )
            ).scalar()
            if d
            else 0
        )
        result.append({
            "name": name,
            "avg_price": avg_price,
            "project_count": project_count,
        })
    return result


def _top_districts_by_supply(
    session: Session, city_id: int, period_id: int, limit: int = 5,
) -> list[dict]:
    """Top districts ranked by new supply."""
    stmt = (
        select(
            District.name_en,
            func.sum(SupplyRecord.new_supply),
            func.avg(SupplyRecord.absorption_rate_pct),
        )
        .join(SupplyRecord, SupplyRecord.district_id == District.id)
        .where(
            District.city_id == city_id,
            SupplyRecord.period_id == period_id,
            SupplyRecord.project_id.is_(None),
        )
        .group_by(District.name_en)
        .order_by(func.sum(SupplyRecord.new_supply).desc())
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    return [
        {"name": r[0], "new_supply": r[1] or 0, "absorption": r[2] or 0}
        for r in rows
    ]


def _supply_pipeline(
    session: Session, projects: list[Project],
) -> list[dict]:
    """Aggregate projects by status with unit totals."""
    status_map: dict[str, dict] = {}
    for p in projects:
        status = p.status or "unknown"
        if status not in status_map:
            status_map[status] = {"status": status, "count": 0, "units": 0}
        status_map[status]["count"] += 1
        status_map[status]["units"] += p.total_units or 0
    return sorted(status_map.values(), key=lambda x: x["count"], reverse=True)


def render_market_briefing(
    session: Session,
    city_name: str,
    year: int,
    half: str,
) -> Optional[str]:
    """Render a full market briefing for a city/period.

    Returns rendered markdown string, or None if city/period not found.
    """
    city = get_city_by_name(session, city_name)
    if not city:
        return None

    period = get_period(session, year, half)
    if not period:
        return None

    projects = list_projects_by_city(session, city.name_en)
    if not projects:
        return None

    # Aggregate stats
    active_selling = sum(1 for p in projects if p.status == "selling")
    under_construction = sum(1 for p in projects if p.status == "under-construction")

    # Average price across all projects in this period
    price_rows = (
        session.execute(
            select(PriceRecord.price_usd_per_m2)
            .join(Project)
            .join(District)
            .where(
                District.city_id == city.id,
                PriceRecord.period_id == period.id,
                PriceRecord.price_usd_per_m2.isnot(None),
            )
        )
        .scalars()
        .all()
    )
    avg_price = sum(price_rows) / len(price_rows) if price_rows else 0

    # Average absorption
    absorption_rows = (
        session.execute(
            select(SupplyRecord.absorption_rate_pct)
            .join(District, SupplyRecord.district_id == District.id)
            .where(
                District.city_id == city.id,
                SupplyRecord.period_id == period.id,
                SupplyRecord.absorption_rate_pct.isnot(None),
                SupplyRecord.project_id.is_(None),
            )
        )
        .scalars()
        .all()
    )
    avg_absorption = (
        sum(absorption_rows) / len(absorption_rows) if absorption_rows else 0
    )

    context = {
        "city_name": city.name_en,
        "period": f"{year}-{half}",
        "generated_date": date.today().isoformat(),
        "project_count": len(projects),
        "active_selling": active_selling,
        "under_construction": under_construction,
        "avg_price_usd": avg_price,
        "avg_absorption": avg_absorption,
        "grades": _grade_distribution(session, city.id, period.id, projects),
        "top_districts_by_price": _top_districts_by_price(
            session, city.id, year, half
        ),
        "top_districts_by_supply": _top_districts_by_supply(
            session, city.id, period.id
        ),
        "price_changes": [],  # Requires multi-period data
        "supply_pipeline": _supply_pipeline(session, projects),
        "takeaways": _generate_takeaways(
            city.name_en, len(projects), avg_price, avg_absorption,
            active_selling,
        ),
    }

    return render_template("market_briefing.md.j2", **context)


def _generate_takeaways(
    city_name: str,
    project_count: int,
    avg_price: float,
    avg_absorption: float,
    active_selling: int,
) -> list[str]:
    """Generate key takeaways from market data."""
    takeaways = []
    takeaways.append(
        f"{city_name} market tracks {project_count} projects "
        f"with {active_selling} actively selling."
    )
    if avg_price > 0:
        takeaways.append(
            f"Average price sits at ${avg_price:,.0f}/m2 across all grades."
        )
    if avg_absorption > 0:
        takeaways.append(
            f"Market-wide absorption rate is {avg_absorption:.1f}%, "
            + (
                "indicating strong demand."
                if avg_absorption > 70
                else "indicating moderate demand."
                if avg_absorption > 40
                else "suggesting buyer caution."
            )
        )
    return takeaways
