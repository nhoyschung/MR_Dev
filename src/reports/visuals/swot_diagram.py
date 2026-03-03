"""2x2 SWOT matrix diagram (matplotlib-based PNG)."""

from io import BytesIO

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def generate_swot_diagram(
    strengths: list[str],
    weaknesses: list[str],
    opportunities: list[str],
    threats: list[str],
    output_path: str | None = None,
) -> bytes:
    """Generate a 2x2 SWOT matrix diagram.

    Returns PNG bytes.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('SWOT Analysis', fontsize=16, fontweight='bold', y=0.98)

    quadrants = [
        (axes[0, 0], "Strengths", strengths, '#27AE60'),
        (axes[0, 1], "Weaknesses", weaknesses, '#E74C3C'),
        (axes[1, 0], "Opportunities", opportunities, '#3498DB'),
        (axes[1, 1], "Threats", threats, '#E8A820'),
    ]

    for ax, title, items, color in quadrants:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Background
        rect = mpatches.FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.96,
            boxstyle="round,pad=0.02",
            facecolor=color, alpha=0.15, edgecolor=color, linewidth=2,
        )
        ax.add_patch(rect)

        # Title
        ax.text(0.5, 0.92, title, ha='center', va='top',
                fontsize=14, fontweight='bold', color=color)

        # Items
        text = '\n'.join(f'• {item[:60]}' for item in items[:6])
        ax.text(0.08, 0.82, text, ha='left', va='top',
                fontsize=9, wrap=True, linespacing=1.5)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    data = buf.read()

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(data)

    return data
