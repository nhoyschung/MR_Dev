"""Schematic competitor location map (matplotlib-based PNG)."""

from io import BytesIO
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np


def generate_competitor_map(
    site_name: str,
    competitors: list[dict],
    distance_rings: list[float] | None = None,
    output_path: str | None = None,
) -> bytes:
    """Schematic competitor map with distance rings.

    Args:
        site_name: Name of the subject site (center).
        competitors: List with 'name', 'distance_km', 'price_usd', 'units', 'status'.
        distance_rings: Concentric ring radii in km (default [3, 5, 8]).
        output_path: If set, save PNG to this path.

    Returns:
        PNG bytes.
    """
    if distance_rings is None:
        distance_rings = [3, 5, 8]

    fig, ax = plt.subplots(figsize=(10, 10))
    max_ring = max(distance_rings) * 1.2

    # Draw rings
    for r in distance_rings:
        circle = plt.Circle((0, 0), r, fill=False, linestyle='--',
                             color='gray', alpha=0.5, linewidth=1)
        ax.add_patch(circle)
        ax.text(0, r + 0.15, f'{r}km', ha='center', fontsize=8, color='gray')

    # Plot site center
    ax.plot(0, 0, marker='*', markersize=20, color='red', zorder=5)
    ax.text(0, -0.5, site_name, ha='center', fontsize=10, fontweight='bold', color='red')

    # Plot competitors at approximate angles
    n = len(competitors)
    for i, comp in enumerate(competitors):
        dist = comp.get("distance_km", 5) or 5
        angle = 2 * np.pi * i / max(n, 1)
        x = dist * np.cos(angle)
        y = dist * np.sin(angle)

        units = comp.get("units", 100) or 100
        size = max(30, min(units / 5, 300))
        price = comp.get("price_usd", 0) or 0
        color = 'green' if comp.get("status") == "on-sales" else 'steelblue'

        ax.scatter(x, y, s=size, color=color, alpha=0.7,
                   edgecolors='black', linewidth=0.5, zorder=4)

        label = comp["name"]
        if price:
            label += f'\n${price:,.0f}/m²'
        ax.annotate(label, (x, y), textcoords='offset points',
                    xytext=(8, 8), fontsize=7, zorder=6)

    ax.set_xlim(-max_ring, max_ring)
    ax.set_ylim(-max_ring, max_ring)
    ax.set_aspect('equal')
    ax.set_title(f'Competitor Map — {site_name}', fontsize=13, fontweight='bold', pad=15)
    ax.axis('off')
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    data = buf.read()

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(data)

    return data
