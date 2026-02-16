"""Market segment analysis: grade-level supply-demand trends and pricing."""

from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.models import (
    MarketSegmentSummary, Project, PriceRecord, ReportPeriod, City
)
from src.db.queries import get_city_by_name, get_period, get_grade_price_summary
from src.reports.charts import _fig_to_base64
from src.reports.renderer import render_template


# Standard market segments
SEGMENTS = {
    "Super-Luxury": ["SL"],
    "Luxury": ["L"],
    "High-End": ["H-I", "H-II"],
    "Mid-Range": ["M-I", "M-II", "M-III"],
    "Affordable": ["A-I", "A-II"],
}


def _get_segment_summaries(
    session: Session, city_id: int, year: int, half: str
) -> list[dict]:
    """Get market segment summaries from database.

    Args:
        session: Database session
        city_id: City ID
        year: Year
        half: H1 or H2

    Returns:
        List of segment summary dicts
    """
    period = session.execute(
        select(ReportPeriod).where(
            ReportPeriod.year == year,
            ReportPeriod.half == half
        )
    ).scalar_one_or_none()

    if not period:
        return []

    # Get stored segment summaries
    stmt = (
        select(MarketSegmentSummary)
        .where(
            MarketSegmentSummary.city_id == city_id,
            MarketSegmentSummary.period_id == period.id
        )
        .order_by(MarketSegmentSummary.avg_price_usd.desc())
    )
    summaries = session.execute(stmt).scalars().all()

    return [
        {
            "segment": s.segment or "Unknown",
            "grade_code": s.grade_code,
            "avg_price": s.avg_price_usd or 0,
            "total_supply": s.total_supply or 0,
            "total_sold": s.total_sold or 0,
            "absorption_rate": s.absorption_rate or 0,
            "new_launches": s.new_launches or 0,
        }
        for s in summaries
    ]


def _compute_segment_data(
    session: Session, city_id: int, year: int, half: str
) -> list[dict]:
    """Compute segment data from projects if no stored summaries exist.

    Args:
        session: Database session
        city_id: City ID
        year: Year
        half: H1 or H2

    Returns:
        List of computed segment dicts
    """
    grade_summary = get_grade_price_summary(session, city_id, year, half)
    if not grade_summary:
        return []

    results = []
    for segment_name, grade_codes in SEGMENTS.items():
        # Aggregate grades in this segment
        segment_prices = []
        segment_count = 0

        for grade_code, avg_price, min_price, max_price, count in grade_summary:
            if grade_code in grade_codes:
                segment_prices.append((avg_price, count))
                segment_count += count

        if segment_prices:
            # Weighted average price
            total_price_weight = sum(p * c for p, c in segment_prices)
            total_count = sum(c for _, c in segment_prices)
            avg_price = total_price_weight / total_count if total_count else 0

            results.append({
                "segment": segment_name,
                "grade_code": ", ".join(grade_codes),
                "avg_price": avg_price,
                "total_supply": 0,  # Would need supply_records data
                "total_sold": 0,
                "absorption_rate": 0,
                "new_launches": segment_count,
            })

    return sorted(results, key=lambda x: x["avg_price"], reverse=True)


def _segment_price_chart(segments: list[dict]) -> Optional[str]:
    """Create a bar chart showing average prices by segment.

    Args:
        segments: List of segment dicts

    Returns:
        Base64-encoded PNG image data URL
    """
    if not segments:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    names = [s["segment"] for s in segments]
    prices = [s["avg_price"] for s in segments]
    colors = ['purple', 'darkblue', 'steelblue', 'green', 'orange']

    bars = ax.bar(names, prices,
                   color=[colors[i % len(colors)] for i in range(len(names))],
                   edgecolor='black', linewidth=1.5)

    # Add value labels
    for bar, price in zip(bars, prices):
        if price > 0:
            ax.text(bar.get_x() + bar.get_width()/2., price,
                    f'${price:,.0f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Average Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Market Segment Pricing', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    plt.xticks(rotation=15, ha='right')

    plt.tight_layout()
    return _fig_to_base64(fig)


def _supply_demand_chart(segments: list[dict]) -> Optional[str]:
    """Create a grouped bar chart for supply vs sold units.

    Args:
        segments: List of segment dicts

    Returns:
        Base64-encoded PNG image data URL
    """
    # Filter segments with supply data
    data = [s for s in segments if s.get("total_supply", 0) > 0 or s.get("total_sold", 0) > 0]
    if not data:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    names = [s["segment"] for s in data]
    supply = [s["total_supply"] for s in data]
    sold = [s["total_sold"] for s in data]

    x = range(len(names))
    width = 0.35

    bars1 = ax.bar([i - width/2 for i in x], supply, width,
                    label='Total Supply', color='steelblue', edgecolor='black')
    bars2 = ax.bar([i + width/2 for i in x], sold, width,
                    label='Sold Units', color='coral', edgecolor='black')

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_ylabel('Unit Count', fontsize=11, fontweight='bold')
    ax.set_title('Supply vs Demand by Segment', fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    return _fig_to_base64(fig)


def _absorption_rate_chart(segments: list[dict]) -> Optional[str]:
    """Create a horizontal bar chart for absorption rates.

    Args:
        segments: List of segment dicts

    Returns:
        Base64-encoded PNG image data URL
    """
    # Filter segments with absorption data
    data = [(s["segment"], s["absorption_rate"])
            for s in segments if s.get("absorption_rate", 0) > 0]

    if not data:
        return None

    fig, ax = plt.subplots(figsize=(10, max(6, len(data) * 0.6)))

    names = [item[0] for item in data]
    rates = [item[1] for item in data]
    colors = ['green' if r >= 70 else 'orange' if r >= 50 else 'red' for r in rates]

    bars = ax.barh(names, rates, color=colors, edgecolor='black', linewidth=1.2, alpha=0.7)

    # Add value labels
    for bar, rate in zip(bars, rates):
        ax.text(rate + 2, bar.get_y() + bar.get_height()/2.,
                f'{rate:.1f}%',
                ha='left', va='center', fontsize=10, fontweight='bold')

    ax.axvline(x=70, color='green', linestyle='--', linewidth=1.5, alpha=0.5, label='Strong (70%)')
    ax.axvline(x=50, color='orange', linestyle='--', linewidth=1.5, alpha=0.5, label='Moderate (50%)')

    ax.set_xlabel('Absorption Rate (%)', fontsize=11, fontweight='bold')
    ax.set_title('Absorption Rate by Segment', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.set_xlim(0, 100)
    ax.legend(loc='lower right', fontsize=9)

    plt.tight_layout()
    return _fig_to_base64(fig)


def render_segment_analysis(
    session: Session,
    city_name: str,
    year: int = 2024,
    half: str = "H1",
) -> Optional[str]:
    """Generate a market segment analysis report.

    Args:
        session: Database session
        city_name: City name (supports aliases)
        year: Year for analysis
        half: Half for analysis (H1 or H2)

    Returns:
        Rendered markdown report string, or None if city not found
    """
    city = get_city_by_name(session, city_name)
    if not city:
        return None

    period = get_period(session, year, half)
    if not period:
        return None

    # Try to get stored summaries first
    segments = _get_segment_summaries(session, city.id, year, half)

    # If no stored data, compute from projects
    if not segments:
        segments = _compute_segment_data(session, city.id, year, half)

    if not segments:
        return None

    # Calculate market stats
    total_supply = sum(s["total_supply"] for s in segments)
    total_sold = sum(s["total_sold"] for s in segments)
    overall_absorption = (total_sold / total_supply * 100) if total_supply > 0 else 0

    # Identify dominant segments
    highest_price_seg = max(segments, key=lambda x: x["avg_price"]) if segments else None
    highest_supply_seg = max(segments, key=lambda x: x["total_supply"]) if segments else None
    highest_absorption_seg = max(segments, key=lambda x: x["absorption_rate"]) if segments else None

    # Generate charts
    chart_price = _segment_price_chart(segments)
    chart_supply_demand = _supply_demand_chart(segments)
    chart_absorption = _absorption_rate_chart(segments)

    context = {
        "generated_date": date.today().isoformat(),
        "city_name": city.name_en,
        "period": f"{year}-{half}",
        "segments": segments,
        "total_supply": total_supply,
        "total_sold": total_sold,
        "overall_absorption": overall_absorption,
        "highest_price_seg": highest_price_seg,
        "highest_supply_seg": highest_supply_seg,
        "highest_absorption_seg": highest_absorption_seg,
        "chart_price": chart_price,
        "chart_supply_demand": chart_supply_demand,
        "chart_absorption": chart_absorption,
    }

    return render_template("segment_analysis.md.j2", **context)
