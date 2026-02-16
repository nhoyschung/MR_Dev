"""Competitor benchmarking report: 11-dimension comparative analysis."""

from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import (
    Project, CompetitorComparison, PriceRecord, ReportPeriod,
    ProjectFacility, ProjectSalesPoint
)
from src.db.queries import get_latest_price, get_period
from src.reports.charts import _fig_to_base64
from src.reports.renderer import render_template


# 11 standard comparison dimensions
DIMENSIONS = [
    "Location",
    "Transportation",
    "Surroundings",
    "Design",
    "Facilities",
    "Unit Layout",
    "Pricing",
    "Developer Brand",
    "Payment Terms",
    "Legal Status",
    "Management",
]


def _get_project_score_data(
    session: Session, project_id: int, period_id: int
) -> dict[str, float]:
    """Get stored dimension scores for a project from database.

    Args:
        session: Database session
        project_id: Project ID
        period_id: Period ID

    Returns:
        Dict of dimension -> score
    """
    # Get scores where this project is the subject
    stmt = (
        select(CompetitorComparison)
        .where(
            CompetitorComparison.subject_project_id == project_id,
            CompetitorComparison.period_id == period_id
        )
    )
    comparisons = session.execute(stmt).scalars().all()

    scores = {}
    for comp in comparisons:
        if comp.dimension and comp.subject_score is not None:
            scores[comp.dimension] = comp.subject_score

    return scores


def _auto_score_project(session: Session, project: Project, period_id: int) -> dict[str, float]:
    """Auto-generate dimension scores based on available data.

    Args:
        session: Database session
        project: Project object
        period_id: Period ID

    Returns:
        Dict of dimension -> score (1-10 scale)
    """
    scores = {}

    # 1. Location - Based on district type and city
    if project.district:
        if project.district.district_type in ("urban", "central"):
            scores["Location"] = 8.0
        elif project.district.district_type in ("suburban"):
            scores["Location"] = 6.0
        else:
            scores["Location"] = 5.0

    # 2. Transportation - Placeholder (would need infrastructure data)
    scores["Transportation"] = 6.0

    # 3. Surroundings - Placeholder
    scores["Surroundings"] = 6.0

    # 4. Design - Based on project type
    if project.project_type == "mixed-use":
        scores["Design"] = 7.0
    elif project.project_type == "apartment":
        scores["Design"] = 6.0
    else:
        scores["Design"] = 5.0

    # 5. Facilities - Count from project_facilities table
    facility_count = session.execute(
        select(ProjectFacility).where(ProjectFacility.project_id == project.id)
    ).scalars().all()
    if len(facility_count) >= 5:
        scores["Facilities"] = 8.0
    elif len(facility_count) >= 3:
        scores["Facilities"] = 6.0
    else:
        scores["Facilities"] = 4.0

    # 6. Unit Layout - Based on total units (proxy for variety)
    if project.total_units and project.total_units > 1000:
        scores["Unit Layout"] = 7.0
    elif project.total_units and project.total_units > 500:
        scores["Unit Layout"] = 6.0
    else:
        scores["Unit Layout"] = 5.0

    # 7. Pricing - Based on grade (relative value)
    if project.grade_primary in ("SL", "L"):
        scores["Pricing"] = 7.0
    elif project.grade_primary in ("H-I", "H-II"):
        scores["Pricing"] = 6.0
    elif project.grade_primary in ("M-I", "M-II", "M-III"):
        scores["Pricing"] = 5.0
    else:
        scores["Pricing"] = 4.0

    # 8. Developer Brand - Check if developer exists
    if project.developer:
        # Check developer's project count as proxy for brand strength
        dev_projects = session.execute(
            select(Project).where(Project.developer_id == project.developer.id)
        ).scalars().all()
        if len(dev_projects) >= 5:
            scores["Developer Brand"] = 8.0
        elif len(dev_projects) >= 2:
            scores["Developer Brand"] = 6.0
        else:
            scores["Developer Brand"] = 5.0
    else:
        scores["Developer Brand"] = 4.0

    # 9. Payment Terms - Check sales points
    sales_points = session.execute(
        select(ProjectSalesPoint).where(ProjectSalesPoint.project_id == project.id)
    ).scalars().all()
    if len(sales_points) >= 3:
        scores["Payment Terms"] = 7.0
    elif len(sales_points) >= 1:
        scores["Payment Terms"] = 6.0
    else:
        scores["Payment Terms"] = 5.0

    # 10. Legal Status - Based on project status
    if project.status == "completed":
        scores["Legal Status"] = 9.0
    elif project.status == "selling":
        scores["Legal Status"] = 7.0
    elif project.status == "under-construction":
        scores["Legal Status"] = 6.0
    else:
        scores["Legal Status"] = 4.0

    # 11. Management - Placeholder
    scores["Management"] = 6.0

    return scores


def _radar_chart(projects_scores: list[tuple[str, dict[str, float]]]) -> Optional[str]:
    """Create a radar chart comparing projects across dimensions.

    Args:
        projects_scores: List of (project_name, scores_dict) tuples

    Returns:
        Base64-encoded PNG image data URL
    """
    if not projects_scores:
        return None

    # Use standard dimensions
    categories = DIMENSIONS
    num_vars = len(categories)

    # Create angles for radar chart
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    colors = ['blue', 'red', 'green', 'orange', 'purple']
    for idx, (proj_name, scores) in enumerate(projects_scores[:5]):  # Max 5 projects
        values = [scores.get(cat, 0) for cat in categories]
        values += values[:1]  # Complete the circle

        ax.plot(angles, values, 'o-', linewidth=2, label=proj_name,
                color=colors[idx % len(colors)])
        ax.fill(angles, values, alpha=0.15, color=colors[idx % len(colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], size=8)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_title('11-Dimension Competitive Analysis', size=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

    plt.tight_layout()
    return _fig_to_base64(fig)


def _score_comparison_chart(projects_scores: list[tuple[str, dict[str, float]]]) -> Optional[str]:
    """Create a grouped bar chart comparing total scores.

    Args:
        projects_scores: List of (project_name, scores_dict) tuples

    Returns:
        Base64-encoded PNG image data URL
    """
    if not projects_scores:
        return None

    fig, ax = plt.subplots(figsize=(max(8, len(projects_scores) * 2), 6))

    names = [p[0] for p in projects_scores]
    totals = [sum(p[1].values()) for p in projects_scores]
    colors = ['steelblue', 'coral', 'lightgreen', 'gold', 'plum']

    bars = ax.bar(range(len(names)), totals,
                   color=[colors[i % len(colors)] for i in range(len(names))],
                   edgecolor='black', linewidth=1.5)

    # Add value labels
    for bar, total in zip(bars, totals):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{total:.1f}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_ylabel('Total Score', fontsize=11, fontweight='bold')
    ax.set_title('Overall Competitive Score Comparison', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(totals) * 1.1)

    plt.tight_layout()
    return _fig_to_base64(fig)


def render_competitor_benchmark(
    session: Session,
    project_names: list[str],
    year: int = 2024,
    half: str = "H1",
) -> Optional[str]:
    """Generate an 11-dimension competitor benchmarking report.

    Args:
        session: Database session
        project_names: List of 2-5 project names to compare
        year: Year for analysis
        half: Half for analysis (H1 or H2)

    Returns:
        Rendered markdown report string, or None if projects not found
    """
    if len(project_names) < 2:
        return None

    period = get_period(session, year, half)
    if not period:
        return None

    # Load projects
    projects = []
    for name in project_names[:5]:  # Max 5 projects
        stmt = select(Project).where(Project.name.ilike(f"%{name}%"))
        project = session.execute(stmt).scalars().first()
        if project:
            projects.append(project)

    if len(projects) < 2:
        return None

    # Get scores for each project
    projects_scores = []
    projects_data = []

    for project in projects:
        # Try to get stored scores first
        scores = _get_project_score_data(session, project.id, period.id)

        # If no stored scores, auto-generate
        if not scores or len(scores) < 5:
            scores = _auto_score_project(session, project, period.id)

        projects_scores.append((project.name, scores))

        # Get price data
        price_record = get_latest_price(session, project.id)
        price_usd = price_record.price_usd_per_m2 if price_record else 0

        # Calculate value score (total score / price normalized)
        total_score = sum(scores.values())
        value_index = (total_score / price_usd * 1000) if price_usd > 0 else 0

        projects_data.append({
            "name": project.name,
            "developer": project.developer.name_en if project.developer else "N/A",
            "district": project.district.name_en if project.district else "N/A",
            "city": project.district.city.name_en if project.district and project.district.city else "N/A",
            "grade": project.grade_primary or "N/A",
            "price_usd": price_usd,
            "total_units": project.total_units or 0,
            "status": project.status or "unknown",
            "scores": scores,
            "total_score": total_score,
            "value_index": value_index,
        })

    # Determine winner for each dimension
    dimension_winners = {}
    for dim in DIMENSIONS:
        scores_for_dim = [(p["name"], p["scores"].get(dim, 0)) for p in projects_data]
        if scores_for_dim:
            winner = max(scores_for_dim, key=lambda x: x[1])
            dimension_winners[dim] = winner[0]

    # Overall winner
    overall_winner = max(projects_data, key=lambda x: x["total_score"])
    best_value = max(projects_data, key=lambda x: x["value_index"])

    # Generate charts
    chart_radar = _radar_chart(projects_scores)
    chart_total = _score_comparison_chart(projects_scores)

    context = {
        "generated_date": date.today().isoformat(),
        "period": f"{year}-{half}",
        "projects": projects_data,
        "dimensions": DIMENSIONS,
        "dimension_winners": dimension_winners,
        "overall_winner": overall_winner["name"],
        "best_value": best_value["name"],
        "chart_radar": chart_radar,
        "chart_total": chart_total,
    }

    return render_template("competitor_benchmark.md.j2", **context)
