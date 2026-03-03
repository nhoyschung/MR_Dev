"""Site analysis diagram: directional views, roads, constraints (matplotlib PNG)."""

from io import BytesIO

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# Direction → (dx, dy) offsets for arrows
_DIR_VECTORS = {
    "N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0),
    "NE": (0.7, 0.7), "NW": (-0.7, 0.7), "SE": (0.7, -0.7), "SW": (-0.7, -0.7),
}


def generate_site_analysis_diagram(
    site_name: str,
    views: list[dict],
    roads: list[dict] | None = None,
    output_path: str | None = None,
) -> bytes:
    """Site analysis diagram with directional views and roads.

    Args:
        site_name: Name of the subject site.
        views: List with 'direction', 'view_type' (positive/negative), 'view_target'.
        roads: Optional list with 'name', 'width_m', 'direction'.
        output_path: If set, save PNG to path.

    Returns PNG bytes.
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    # Central site box
    site_rect = mpatches.FancyBboxPatch(
        (-1, -1), 2, 2,
        boxstyle="round,pad=0.1",
        facecolor='#F0F0F0', edgecolor='black', linewidth=2,
    )
    ax.add_patch(site_rect)
    ax.text(0, 0, site_name, ha='center', va='center',
            fontsize=12, fontweight='bold')

    # Directional views
    for view in views:
        direction = view.get("direction", "N")
        view_type = view.get("view_type", "neutral")
        target = view.get("view_target", "")

        dx, dy = _DIR_VECTORS.get(direction, (0, 1))
        color = 'green' if view_type == "positive" else (
            'red' if view_type == "negative" else 'gray'
        )

        # Arrow from site edge
        start_x, start_y = dx * 1.2, dy * 1.2
        end_x, end_y = dx * 3.0, dy * 3.0

        ax.annotate(
            '', xy=(end_x, end_y), xytext=(start_x, start_y),
            arrowprops=dict(arrowstyle='->', color=color, lw=2.5),
        )

        # Label
        label_x, label_y = dx * 3.5, dy * 3.5
        label = f'{direction}: {target}'
        symbol = '+' if view_type == 'positive' else '-' if view_type == 'negative' else '~'
        ax.text(label_x, label_y, f'[{symbol}] {label}',
                ha='center', va='center', fontsize=8, color=color,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=color, alpha=0.8))

    # Roads
    if roads:
        for i, road in enumerate(roads):
            direction = road.get("direction", "S")
            dx, dy = _DIR_VECTORS.get(direction, (0, -1))
            rx, ry = dx * 1.5, dy * 1.5
            ax.text(rx, ry, f'🛣 {road["name"]} ({road.get("width_m", "?")}m)',
                    ha='center', va='center', fontsize=8, color='#555',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFCC', alpha=0.8))

    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect('equal')
    ax.set_title(f'Site Analysis — {site_name}', fontsize=14, fontweight='bold', pad=15)
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
