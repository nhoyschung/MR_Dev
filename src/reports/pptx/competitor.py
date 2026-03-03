"""PPTX generator: Competitor Benchmark (5-slide template).

Slide structure:
  1. Cover
  2. Competitor Scorecard (table)
  3. Radar Chart (11-dimension)
  4. Dimension Winners (table)
  5. Conclusion — Overall Winner
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.competitor_benchmark import _build_competitor_data, DIMENSIONS
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(data: dict, language: str) -> SlideContentManifest:
    slides: list[dict] = []
    projects = data["projects"]
    overall_winner = data["overall_winner"]
    best_value = data["best_value"]

    # Slide 1: Cover
    names_str = " vs ".join(p["name"] for p in projects[:3])
    slides.append({
        "index": 1, "type": "cover",
        "title": "Competitive Benchmark Analysis",
        "subtitle": names_str,
        "city": projects[0]["city"] if projects else "",
        "period": data["period"],
        "report_type": "Competitor Benchmark",
        "date": data["generated_date"],
    })

    # Slide 2: Competitor Scorecard
    score_headers = ["Project", "Grade", "Price (USD/m²)", "Total Score", "Value Index"]
    score_rows = [
        [
            p["name"],
            p["grade"],
            f"${p['price_usd']:,.0f}" if p["price_usd"] else "N/A",
            f"{p['total_score']:.1f}",
            f"{p['value_index']:.2f}",
        ]
        for p in projects
    ]
    slides.append({
        "index": 2, "type": "table",
        "title": "Competitor Scorecard",
        "headers": score_headers,
        "rows": score_rows,
        "caption": f"Overall winner: {overall_winner}  ·  Best value: {best_value}",
        "grade_col_index": 1,
    })

    # Slide 3: Radar Chart
    slides.append({
        "index": 3, "type": "chart",
        "title": "11-Dimension Competitive Radar",
        "chart_type": "radar",
        "chart_params": {
            "projects_scores": data.get("projects_scores", []),
            "categories": DIMENSIONS,
        },
        "caption": "Scores 1–10 across 11 standard NHO-PD evaluation dimensions.",
        "right_panel_text": None,
    })

    # Slide 4: Dimension Winners
    dim_headers = ["Dimension", "Winner", "Score"]
    dim_rows = []
    for dim in DIMENSIONS:
        winner_name = data["dimension_winners"].get(dim, "N/A")
        winner_proj = next((p for p in projects if p["name"] == winner_name), None)
        score = winner_proj["scores"].get(dim, 0) if winner_proj else 0
        dim_rows.append([dim, winner_name, f"{score:.1f}"])

    slides.append({
        "index": 4, "type": "table",
        "title": "Dimension-by-Dimension Winners",
        "headers": dim_headers,
        "rows": dim_rows,
        "caption": None,
        "grade_col_index": None,
    })

    # Slide 5: Conclusion
    winner_proj = next((p for p in projects if p["name"] == overall_winner), projects[0])
    bullets = [
        f"Overall winner: {overall_winner} (score {winner_proj['total_score']:.1f}/110)",
        f"Best value for money: {best_value}",
        f"{len(projects)} projects evaluated across {len(DIMENSIONS)} dimensions",
    ]
    # Add top strengths
    top_dims = sorted(data["dimension_winners"].items(),
                      key=lambda x: next((p["scores"].get(x[0], 0) for p in projects
                                          if p["name"] == x[1]), 0), reverse=True)[:3]
    for dim, winner in top_dims:
        bullets.append(f"Strongest {dim}: {winner}")

    slides.append({
        "index": 5, "type": "conclusion",
        "title": "Overall Verdict",
        "verdict": f"WINNER: {overall_winner}",
        "bullets": bullets,
        "badge_label": overall_winner[:20],
        "badge_color": "green",
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "competitor",
        "language": language,
        "params": {
            "projects": [p["name"] for p in projects],
            "year": data.get("year"),
            "half": data.get("half"),
        },
        "slides": slides,
    }


def generate_competitor_pptx(
    session: Session,
    project_names: list[str],
    year: int = 2024,
    half: str = "H1",
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate a 5-slide competitor benchmark PPTX.

    Returns None if fewer than 2 projects found.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        data = _build_competitor_data(session, project_names, year, half)
        if data is None:
            return None
        manifest = _build_default_manifest(data, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    slug = "_vs_".join(n.lower().replace(" ", "_")[:10] for n in project_names[:3])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"competitor_{slug}_{year}_{half}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
