"""Unit-type price structure analysis report generation."""

from datetime import date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.models import Project, ReportPeriod
from src.db.queries import (
    get_unit_type_prices,
    get_unit_type_price_variance,
    compare_unit_type_structures,
    get_period,
)
from src.reports.renderer import render_template


def _resolve_project(session: Session, name: str) -> Optional[Project]:
    """Find a project by name (case-insensitive)."""
    stmt = select(Project).where(func.lower(Project.name) == name.lower())
    return session.execute(stmt).scalar_one_or_none()


def _assemble_unit_type_context(
    session: Session,
    project_name: str,
    competitor_names: list[str],
    year: int = 2025,
    half: str = "H2",
) -> Optional[dict]:
    """Assemble context dict shared by MD and PPTX renderers.

    Returns None if the subject project is not found or has no unit-type data.
    """
    subject = _resolve_project(session, project_name)
    if not subject:
        return None

    period = get_period(session, year, half)
    period_id = period.id if period else None

    subject_prices = get_unit_type_prices(session, subject.id, period_id)
    if not subject_prices:
        return None

    subject_variance = get_unit_type_price_variance(session, subject.id, period_id)

    # Resolve competitors
    competitors = []
    competitor_ids = []
    for cname in competitor_names:
        comp = _resolve_project(session, cname)
        if comp:
            competitors.append(comp)
            competitor_ids.append(comp.id)

    comparison = compare_unit_type_structures(
        session, subject.id, competitor_ids, period_id
    )

    # Attach project names to competitor variance results
    for i, comp_var in enumerate(comparison.get("competitors", [])):
        if i < len(competitors):
            comp_var["project_name"] = competitors[i].name

    # Build competitor detail tables
    competitor_details = []
    for comp in competitors:
        c_prices = get_unit_type_prices(session, comp.id, period_id)
        if c_prices:
            competitor_details.append({
                "project_name": comp.name,
                "unit_types": c_prices,
            })

    return {
        "generated_date": date.today().isoformat(),
        "subject_name": subject.name,
        "competitor_names": [c.name for c in competitors],
        "period": f"{year}-{half}",
        "subject_prices": subject_prices,
        "subject_variance": subject_variance,
        "comparison": comparison,
        "anomalies": comparison.get("anomalies", []),
        "competitor_details": competitor_details,
    }


def generate_unit_type_analysis(
    session: Session,
    project_name: str,
    competitor_names: list[str],
    year: int = 2025,
    half: str = "H2",
) -> Optional[str]:
    """Generate unit-type price structure analysis as Markdown.

    Returns None if the subject project is not found or has insufficient data.
    """
    context = _assemble_unit_type_context(
        session, project_name, competitor_names, year, half
    )
    if not context:
        return None

    return render_template("unit_type_analysis.md.j2", **context)
