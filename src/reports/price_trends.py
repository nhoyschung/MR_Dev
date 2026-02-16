"""Price trend analysis report with YoY/QoQ calculations and visualizations."""

from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import PriceChangeFactor, ReportPeriod, City
from src.db.queries import (
    get_city_by_name,
    get_city_price_trend,
    get_grade_price_summary,
    get_project_price_changes,
    get_price_range_by_city,
)
from src.reports.charts import _fig_to_base64
from src.reports.renderer import render_template


def _calculate_period_changes(trend_data: list[tuple[int, str, float, int]]) -> list[dict]:
    """Calculate QoQ and YoY changes from price trend data.

    Args:
        trend_data: List of (year, half, avg_price, count) tuples

    Returns:
        List of dicts with period info, prices, and change percentages
    """
    results = []
    for i, (year, half, price, count) in enumerate(trend_data):
        period_key = f"{year}-{half}"
        item = {
            "period": period_key,
            "year": year,
            "half": half,
            "avg_price": price,
            "project_count": count,
            "qoq_change": None,
            "yoy_change": None,
        }

        # QoQ: Compare to previous half (H1 -> prev H2, H2 -> current H1)
        if i > 0:
            prev_price = trend_data[i-1][2]
            if prev_price > 0:
                item["qoq_change"] = ((price - prev_price) / prev_price) * 100

        # YoY: Compare to same half one year ago
        target_year = year - 1
        for y, h, p, c in trend_data[:i]:
            if y == target_year and h == half:
                if p > 0:
                    item["yoy_change"] = ((price - p) / p) * 100
                break

        results.append(item)

    return results


def _price_trend_chart(trend_data: list[dict]) -> Optional[str]:
    """Create a line chart showing price trends over time.

    Args:
        trend_data: List of period dicts with 'period' and 'avg_price'

    Returns:
        Base64-encoded PNG image data URL
    """
    if not trend_data:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    periods = [item['period'] for item in trend_data]
    prices = [item['avg_price'] for item in trend_data]

    ax.plot(periods, prices, marker='o', linewidth=2, markersize=8,
            color='steelblue', markerfacecolor='coral', markeredgecolor='black')

    # Add value labels
    for period, price in zip(periods, prices):
        ax.text(period, price, f'${price:,.0f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Period', fontsize=11, fontweight='bold')
    ax.set_ylabel('Average Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Price Trend Analysis', fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.xticks(rotation=45, ha='right')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    return _fig_to_base64(fig)


def _qoq_yoy_chart(trend_data: list[dict]) -> Optional[str]:
    """Create a dual-line chart showing QoQ and YoY changes.

    Args:
        trend_data: List of period dicts with 'qoq_change' and 'yoy_change'

    Returns:
        Base64-encoded PNG image data URL
    """
    # Filter out periods without change data
    data_with_changes = [d for d in trend_data if d.get('qoq_change') or d.get('yoy_change')]
    if not data_with_changes:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    periods = [item['period'] for item in data_with_changes]
    qoq = [item.get('qoq_change') or 0 for item in data_with_changes]
    yoy = [item.get('yoy_change') or 0 for item in data_with_changes]

    ax.plot(periods, qoq, marker='o', linewidth=2, markersize=7,
            color='green', label='QoQ Change (%)', markeredgecolor='black')
    ax.plot(periods, yoy, marker='s', linewidth=2, markersize=7,
            color='blue', label='YoY Change (%)', markeredgecolor='black')

    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.7)

    ax.set_xlabel('Period', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price Change (%)', fontsize=11, fontweight='bold')
    ax.set_title('Quarter-over-Quarter & Year-over-Year Price Changes',
                 fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.legend(loc='best', fontsize=10)
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    return _fig_to_base64(fig)


def _grade_price_chart(grade_data: list[tuple[str, float, float, float, int]]) -> Optional[str]:
    """Create a bar chart showing price ranges by grade.

    Args:
        grade_data: List of (grade, avg, min, max, count) tuples

    Returns:
        Base64-encoded PNG image data URL
    """
    if not grade_data:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    grades = [item[0] for item in grade_data]
    avgs = [item[1] for item in grade_data]
    mins = [item[2] for item in grade_data]
    maxs = [item[3] for item in grade_data]

    x = range(len(grades))
    width = 0.6

    # Bar chart for averages
    bars = ax.bar(x, avgs, width, color='steelblue', edgecolor='black',
                   linewidth=1.2, label='Average Price')

    # Error bars showing min-max range
    for i, (avg, min_val, max_val) in enumerate(zip(avgs, mins, maxs)):
        ax.plot([i, i], [min_val, max_val], color='red', linewidth=2, alpha=0.7)
        ax.scatter([i, i], [min_val, max_val], color='red', s=50, zorder=3)

    # Value labels
    for bar, avg in zip(bars, avgs):
        ax.text(bar.get_x() + bar.get_width()/2., avg,
                f'${avg:,.0f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(grades)
    ax.set_xlabel('Grade', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Price Distribution by Grade (Avg, Min, Max)',
                 fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    return _fig_to_base64(fig)


def _get_price_factors(
    session: Session, city_id: int, period_year: int, period_half: str
) -> list[dict]:
    """Get price change factors for a city/period.

    Args:
        session: Database session
        city_id: City ID
        period_year: Year
        period_half: H1 or H2

    Returns:
        List of price factor dicts with type, category, description
    """
    from src.db.models import PriceRecord, Project, District

    # Get period ID
    period = session.execute(
        select(ReportPeriod).where(
            ReportPeriod.year == period_year,
            ReportPeriod.half == period_half
        )
    ).scalar_one_or_none()

    if not period:
        return []

    # Get price change factors via PriceRecord → Project → District → City
    stmt = (
        select(PriceChangeFactor)
        .join(PriceRecord, PriceChangeFactor.price_record_id == PriceRecord.id)
        .join(Project, PriceRecord.project_id == Project.id)
        .join(District, Project.district_id == District.id)
        .where(
            District.city_id == city_id,
            PriceRecord.period_id == period.id
        )
        .order_by(
            PriceChangeFactor.factor_type.desc(),  # 'increase' before 'decrease'
        )
    )
    factors = session.execute(stmt).scalars().all()

    return [
        {
            "type": f.factor_type,
            "category": f.factor_category,
            "description": f.description or "",
        }
        for f in factors
    ]


def render_price_trend_report(
    session: Session,
    city_name: str,
    focus_year: int = 2024,
    focus_half: str = "H1",
) -> Optional[str]:
    """Generate a comprehensive price trend analysis report.

    Args:
        session: Database session
        city_name: City name (supports aliases)
        focus_year: Year for detailed analysis
        focus_half: Half for detailed analysis (H1 or H2)

    Returns:
        Rendered markdown report string, or None if city not found
    """
    city = get_city_by_name(session, city_name)
    if not city:
        return None

    # 1. Price trend over all periods
    trend_raw = get_city_price_trend(session, city_name)
    if not trend_raw:
        return None

    trend_analysis = _calculate_period_changes(trend_raw)

    # 2. Grade price summary for focus period
    grade_summary = get_grade_price_summary(session, city.id, focus_year, focus_half)

    # 3. Project-level price changes
    project_changes = get_project_price_changes(session, city.id)
    top_gainers = [p for p in project_changes if p['change_pct'] > 0][:5]
    top_decliners = [p for p in project_changes if p['change_pct'] < 0][:5]

    # 4. Price range for focus period
    price_range = get_price_range_by_city(session, city_name, focus_year, focus_half)

    # 5. Price change factors
    price_factors = _get_price_factors(session, city.id, focus_year, focus_half)
    increase_factors = [f for f in price_factors if f['type'] == 'increase']
    decrease_factors = [f for f in price_factors if f['type'] == 'decrease']

    # Generate charts
    chart_trend = _price_trend_chart(trend_analysis)
    chart_qoq_yoy = _qoq_yoy_chart(trend_analysis)
    chart_grade = _grade_price_chart(grade_summary) if grade_summary else None

    # Context for template
    context = {
        "generated_date": date.today().isoformat(),
        "city_name": city.name_en,
        "focus_period": f"{focus_year}-{focus_half}",
        "focus_year": focus_year,
        "focus_half": focus_half,
        "trend_data": trend_analysis,
        "grade_summary": [
            {
                "grade": g[0],
                "avg_price": g[1],
                "min_price": g[2],
                "max_price": g[3],
                "project_count": g[4],
            }
            for g in grade_summary
        ] if grade_summary else [],
        "top_gainers": top_gainers,
        "top_decliners": top_decliners,
        "price_range": {
            "min": price_range[0] if price_range else 0,
            "avg": price_range[1] if price_range else 0,
            "max": price_range[2] if price_range else 0,
        } if price_range else None,
        "increase_factors": increase_factors,
        "decrease_factors": decrease_factors,
        "chart_trend": chart_trend,
        "chart_qoq_yoy": chart_qoq_yoy,
        "chart_grade": chart_grade,
    }

    return render_template("price_trends.md.j2", **context)
