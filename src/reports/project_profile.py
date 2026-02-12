"""Project profile report — assemble data and render template."""

from datetime import date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.models import (
    City, District, Project, PriceRecord, ReportPeriod, Developer,
    GradeDefinition,
)
from src.db.queries import (
    get_latest_price, get_price_history, list_projects_by_grade,
    list_projects_by_developer, get_grade_for_price,
)
from src.reports.renderer import render_template


def _find_project(session: Session, name: str) -> Optional[Project]:
    """Find a project by name (case-insensitive, substring match)."""
    # Exact match first
    proj = session.execute(
        select(Project).where(func.lower(Project.name) == name.lower())
    ).scalar_one_or_none()
    if proj:
        return proj

    # Substring match
    proj = session.execute(
        select(Project).where(Project.name.ilike(f"%{name}%")).limit(1)
    ).scalar_one_or_none()
    return proj


def _build_price_history(session: Session, project: Project) -> list[dict]:
    """Build price history list with period labels."""
    records = get_price_history(session, project.id)
    history = []
    prev_price = None
    for r in records:
        period = session.get(ReportPeriod, r.period_id)
        change = None
        if prev_price and r.price_usd_per_m2:
            pct = ((r.price_usd_per_m2 - prev_price) / prev_price) * 100
            change = f"{pct:+.1f}%"
        history.append({
            "period": f"{period.year}-{period.half}" if period else "?",
            "price": r.price_usd_per_m2 or 0,
            "change": change,
        })
        if r.price_usd_per_m2:
            prev_price = r.price_usd_per_m2
    return history


def render_project_profile(
    session: Session,
    project_name: str,
) -> Optional[str]:
    """Render a project profile report.

    Returns rendered markdown string, or None if project not found.
    """
    project = _find_project(session, project_name)
    if not project:
        return None

    # Build project context
    latest_price = get_latest_price(session, project.id)
    district = project.district
    city = district.city if district else None

    # Grade info
    grade_min = grade_max = segment = grade_position = None
    if city and latest_price and latest_price.price_usd_per_m2:
        grade_def = get_grade_for_price(
            session, city.id, latest_price.price_usd_per_m2
        )
        if grade_def:
            grade_min = grade_def.min_price_usd
            grade_max = grade_def.max_price_usd
            segment = grade_def.segment
            price_range = (grade_max or 0) - (grade_min or 0)
            if price_range > 0:
                pos = (latest_price.price_usd_per_m2 - (grade_min or 0)) / price_range
                if pos < 0.33:
                    grade_position = "Low end of grade"
                elif pos < 0.66:
                    grade_position = "Mid range of grade"
                else:
                    grade_position = "High end of grade"

    project_ctx = {
        "name": project.name,
        "developer_name": project.developer.name_en if project.developer else None,
        "district_name": district.name_en if district else "N/A",
        "city_name": city.name_en if city else "N/A",
        "project_type": project.project_type,
        "status": project.status,
        "total_units": project.total_units,
        "launch_date": project.launch_date,
        "completion_date": project.completion_date,
        "grade_primary": project.grade_primary,
        "segment": segment,
        "price_usd": f"{latest_price.price_usd_per_m2:,.0f}" if latest_price and latest_price.price_usd_per_m2 else None,
        "price_vnd": f"{latest_price.price_vnd_per_m2:,.0f}" if latest_price and latest_price.price_vnd_per_m2 else None,
        "grade_min": f"{grade_min:,.0f}" if grade_min else None,
        "grade_max": f"{grade_max:,.0f}" if grade_max else None,
        "grade_position": grade_position,
    }

    # Developer context
    developer = project.developer
    developer_projects = []
    if developer:
        dev_projects = list_projects_by_developer(session, developer.name_en)
        for dp in dev_projects:
            if dp.id == project.id:
                continue
            dp_price = get_latest_price(session, dp.id)
            developer_projects.append({
                "name": dp.name,
                "district": dp.district.name_en if dp.district else "N/A",
                "grade": dp.grade_primary,
                "price": f"{dp_price.price_usd_per_m2:,.0f}" if dp_price and dp_price.price_usd_per_m2 else None,
            })

    # District peers
    district_projects = []
    district_avg_price = None
    if district:
        peers = session.execute(
            select(Project).where(Project.district_id == district.id)
        ).scalars().all()
        peer_prices = []
        for dp in peers:
            if dp.id == project.id:
                continue
            dp_price = get_latest_price(session, dp.id)
            price_val = dp_price.price_usd_per_m2 if dp_price else None
            if price_val:
                peer_prices.append(price_val)
            district_projects.append({
                "name": dp.name,
                "grade": dp.grade_primary,
                "price": f"{price_val:,.0f}" if price_val else None,
            })
        if peer_prices:
            district_avg_price = f"{sum(peer_prices) / len(peer_prices):,.0f}"

    # Grade peers
    grade_peers = []
    if project.grade_primary:
        gp_list = list_projects_by_grade(session, project.grade_primary)
        for gp in gp_list:
            if gp.id == project.id:
                continue
            gp_price = get_latest_price(session, gp.id)
            grade_peers.append({
                "name": gp.name,
                "district": gp.district.name_en if gp.district else "N/A",
                "price": f"{gp_price.price_usd_per_m2:,.0f}" if gp_price and gp_price.price_usd_per_m2 else None,
            })

    price_history = _build_price_history(session, project)

    context = {
        "generated_date": date.today().isoformat(),
        "project": project_ctx,
        "price_history": price_history if len(price_history) > 1 else [],
        "developer": developer,
        "developer_projects": developer_projects,
        "district_projects": district_projects,
        "district_avg_price": district_avg_price,
        "grade_peers": grade_peers,
    }

    return render_template("project_profile.md.j2", **context)
