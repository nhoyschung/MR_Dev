"""Zone (district) analysis report: assemble data and render template."""

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import District, Project, PriceRecord, ReportPeriod
from src.db.queries import (
    avg_price_by_district,
    get_city_by_name,
    get_district_by_name,
    get_district_supply,
    get_period,
)
from src.reports.charts import (
    grade_distribution_chart,
    price_comparison_chart,
    supply_demand_chart,
    price_range_scatter,
)
from src.reports.renderer import render_template


def _find_district(
    session: Session, district_name: str, city_id: int
) -> Optional[District]:
    """Find district with exact match first, then fallback to partial match."""
    district = get_district_by_name(session, district_name, city_id=city_id)
    if district:
        return district
    return (
        session.execute(
            select(District).where(
                District.city_id == city_id,
                District.name_en.ilike(f"%{district_name}%"),
            )
        )
        .scalars()
        .first()
    )


def _grade_distribution(projects: list[Project]) -> list[dict]:
    """Build grade distribution for projects in the district."""
    counts: dict[str, int] = {}
    for p in projects:
        grade = p.grade_primary or "N/A"
        counts[grade] = counts.get(grade, 0) + 1
    return [
        {"grade": grade, "count": count}
        for grade, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]


def render_zone_analysis(
    session: Session,
    district_name: str,
    city_name: str,
    year: int = 2024,
    half: str = "H1",
) -> Optional[str]:
    """Render a district/zone analysis report.

    Returns rendered markdown string, or None if city/district/period not found.
    """
    city = get_city_by_name(session, city_name)
    if not city:
        return None

    district = _find_district(session, district_name, city.id)
    if not district:
        return None

    period = get_period(session, year, half)
    if not period:
        return None

    projects = (
        session.execute(select(Project).where(Project.district_id == district.id))
        .scalars()
        .all()
    )
    project_count = len(projects)
    active_projects = sum(
        1 for p in projects if p.status in ("selling", "under-construction")
    )
    planned_projects = sum(1 for p in projects if p.status == "planning")

    # District-level supply comes from supply_records keyed by district_id.
    supply_rows = get_district_supply(session, district.id, year, half)
    total_inventory = sum(r.total_inventory or 0 for r in supply_rows)
    new_supply = sum(r.new_supply or 0 for r in supply_rows)
    sold_units = sum(r.sold_units or 0 for r in supply_rows)
    remaining_inventory = sum(r.remaining_inventory or 0 for r in supply_rows)
    avg_absorption = (
        sum((r.absorption_rate_pct or 0) for r in supply_rows) / len(supply_rows)
        if supply_rows
        else 0
    )

    # Price landscape for this period.
    price_rows = (
        session.execute(
            select(PriceRecord.price_usd_per_m2)
            .join(Project, PriceRecord.project_id == Project.id)
            .where(
                Project.district_id == district.id,
                PriceRecord.period_id == period.id,
                PriceRecord.price_usd_per_m2.isnot(None),
            )
        )
        .scalars()
        .all()
    )
    zone_avg_price = sum(price_rows) / len(price_rows) if price_rows else 0
    zone_min_price = min(price_rows) if price_rows else 0
    zone_max_price = max(price_rows) if price_rows else 0

    city_avg_price = 0.0
    city_district_avgs = avg_price_by_district(session, city.id, year, half)
    if city_district_avgs:
        city_avg_price = sum(v for _, v in city_district_avgs) / len(city_district_avgs)

    # Project roster with period price.
    roster: list[dict] = []
    for p in sorted(projects, key=lambda x: x.name):
        period_price = (
            session.execute(
                select(PriceRecord.price_usd_per_m2).where(
                    PriceRecord.project_id == p.id,
                    PriceRecord.period_id == period.id,
                )
            )
            .scalars()
            .first()
        )
        roster.append(
            {
                "name": p.name,
                "developer": p.developer.name_en if p.developer else "N/A",
                "units": p.total_units or 0,
                "price_usd": period_price,
                "grade": p.grade_primary or "N/A",
                "status": p.status or "unknown",
            }
        )

    # Basic outlook narrative.
    outlook: list[str] = []
    if avg_absorption >= 80:
        outlook.append("Demand is strong based on district absorption.")
    elif avg_absorption >= 60:
        outlook.append("Demand is stable with moderate absorption.")
    elif avg_absorption > 0:
        outlook.append("Demand is cautious; absorption is below benchmark levels.")
    else:
        outlook.append("Absorption data is limited for this period.")

    if zone_avg_price and city_avg_price:
        if zone_avg_price > city_avg_price:
            outlook.append("District pricing is above city district-average levels.")
        elif zone_avg_price < city_avg_price:
            outlook.append("District pricing is below city district-average levels.")
        else:
            outlook.append("District pricing is aligned with city district-average levels.")

    if new_supply > sold_units:
        outlook.append("New supply exceeds sold units, so inventory pressure remains.")
    elif sold_units > 0:
        outlook.append("Sold units are keeping pace with incoming supply.")

    # Generate charts
    grade_dist = _grade_distribution(projects)
    chart_grade_dist = grade_distribution_chart(grade_dist)
    chart_price_comp = price_comparison_chart(
        zone_avg_price, zone_min_price, zone_max_price,
        city_avg_price, district.name_en, city.name_en
    )
    chart_supply_demand = supply_demand_chart(
        total_inventory, new_supply, sold_units,
        remaining_inventory, avg_absorption
    )
    chart_price_scatter = price_range_scatter(roster)

    context = {
        "generated_date": date.today().isoformat(),
        "period": f"{year}-{half}",
        "city_name": city.name_en,
        "district_name": district.name_en,
        "district_type": district.district_type or "N/A",
        "project_count": project_count,
        "active_projects": active_projects,
        "planned_projects": planned_projects,
        "total_inventory": total_inventory,
        "new_supply": new_supply,
        "sold_units": sold_units,
        "remaining_inventory": remaining_inventory,
        "avg_absorption": avg_absorption,
        "zone_avg_price": zone_avg_price,
        "zone_min_price": zone_min_price,
        "zone_max_price": zone_max_price,
        "city_avg_price": city_avg_price,
        "grade_distribution": grade_dist,
        "projects": roster,
        "outlook": outlook,
        # Charts (base64-encoded images)
        "chart_grade_distribution": chart_grade_dist,
        "chart_price_comparison": chart_price_comp,
        "chart_supply_demand": chart_supply_demand,
        "chart_price_scatter": chart_price_scatter,
    }
    return render_template("zone_analysis.md.j2", **context)
