"""District metrics dashboard: comparative analysis across districts in a city."""

from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.models import District, DistrictMetric, ReportPeriod, City
from src.db.queries import get_city_by_name, get_period
from src.reports.charts import _fig_to_base64
from src.reports.renderer import render_template


def _get_district_metrics_summary(
    session: Session, city_id: int, year: int, half: str
) -> list[dict]:
    """Get aggregated metrics for all districts in a city for a period.

    Args:
        session: Database session
        city_id: City ID
        year: Year
        half: H1 or H2

    Returns:
        List of dicts with district info and metrics
    """
    period = session.execute(
        select(ReportPeriod).where(
            ReportPeriod.year == year,
            ReportPeriod.half == half
        )
    ).scalar_one_or_none()

    if not period:
        return []

    # Get all districts in the city
    districts = session.execute(
        select(District).where(District.city_id == city_id)
        .order_by(District.name_en)
    ).scalars().all()

    results = []
    for district in districts:
        # Get metrics for this district in this period
        metrics_raw = session.execute(
            select(DistrictMetric).where(
                DistrictMetric.district_id == district.id,
                DistrictMetric.period_id == period.id
            )
        ).scalars().all()

        # Parse metrics into a dict
        metrics = {}
        for m in metrics_raw:
            metrics[m.metric_type] = m.value_numeric if m.value_numeric is not None else m.value_text

        # Only include districts with at least some metrics
        if metrics:
            results.append({
                "district_id": district.id,
                "district_name": district.name_en,
                "district_type": district.district_type or "N/A",
                "avg_price": metrics.get("avg_price", 0),
                "supply_count": int(metrics.get("supply_count", 0)),
                "avg_price_change_pct": metrics.get("avg_price_change_pct", 0),
                "absorption_rate": metrics.get("absorption_rate", 0),
                "new_supply": int(metrics.get("new_supply", 0)),
                "inventory": int(metrics.get("inventory", 0)),
            })

    return sorted(results, key=lambda x: x["avg_price"], reverse=True)


def _district_comparison_chart(districts_data: list[dict], metric_name: str, metric_label: str) -> Optional[str]:
    """Create a horizontal bar chart comparing districts by a metric.

    Args:
        districts_data: List of district dicts
        metric_name: Key name in the dict (e.g., 'avg_price', 'supply_count')
        metric_label: Display label for the metric

    Returns:
        Base64-encoded PNG image data URL
    """
    # Filter districts with non-zero values
    data = [(d["district_name"], d[metric_name]) for d in districts_data if d.get(metric_name, 0) > 0]
    if not data:
        return None

    # Sort by value descending
    data = sorted(data, key=lambda x: x[1], reverse=True)[:15]  # Top 15 districts

    fig, ax = plt.subplots(figsize=(10, max(6, len(data) * 0.4)))

    names = [item[0] for item in data]
    values = [item[1] for item in data]

    bars = ax.barh(names, values, color='steelblue', edgecolor='darkblue', linewidth=1.2)

    # Add value labels
    for bar, val in zip(bars, values):
        if 'price' in metric_name.lower():
            label = f'${val:,.0f}'
        else:
            label = f'{val:,.0f}'
        ax.text(val, bar.get_y() + bar.get_height()/2., label,
                ha='left', va='center', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    ax.set_xlabel(metric_label, fontsize=11, fontweight='bold')
    ax.set_title(f'{metric_label} by District', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    if 'price' in metric_name.lower():
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    return _fig_to_base64(fig)


def _supply_demand_heatmap(districts_data: list[dict]) -> Optional[str]:
    """Create a scatter plot showing supply vs price for districts.

    Args:
        districts_data: List of district dicts

    Returns:
        Base64-encoded PNG image data URL
    """
    # Filter districts with both supply and price data
    data = [(d["district_name"], d["supply_count"], d["avg_price"])
            for d in districts_data
            if d.get("supply_count", 0) > 0 and d.get("avg_price", 0) > 0]

    if not data:
        return None

    fig, ax = plt.subplots(figsize=(12, 8))

    names = [item[0] for item in data]
    supply = [item[1] for item in data]
    prices = [item[2] for item in data]

    # Scatter plot with size based on supply
    scatter = ax.scatter(supply, prices, s=[s*10 for s in supply],
                        alpha=0.6, c=prices, cmap='RdYlGn_r',
                        edgecolors='black', linewidth=1)

    # Add district labels
    for name, sup, price in zip(names, supply, prices):
        ax.annotate(name, (sup, price), fontsize=8,
                   xytext=(5, 5), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    ax.set_xlabel('Supply Count (Units)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Average Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('District Supply vs Price Analysis', fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Color bar
    cbar = plt.colorbar(scatter, ax=ax, label='Avg Price (USD/m²)')
    cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    return _fig_to_base64(fig)


def _price_change_chart(districts_data: list[dict]) -> Optional[str]:
    """Create a bar chart showing price changes across districts.

    Args:
        districts_data: List of district dicts with price change data

    Returns:
        Base64-encoded PNG image data URL
    """
    # Filter districts with price change data
    data = [(d["district_name"], d["avg_price_change_pct"])
            for d in districts_data
            if d.get("avg_price_change_pct") is not None and d["avg_price_change_pct"] != 0]

    if not data:
        return None

    # Sort by change percentage
    data = sorted(data, key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(data) * 0.4)))

    names = [item[0] for item in data]
    changes = [item[1] for item in data]
    colors = ['green' if c > 0 else 'red' for c in changes]

    bars = ax.barh(names, changes, color=colors, edgecolor='black', linewidth=1.2, alpha=0.7)

    # Add value labels
    for bar, val in zip(bars, changes):
        label = f'{val:+.1f}%'
        x_pos = val + (0.5 if val > 0 else -0.5)
        ax.text(x_pos, bar.get_y() + bar.get_height()/2., label,
                ha='left' if val > 0 else 'right', va='center',
                fontsize=9, fontweight='bold')

    ax.axvline(x=0, color='black', linewidth=1.5, linestyle='-')
    ax.set_xlabel('Price Change (%)', fontsize=11, fontweight='bold')
    ax.set_title('Price Change by District', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    return _fig_to_base64(fig)


def render_district_dashboard(
    session: Session,
    city_name: str,
    year: int = 2024,
    half: str = "H1",
) -> Optional[str]:
    """Generate a district metrics dashboard for a city.

    Args:
        session: Database session
        city_name: City name (supports aliases)
        year: Year for analysis
        half: Half for analysis (H1 or H2)

    Returns:
        Rendered markdown dashboard string, or None if city not found
    """
    city = get_city_by_name(session, city_name)
    if not city:
        return None

    period = get_period(session, year, half)
    if not period:
        return None

    # Get district metrics
    districts_data = _get_district_metrics_summary(session, city.id, year, half)
    if not districts_data:
        return None

    # Calculate summary stats
    total_districts = len(districts_data)
    avg_city_price = sum(d["avg_price"] for d in districts_data) / total_districts if total_districts else 0
    total_supply = sum(d["supply_count"] for d in districts_data)

    # Identify top/bottom performers
    top_price = max(districts_data, key=lambda x: x["avg_price"]) if districts_data else None
    bottom_price = min((d for d in districts_data if d["avg_price"] > 0),
                       key=lambda x: x["avg_price"], default=None)
    top_supply = max(districts_data, key=lambda x: x["supply_count"]) if districts_data else None

    # Generate charts
    chart_price = _district_comparison_chart(districts_data, "avg_price", "Average Price (USD/m²)")
    chart_supply = _district_comparison_chart(districts_data, "supply_count", "Supply Count (Units)")
    chart_heatmap = _supply_demand_heatmap(districts_data)
    chart_price_change = _price_change_chart(districts_data)

    context = {
        "generated_date": date.today().isoformat(),
        "city_name": city.name_en,
        "period": f"{year}-{half}",
        "year": year,
        "half": half,
        "total_districts": total_districts,
        "avg_city_price": avg_city_price,
        "total_supply": total_supply,
        "top_price_district": top_price,
        "bottom_price_district": bottom_price,
        "top_supply_district": top_supply,
        "districts": districts_data,
        "chart_price": chart_price,
        "chart_supply": chart_supply,
        "chart_heatmap": chart_heatmap,
        "chart_price_change": chart_price_change,
    }

    return render_template("district_dashboard.md.j2", **context)
