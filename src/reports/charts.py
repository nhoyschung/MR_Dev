"""Chart generation utilities for reports using matplotlib."""

import base64
from io import BytesIO
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for server/CLI usage


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert matplotlib figure to base64-encoded PNG string."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"


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
