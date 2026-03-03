"""Chart generation utilities for reports using matplotlib."""

import base64
from io import BytesIO
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for server/CLI usage


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert matplotlib figure to base64-encoded PNG string, then close figure."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"


def fig_to_bytesio(fig: plt.Figure, dpi: int = 150) -> BytesIO:
    """Render an open Figure to a BytesIO PNG buffer without closing the figure.

    Caller is responsible for closing the figure afterward.
    Used by PPTX builders that need to insert the image into a slide.
    """
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Figure factory functions (return open Figure; caller closes)
# ---------------------------------------------------------------------------

def create_grade_distribution_figure(grade_data: list[dict]) -> Optional[plt.Figure]:
    """Create grade distribution bar chart Figure (caller must close).

    Args:
        grade_data: List of dicts with 'grade' and 'count' keys.

    Returns:
        Open matplotlib Figure, or None if no data.
    """
    if not grade_data:
        return None

    grades = [item['grade'] for item in grade_data]
    counts = [item['count'] for item in grade_data]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(grades, counts, color='steelblue', edgecolor='darkblue', linewidth=1.2)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Grade', fontsize=11, fontweight='bold')
    ax.set_ylabel('Project Count', fontsize=11, fontweight='bold')
    ax.set_title('Project Distribution by Grade', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def create_radar_figure(
    projects_scores: list[tuple[str, dict[str, float]]],
    categories: list[str],
) -> Optional[plt.Figure]:
    """Create radar chart Figure for multi-project comparison (caller must close).

    Args:
        projects_scores: List of (project_name, scores_dict) tuples.
        categories: Ordered list of dimension labels.

    Returns:
        Open matplotlib Figure, or None if no data.
    """
    import numpy as np

    if not projects_scores:
        return None

    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    colors = ['blue', 'red', 'green', 'orange', 'purple']

    for idx, (proj_name, scores) in enumerate(projects_scores[:5]):
        values = [scores.get(cat, 0) for cat in categories]
        values += values[:1]
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
    return fig


def create_price_trend_figure(trend_data: list[dict]) -> Optional[plt.Figure]:
    """Create price trend line chart Figure (caller must close).

    Args:
        trend_data: List of dicts with 'period', 'price' keys (chronological order).

    Returns:
        Open matplotlib Figure, or None if no data.
    """
    if not trend_data:
        return None

    periods = [d['period'] for d in trend_data]
    prices = [d['price'] for d in trend_data]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(periods, prices, 'o-', linewidth=2.5, color='steelblue',
            markersize=7, markerfacecolor='white', markeredgewidth=2)

    for period, price in zip(periods, prices):
        ax.annotate(f'${price:,.0f}', (period, price),
                    textcoords='offset points', xytext=(0, 10),
                    ha='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Period', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Price Trend Over Time', fontsize=13, fontweight='bold', pad=15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    return fig


def create_supply_demand_figure(
    total_inventory: int,
    new_supply: int,
    sold_units: int,
    remaining_inventory: int,
    absorption_rate: float,
) -> Optional[plt.Figure]:
    """Create supply-demand bar chart Figure (caller must close).

    Args:
        total_inventory: Total units in inventory.
        new_supply: New units launched.
        sold_units: Units sold.
        remaining_inventory: Remaining unsold units.
        absorption_rate: Absorption rate percentage.

    Returns:
        Open matplotlib Figure, or None if no data.
    """
    if total_inventory == 0 and new_supply == 0:
        return None

    fig, ax1 = plt.subplots(figsize=(10, 5))
    categories = ['Total\nInventory', 'New\nSupply', 'Sold\nUnits', 'Remaining\nInventory']
    values = [total_inventory, new_supply, sold_units, remaining_inventory]
    colors = ['steelblue', 'mediumseagreen', 'coral', 'lightcoral']

    bars = ax1.bar(categories, values, color=colors, edgecolor='black', linewidth=1.2, alpha=0.8)
    for bar, val in zip(bars, values):
        if val > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2., val,
                     f'{val:,}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.set_ylabel('Unit Count', fontsize=11, fontweight='bold')
    ax1.set_title('Supply & Demand Metrics', fontsize=13, fontweight='bold', pad=15)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)

    if absorption_rate > 0:
        ax2 = ax1.twinx()
        ax2.axhline(y=absorption_rate, color='red', linestyle='--', linewidth=2,
                    label=f'Absorption Rate: {absorption_rate:.1f}%')
        ax2.set_ylabel('Absorption Rate (%)', fontsize=11, fontweight='bold', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    return fig


def create_price_comparison_figure(
    zone_avg: float,
    zone_min: float,
    zone_max: float,
    city_avg: float,
    zone_name: str,
    city_name: str,
) -> Optional[plt.Figure]:
    """Create price comparison bar chart Figure (caller must close).

    Returns:
        Open matplotlib Figure, or None if no data.
    """
    if zone_avg == 0 and city_avg == 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    categories = ['Zone Min', 'Zone Avg', 'City Avg', 'Zone Max']
    values = [zone_min, zone_avg, city_avg, zone_max]
    colors = ['lightcoral', 'steelblue', 'lightgreen', 'coral']

    bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.2)
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2., val,
                    f'${val:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title(f'Price Comparison: {zone_name} vs {city_name}',
                 fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    plt.tight_layout()
    return fig


def grade_distribution_chart(grade_data: list[dict]) -> Optional[str]:
    """Create a bar chart for grade distribution.

    Args:
        grade_data: List of dicts with 'grade' and 'count' keys

    Returns:
        Base64-encoded PNG image data URL, or None if no data
    """
    if not grade_data:
        return None

    grades = [item['grade'] for item in grade_data]
    counts = [item['count'] for item in grade_data]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(grades, counts, color='steelblue', edgecolor='darkblue', linewidth=1.2)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Grade', fontsize=11, fontweight='bold')
    ax.set_ylabel('Project Count', fontsize=11, fontweight='bold')
    ax.set_title('Project Distribution by Grade', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    return _fig_to_base64(fig)


def price_comparison_chart(
    zone_avg: float,
    zone_min: float,
    zone_max: float,
    city_avg: float,
    zone_name: str,
    city_name: str
) -> Optional[str]:
    """Create a bar chart comparing zone prices to city average.

    Args:
        zone_avg: Average price in zone (USD/m2)
        zone_min: Minimum price in zone
        zone_max: Maximum price in zone
        city_avg: City average price
        zone_name: District/zone name
        city_name: City name

    Returns:
        Base64-encoded PNG image data URL, or None if no data
    """
    if zone_avg == 0 and city_avg == 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    categories = ['Zone Min', 'Zone Avg', 'City Avg', 'Zone Max']
    values = [zone_min, zone_avg, city_avg, zone_max]
    colors = ['lightcoral', 'steelblue', 'lightgreen', 'coral']

    bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.2)

    # Add value labels
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2., val,
                    f'${val:,.0f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title(f'Price Comparison: {zone_name} vs {city_name}',
                 fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Format y-axis with thousands separator
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    return _fig_to_base64(fig)


def supply_demand_chart(
    total_inventory: int,
    new_supply: int,
    sold_units: int,
    remaining_inventory: int,
    absorption_rate: float
) -> Optional[str]:
    """Create a dual-axis chart for supply-demand metrics.

    Args:
        total_inventory: Total units in inventory
        new_supply: New units launched
        sold_units: Units sold
        remaining_inventory: Remaining unsold units
        absorption_rate: Absorption rate percentage

    Returns:
        Base64-encoded PNG image data URL, or None if no data
    """
    if total_inventory == 0 and new_supply == 0:
        return None

    fig, ax1 = plt.subplots(figsize=(10, 5))

    categories = ['Total\nInventory', 'New\nSupply', 'Sold\nUnits', 'Remaining\nInventory']
    values = [total_inventory, new_supply, sold_units, remaining_inventory]
    colors = ['steelblue', 'mediumseagreen', 'coral', 'lightcoral']

    bars = ax1.bar(categories, values, color=colors, edgecolor='black', linewidth=1.2, alpha=0.8)

    # Add value labels
    for bar, val in zip(bars, values):
        if val > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., val,
                     f'{val:,}',
                     ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.set_ylabel('Unit Count', fontsize=11, fontweight='bold')
    ax1.set_title('Supply & Demand Metrics', fontsize=13, fontweight='bold', pad=15)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)

    # Add absorption rate as a secondary y-axis if available
    if absorption_rate > 0:
        ax2 = ax1.twinx()
        ax2.axhline(y=absorption_rate, color='red', linestyle='--', linewidth=2,
                    label=f'Absorption Rate: {absorption_rate:.1f}%')
        ax2.set_ylabel('Absorption Rate (%)', fontsize=11, fontweight='bold', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    return _fig_to_base64(fig)


# ---------------------------------------------------------------------------
# Unit-type price analysis charts (return open Figure; caller closes)
# ---------------------------------------------------------------------------

_UNIT_TYPE_COLORS = ['#276EBF', '#C0392B', '#27AE60', '#E8A820', '#6A0DAD']


def create_unit_type_grouped_bar_figure(
    projects_data: list[dict],
) -> Optional[plt.Figure]:
    """Grouped bar chart: unit-type prices across projects (caller must close).

    Args:
        projects_data: List of dicts with 'project_name' and 'unit_types'
            (list of dicts with 'type_name', 'price_usd_per_m2').
    """
    import numpy as np

    if not projects_data:
        return None

    # Collect all unique unit types across projects
    all_types: list[str] = []
    for proj in projects_data:
        for ut in proj.get("unit_types", []):
            if ut["type_name"] not in all_types:
                all_types.append(ut["type_name"])
    if not all_types:
        return None

    n_groups = len(all_types)
    n_projects = len(projects_data)
    bar_width = 0.8 / max(n_projects, 1)
    x = np.arange(n_groups)

    fig, ax = plt.subplots(figsize=(max(10, n_groups * 2), 6))

    for i, proj in enumerate(projects_data):
        prices_map = {ut["type_name"]: ut["price_usd_per_m2"] for ut in proj.get("unit_types", [])}
        values = [prices_map.get(t, 0) for t in all_types]
        offset = (i - n_projects / 2 + 0.5) * bar_width
        bars = ax.bar(x + offset, values, bar_width * 0.9,
                       label=proj["project_name"],
                       color=_UNIT_TYPE_COLORS[i % len(_UNIT_TYPE_COLORS)],
                       edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, val,
                        f'${val:,.0f}', ha='center', va='bottom', fontsize=7, fontweight='bold')

    ax.set_xlabel('Unit Type', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Unit-Type Price Comparison', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(all_types, fontsize=9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f'${v:,.0f}'))
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def create_variance_comparison_figure(
    variance_data: list[dict],
) -> Optional[plt.Figure]:
    """Bar chart comparing CV% across projects (caller must close).

    Args:
        variance_data: List of dicts with 'project_name', 'cv_pct', 'is_subject'.
    """
    if not variance_data:
        return None

    names = [d["project_name"] for d in variance_data]
    cvs = [d["cv_pct"] for d in variance_data]
    colors = ['#E8A820' if d.get("is_subject") else 'steelblue' for d in variance_data]

    fig, ax = plt.subplots(figsize=(max(8, len(names) * 1.5), 5))
    bars = ax.bar(names, cvs, color=colors, edgecolor='black', linewidth=0.8)

    for bar, val in zip(bars, cvs):
        ax.text(bar.get_x() + bar.get_width() / 2, val,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Market normal baseline at 7.5%
    ax.axhline(y=7.5, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.text(len(names) - 0.5, 7.8, 'NORMAL ~7.5%', fontsize=8, color='green',
            ha='right', fontweight='bold')

    ax.set_ylabel('Coefficient of Variation (%)', fontsize=11, fontweight='bold')
    ax.set_title('Price Variance Comparison (CV%)', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.xticks(rotation=20, ha='right', fontsize=9)
    plt.tight_layout()
    return fig


def create_area_price_scatter_figure(
    scatter_data: list[dict],
) -> Optional[plt.Figure]:
    """Scatter plot: area vs price with per-project trend lines (caller must close).

    Args:
        scatter_data: List of dicts with 'project_name', 'points'
            (list of dicts with 'net_area_m2', 'price_usd_per_m2', 'type_name').
    """
    import numpy as np

    if not scatter_data:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, proj in enumerate(scatter_data):
        color = _UNIT_TYPE_COLORS[i % len(_UNIT_TYPE_COLORS)]
        points = proj.get("points", [])
        if not points:
            continue
        areas = [p["net_area_m2"] for p in points]
        prices = [p["price_usd_per_m2"] for p in points]

        ax.scatter(areas, prices, color=color, s=80, alpha=0.8,
                   edgecolors='white', linewidth=0.5, label=proj["project_name"])

        # Label each point with type_name
        for p in points:
            ax.annotate(p.get("type_name", ""), (p["net_area_m2"], p["price_usd_per_m2"]),
                        textcoords='offset points', xytext=(5, 5), fontsize=7, color=color)

        # Trend line
        if len(areas) >= 2:
            z = np.polyfit(areas, prices, 1)
            x_line = np.linspace(min(areas) - 5, max(areas) + 5, 50)
            y_line = np.polyval(z, x_line)
            slope = z[0]
            linestyle = '-' if slope > 0 else '--'
            line_color = 'red' if slope > 0 else color
            ax.plot(x_line, y_line, linestyle=linestyle, color=line_color, alpha=0.5, linewidth=1.5)
            if slope > 0:
                ax.text(max(areas), max(prices) + 50, 'INVERTED',
                        fontsize=8, color='red', fontweight='bold')

    ax.set_xlabel('Net Area (m²)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Area vs Price — Trend Analysis', fontsize=13, fontweight='bold', pad=15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f'${v:,.0f}'))
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Part C/D: Product Proposal + Compact Land Review charts
# ---------------------------------------------------------------------------

_PRODUCT_COLORS = {
    "townhouse": "#276EBF",
    "shophouse": "#C0392B",
    "villa": "#27AE60",
    "commercial_apt": "#E8A820",
    "social_apt": "#6A0DAD",
    "apartment": "#3498DB",
    "TH": "#276EBF",
    "SH": "#C0392B",
    "Villa": "#27AE60",
    "Semi-villa": "#2ECC71",
    "Single Villa": "#1ABC9C",
}


def create_phase_price_progression_figure(
    phases_data: list[dict],
) -> Optional[plt.Figure]:
    """Line chart: phase price progression by product type (caller must close).

    Args:
        phases_data: List of dicts with 'phase_code', and product-type price keys
            (e.g. 'townhouse_usd', 'villa_usd').
    """
    if not phases_data:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    phase_codes = [p["phase_code"] for p in phases_data]

    # Detect product types with price data
    product_keys = [k for k in phases_data[0] if k.endswith("_usd") and k != "phase_code"]
    for key in product_keys:
        label = key.replace("_usd", "").replace("_", " ").title()
        prices = [p.get(key) for p in phases_data]
        valid_indices = [i for i, v in enumerate(prices) if v]
        if not valid_indices:
            continue
        x_vals = [phase_codes[i] for i in valid_indices]
        y_vals = [prices[i] for i in valid_indices]
        color = _PRODUCT_COLORS.get(key.replace("_usd", ""), "gray")
        ax.plot(x_vals, y_vals, marker='o', linewidth=2, markersize=8,
                color=color, label=label)
        for xv, yv in zip(x_vals, y_vals):
            ax.annotate(f'${yv:,.0f}', (xv, yv), textcoords='offset points',
                        xytext=(0, 10), ha='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Phase', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Phase Price Progression', fontsize=13, fontweight='bold', pad=15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f'${v:,.0f}'))
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def create_zone_product_mix_figure(
    zones_data: list[dict],
) -> Optional[plt.Figure]:
    """Stacked bar: zone-level product type unit counts (caller must close).

    Args:
        zones_data: List of dicts with 'zone_code' and product-type unit counts
            (e.g. 'highrise_units', 'lowrise_units').
    """
    if not zones_data:
        return None

    import numpy as np

    fig, ax = plt.subplots(figsize=(10, 6))
    zone_labels = [f"Zone {z['zone_code']}" for z in zones_data]
    x = np.arange(len(zone_labels))

    keys = [k for k in zones_data[0] if k.endswith("_units") and k != "zone_code"]
    bottom = np.zeros(len(zones_data))
    for key in keys:
        label = key.replace("_units", "").replace("_", " ").title()
        vals = [z.get(key, 0) or 0 for z in zones_data]
        color = _PRODUCT_COLORS.get(key.replace("_units", ""), "gray")
        ax.bar(x, vals, bottom=bottom, label=label, color=color, edgecolor='white')
        bottom += np.array(vals)

    ax.set_xlabel('Zone', fontsize=11, fontweight='bold')
    ax.set_ylabel('Units', fontsize=11, fontweight='bold')
    ax.set_title('Zone Product Mix', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(zone_labels, fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def create_competitor_distance_band_figure(
    competitors_data: list[dict],
) -> Optional[plt.Figure]:
    """Bubble chart: distance vs price, size = units (caller must close).

    Args:
        competitors_data: List of dicts with 'name', 'distance_km', 'price_usd',
            'units', optional 'nho_target_price'.
    """
    if not competitors_data:
        return None

    fig, ax = plt.subplots(figsize=(10, 7))
    for i, c in enumerate(competitors_data):
        dist = c.get("distance_km", 0) or 0
        price = c.get("price_usd", 0) or 0
        units = c.get("units", 100) or 100
        if not price:
            continue
        color = _UNIT_TYPE_COLORS[i % len(_UNIT_TYPE_COLORS)]
        ax.scatter(dist, price, s=max(units / 3, 30), color=color,
                   alpha=0.7, edgecolors='black', linewidth=0.5)
        ax.annotate(c["name"], (dist, price), textcoords='offset points',
                    xytext=(5, 5), fontsize=7)

    # NHO target line if provided
    nho = next((c.get("nho_target_price") for c in competitors_data
                if c.get("nho_target_price")), None)
    if nho:
        ax.axhline(y=nho, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax.text(0.5, nho + 30, f'NHO Target ${nho:,.0f}', fontsize=9,
                color='red', fontweight='bold')

    ax.set_xlabel('Distance (km)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Competitor Distance vs Price', fontsize=13, fontweight='bold', pad=15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f'${v:,.0f}'))
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def create_competitor_unit_mix_figure(
    competitors_data: list[dict],
) -> Optional[plt.Figure]:
    """Stacked bar: competitor unit mix by bedroom type (caller must close).

    Args:
        competitors_data: List of dicts with 'name' and unit mix pct keys
            (e.g. 'Studio', '1BR-1WC', '2BR-2WC', etc.).
    """
    if not competitors_data:
        return None

    import numpy as np

    mix_keys = ["Studio", "1BR-1WC", "1.5BR-1WC", "2BR-1WC",
                "2BR-2WC", "2.5BR-2WC", "3BR-2WC"]
    mix_colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12',
                  '#9B59B6', '#1ABC9C', '#E67E22']

    fig, ax = plt.subplots(figsize=(max(10, len(competitors_data) * 1.5), 6))
    names = [c["name"][:20] for c in competitors_data]
    x = np.arange(len(names))
    width = 0.6
    bottom = np.zeros(len(competitors_data))

    for key, color in zip(mix_keys, mix_colors):
        vals = [c.get("unit_mix", {}).get(key, 0) for c in competitors_data]
        if any(v > 0 for v in vals):
            ax.bar(x, vals, width, bottom=bottom, label=key,
                   color=color, edgecolor='white', linewidth=0.5)
            bottom += np.array(vals)

    ax.set_ylabel('Unit Mix (%)', fontsize=11, fontweight='bold')
    ax.set_title('Competitor Unit Mix Breakdown', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha='right', fontsize=9)
    ax.legend(fontsize=8, loc='upper right', ncol=2)
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def create_absorption_timeline_figure(
    absorption_data: list[dict],
) -> Optional[plt.Figure]:
    """Bar chart: project absorption rates (caller must close).

    Args:
        absorption_data: List of dicts with 'name', 'sold_pct', 'absorption_note'.
    """
    if not absorption_data:
        return None

    fig, ax = plt.subplots(figsize=(max(8, len(absorption_data) * 1.5), 5))
    names = [d["name"][:20] for d in absorption_data]
    pcts = [d.get("sold_pct", 0) or 0 for d in absorption_data]
    notes = [d.get("absorption_note", "") or "" for d in absorption_data]

    # Color gradient: faster absorption = darker
    max_pct = max(pcts) if pcts else 1
    colors = [plt.cm.Blues(0.3 + 0.7 * (p / max_pct)) for p in pcts]

    bars = ax.bar(names, pcts, color=colors, edgecolor='black', linewidth=0.8)

    for bar, pct, note in zip(bars, pcts, notes):
        label = f'{pct:.0f}%'
        if note:
            short_note = note[:30] + ('...' if len(note) > 30 else '')
            label += f'\n{short_note}'
        ax.text(bar.get_x() + bar.get_width() / 2, pct,
                label, ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Sold (%)', fontsize=11, fontweight='bold')
    ax.set_title('Sales Absorption Performance', fontsize=13, fontweight='bold', pad=15)
    ax.set_ylim(0, max(pcts) * 1.3 if pcts else 100)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.xticks(rotation=20, ha='right', fontsize=9)
    plt.tight_layout()
    return fig


def price_range_scatter(projects: list[dict]) -> Optional[str]:
    """Create a scatter plot of project prices with grades.

    Args:
        projects: List of project dicts with 'name', 'price_usd', 'grade', 'units'

    Returns:
        Base64-encoded PNG image data URL, or None if no data
    """
    if not projects:
        return None

    # Filter projects with price data
    priced_projects = [p for p in projects if p.get('price_usd') and p['price_usd'] > 0]
    if not priced_projects:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Color map by grade
    grade_colors = {
        'SL': 'purple', 'L': 'darkblue', 'H-I': 'blue', 'H-II': 'steelblue',
        'M-I': 'green', 'M-II': 'lightgreen', 'M-III': 'yellowgreen',
        'A-I': 'orange', 'A-II': 'coral', 'N/A': 'gray'
    }

    for project in priced_projects:
        grade = project.get('grade', 'N/A')
        color = grade_colors.get(grade, 'gray')
        size = max(50, min(project.get('units', 0) / 10, 500))  # Scale by unit count

        ax.scatter(project['price_usd'], project.get('units', 0),
                   color=color, s=size, alpha=0.6, edgecolors='black', linewidth=0.5,
                   label=grade if grade not in [p.get('grade', 'N/A') for p in priced_projects[:priced_projects.index(project)]] else '')

    ax.set_xlabel('Price (USD/m²)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Total Units', fontsize=11, fontweight='bold')
    ax.set_title('Project Price vs Size by Grade', fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Format x-axis with thousands separator
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Legend
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc='upper right', fontsize=9, title='Grade')

    plt.tight_layout()
    return _fig_to_base64(fig)
