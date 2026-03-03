"""PPTX generator: Project Profile (5-slide template).

Slide structure:
  1. Cover
  2. Project Overview (KPI dashboard)
  3. Price History (chart or table)
  4. Competitive Context (table)
  5. Developer Portfolio & Conclusion
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.project_profile import _assemble_profile_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    proj = ctx["project"]
    slides: list[dict] = []

    # Slide 1: Cover
    slides.append({
        "index": 1, "type": "cover",
        "title": proj["name"],
        "subtitle": f"{proj['developer_name'] or 'Unknown Developer'} · {proj['city_name']}",
        "city": proj["city_name"],
        "period": ctx["generated_date"],
        "report_type": "Project Profile",
        "date": ctx["generated_date"],
    })

    # Slide 2: KPI Dashboard
    kpis = [
        {"label": "Grade", "value": proj.get("grade_primary") or "N/A",
         "delta": proj.get("grade_position"), "color": "blue"},
        {"label": "Status", "value": (proj.get("status") or "N/A").title(),
         "delta": None, "color": "green"},
        {"label": "Total Units", "value": f"{proj.get('total_units') or 0:,}",
         "delta": None, "color": "blue"},
    ]
    if proj.get("price_usd"):
        kpis.append({
            "label": "Price (USD/m²)", "value": f"${proj['price_usd']}",
            "delta": None, "color": "amber",
        })
    if proj.get("segment"):
        kpis.append({
            "label": "Segment", "value": proj["segment"],
            "delta": None, "color": "blue",
        })

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{proj['name']} — Key Facts",
        "kpis": kpis,
        "note": (
            f"{proj['name']} is a {proj.get('project_type', 'residential')} project "
            f"in {proj['district_name']}, {proj['city_name']}. "
            f"Grade {proj.get('grade_primary', 'N/A')} places it in the "
            f"{proj.get('segment', 'N/A')} segment."
        ),
    })

    # Slide 3: Price History
    history = ctx.get("price_history", [])
    if history:
        slides.append({
            "index": 3, "type": "chart",
            "title": "Price History",
            "chart_type": "price_trend",
            "chart_params": {"trend_data": history},
            "caption": "Historical price per m² (USD) by reporting period.",
            "right_panel_text": None,
        })
    else:
        slides.append({
            "index": 3, "type": "table",
            "title": "Price Information",
            "headers": ["Metric", "Value"],
            "rows": [
                ["Current Price (USD/m²)", f"${proj['price_usd']}" if proj.get("price_usd") else "N/A"],
                ["Current Price (VND/m²)", f"{proj['price_vnd']}" if proj.get("price_vnd") else "N/A"],
                ["Grade Band Min", f"${proj['grade_min']}" if proj.get("grade_min") else "N/A"],
                ["Grade Band Max", f"${proj['grade_max']}" if proj.get("grade_max") else "N/A"],
                ["Position in Grade", proj.get("grade_position") or "N/A"],
            ],
            "caption": "Price positioning within grade band.",
            "grade_col_index": None,
        })

    # Slide 4: District Peers
    peers = ctx.get("district_projects", [])[:8]
    slides.append({
        "index": 4, "type": "table",
        "title": f"District Peers — {proj['district_name']}",
        "headers": ["Project", "Grade", "Price (USD/m²)"],
        "rows": [[p["name"], p.get("grade") or "N/A", f"${p['price']}" if p.get("price") else "N/A"]
                 for p in peers],
        "caption": (
            f"District average: ${ctx['district_avg_price']}/m²" if ctx.get("district_avg_price") else None
        ),
        "grade_col_index": 1,
    })

    # Slide 5: Developer + Conclusion
    dev_projects = ctx.get("developer_projects", [])[:5]
    bullet_items = [f"{p['name']} ({p.get('district', 'N/A')}) — Grade {p.get('grade', 'N/A')}"
                    for p in dev_projects]
    if not bullet_items:
        bullet_items = ["No other projects by this developer in database."]

    slides.append({
        "index": 5, "type": "conclusion",
        "title": "Developer Portfolio & Summary",
        "verdict": f"GRADE {proj.get('grade_primary', 'N/A')}",
        "bullets": bullet_items,
        "badge_label": proj.get("grade_primary") or "N/A",
        "badge_color": "green" if proj.get("grade_primary") in ("SL", "L", "H-I") else "blue",
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "project_profile",
        "language": language,
        "params": {"project_name": proj["name"]},
        "slides": slides,
    }


def generate_project_profile_pptx(
    session: Session,
    project_name: str,
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate a 5-slide project profile PPTX.

    Returns None if project not found in database.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        ctx = _assemble_profile_context(session, project_name)
        if ctx is None:
            return None
        manifest = _build_default_manifest(ctx, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    slug = project_name.lower().replace(" ", "_")[:30]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"project_profile_{slug}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
