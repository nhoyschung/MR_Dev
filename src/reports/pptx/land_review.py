"""PPTX generator: Land Review (12-slide template).

Slide structure:
  1.  Cover
  2.  Site Overview (KPI dashboard)
  3.  Section: Location Analysis
  4.  Location Details (table)
  5.  Market Analysis — Price Trends (table)
  6.  Market Analysis — Supply (table)
  7.  Competitor Overview (table)
  8.  Section: Strategic Assessment
  9.  SWOT Analysis
  10. Product Recommendations (table)
  11. Pricing Strategy (table)
  12. Conclusion & Verdict
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.land_review import _assemble_land_review_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    slides: list[dict] = []
    loc = ctx["location_analysis"]
    market = ctx["market_analysis"]
    swot = ctx["swot_analysis"]
    product = ctx["product_recommendations"]
    pricing = ctx["pricing_strategy"]
    competitors = ctx.get("competitors", [])

    # Slide 1: Cover
    slides.append({
        "index": 1, "type": "cover",
        "title": f"Land Development Review",
        "subtitle": f"{ctx['district']} · {ctx['city']} · {ctx['land_area_ha']} ha",
        "city": ctx["city"],
        "period": ctx["period"],
        "report_type": "Land Review",
        "date": ctx["generated_date"],
    })

    # Slide 2: KPI Dashboard
    kpis = [
        {"label": "Land Area", "value": f"{ctx['land_area_ha']} ha",
         "delta": f"{ctx['land_area_m2']:,.0f} m²", "color": "blue"},
        {"label": "Target Segment", "value": ctx["target_segment"],
         "delta": None, "color": "green"},
        {"label": "Development Type", "value": ctx["development_type"].title(),
         "delta": None, "color": "blue"},
        {"label": "Est. Total Units", "value": f"{product.get('estimated_total_units', 0):,}",
         "delta": f"{product.get('development_phases', 1)} phase(s)", "color": "amber"},
        {"label": "Nearby Competitors", "value": str(ctx["competitor_count"]),
         "delta": None, "color": "red" if ctx["competitor_count"] > 5 else "green"},
    ]
    if pricing.get("recommended_price_m2"):
        kpis.append({
            "label": "Recommended Price",
            "value": pricing["recommended_price_m2"],
            "delta": None, "color": "amber",
        })

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{ctx['district']} Site — Key Metrics",
        "kpis": kpis,
        "note": (
            f"A {ctx['land_area_ha']} ha parcel in {ctx['district']}, {ctx['city']}. "
            f"Target segment: {ctx['target_segment']} "
            f"({', '.join(ctx['target_grades'])}). "
            f"Development type: {ctx['development_type']}."
        ),
    })

    # Slide 3: Section divider — Location
    slides.append({
        "index": 3, "type": "section_divider",
        "number": "01",
        "title": "Location Analysis",
        "subtitle": f"{ctx['district']}, {ctx['city']}",
    })

    # Slide 4: Location details table
    infra = loc.get("infrastructure_score", {})
    reg = loc.get("regulatory_info")
    loc_rows = [
        ["City", ctx["city"]],
        ["District", ctx["district"]],
        ["Ward", ctx["ward"]],
        ["District Type", loc.get("district", "N/A")],
        ["Infrastructure Score", f"{infra.get('total_score', 'N/A')}/100" if infra else "N/A"],
        ["Infrastructure Grade", infra.get("grade", "N/A") if infra else "N/A"],
        ["Max Plot Ratio", str(reg.max_plot_ratio) if reg else "N/A"],
        ["Max Floors", str(reg.max_building_floors) if reg else "N/A"],
        ["Flood Zone", "Yes" if (reg and reg.flood_zone) else "No"],
    ]
    slides.append({
        "index": 4, "type": "table",
        "title": "Location & Regulatory Summary",
        "headers": ["Parameter", "Value"],
        "rows": loc_rows,
        "caption": (
            "  ·  ".join(loc.get("accessibility", []))[:200] or None
        ),
        "grade_col_index": None,
    })

    # Slide 5: Price Trends table
    price_rows = []
    for grade, data in market.get("price_trends", {}).items():
        price_rows.append([
            grade,
            f"${data.get('avg_price_m2', 0):,}",
            data.get("price_range", "N/A"),
        ])
    slides.append({
        "index": 5, "type": "table",
        "title": "Market Price Trends by Grade",
        "headers": ["Grade", "Avg Price (USD/m²)", "Price Range"],
        "rows": price_rows or [["No data", "—", "—"]],
        "caption": pricing.get("positioning"),
        "grade_col_index": 0,
    })

    # Slide 6: Supply table
    supply_rows = []
    for grade, data in market.get("supply_summary", {}).items():
        supply_rows.append([
            grade,
            f"{data.get('new_supply', 0):,}",
            f"{data.get('absorption_rate', 0):.1f}%",
        ])
    slides.append({
        "index": 6, "type": "table",
        "title": "Supply & Absorption by Grade",
        "headers": ["Grade", "New Supply (units)", "Absorption Rate"],
        "rows": supply_rows or [["No data", "—", "—"]],
        "caption": None,
        "grade_col_index": 0,
    })

    # Slide 7: Competitors
    comp_rows = [
        [
            c["name"],
            c.get("grade", "N/A"),
            f"{c.get('distance_km', 0):.1f} km",
            f"${c.get('price_m2', 0):,}" if c.get("price_m2") else "N/A",
            c.get("status", "N/A").title(),
        ]
        for c in competitors[:8]
    ]
    slides.append({
        "index": 7, "type": "table",
        "title": f"Nearby Competitors (within 5 km)",
        "headers": ["Project", "Grade", "Distance", "Price (USD/m²)", "Status"],
        "rows": comp_rows or [["No nearby competitors found", "—", "—", "—", "—"]],
        "caption": f"{ctx['competitor_count']} total competitor projects identified.",
        "grade_col_index": 1,
    })

    # Slide 8: Section divider — Strategic Assessment
    slides.append({
        "index": 8, "type": "section_divider",
        "number": "02",
        "title": "Strategic Assessment",
        "subtitle": "SWOT · Product Mix · Pricing",
    })

    # Slide 9: SWOT
    slides.append({
        "index": 9, "type": "swot",
        "title": "SWOT Analysis",
        "strengths": swot.get("strengths", [])[:4],
        "weaknesses": swot.get("weaknesses", [])[:4],
        "opportunities": swot.get("opportunities", [])[:4],
        "threats": swot.get("threats", [])[:4],
    })

    # Slide 10: Product recommendations
    mix = product.get("unit_mix", {})
    mix_rows = [[unit, f"{pct}%"] for unit, pct in mix.items()]
    mix_rows.append(["TOTAL ESTIMATED UNITS", f"{product.get('estimated_total_units', 0):,}"])
    slides.append({
        "index": 10, "type": "table",
        "title": "Recommended Product Mix",
        "headers": ["Unit Type", "Mix %"],
        "rows": mix_rows,
        "caption": (
            f"Development in {product.get('development_phases', 1)} phase(s). "
            f"Grades: {', '.join(product.get('recommended_grades', []))}"
        ),
        "grade_col_index": None,
    })

    # Slide 11: Pricing strategy
    pricing_rows = [
        ["Market Average", pricing.get("market_average_m2", "N/A")],
        ["Recommended Price", pricing.get("recommended_price_m2", "N/A")],
        ["Positioning", pricing.get("positioning", "N/A")],
        ["Target Grades", ", ".join(pricing.get("target_grades", []))],
    ]
    slides.append({
        "index": 11, "type": "table",
        "title": "Pricing Strategy",
        "headers": ["Parameter", "Recommendation"],
        "rows": pricing_rows,
        "caption": None,
        "grade_col_index": None,
    })

    # Slide 12: Conclusion
    strengths_count = len(swot.get("strengths", []))
    weaknesses_count = len(swot.get("weaknesses", []))
    avg_absorption = sum(
        d.get("absorption_rate", 0) for d in market.get("supply_summary", {}).values()
    ) / max(len(market.get("supply_summary", {})), 1)

    if strengths_count > weaknesses_count and avg_absorption > 60:
        verdict, badge_color = "HIGHLY VIABLE", "green"
    elif strengths_count >= weaknesses_count:
        verdict, badge_color = "MODERATELY VIABLE", "amber"
    else:
        verdict, badge_color = "REQUIRES STUDY", "red"

    bullets = [
        f"Site: {ctx['land_area_ha']} ha in {ctx['district']}, {ctx['city']}",
        f"Target: {ctx['target_segment']} segment "
        f"({', '.join(ctx['target_grades'][:3])})",
        f"Est. {product.get('estimated_total_units', 0):,} units, "
        f"{product.get('development_phases', 1)} phase(s)",
        f"Recommended price: {pricing.get('recommended_price_m2', 'N/A')}",
    ]
    if competitors:
        bullets.append(f"{ctx['competitor_count']} competitors within 5 km radius")

    slides.append({
        "index": 12, "type": "conclusion",
        "title": "Development Verdict",
        "verdict": verdict,
        "bullets": bullets,
        "badge_label": verdict,
        "badge_color": badge_color,
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "land_review",
        "language": language,
        "params": {
            "city": ctx["city"],
            "district": ctx.get("district"),
            "land_area_ha": ctx["land_area_ha"],
        },
        "slides": slides,
    }


def generate_land_review_pptx(
    session: Session,
    land_input: dict,
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate a 12-slide land review PPTX.

    Args:
        session: Database session.
        land_input: Dict with 'city', 'land_area_ha', optional 'district' etc.
        content_override: Pre-built manifest (from AI content writer or translator).
        language: "en" or "ko".

    Returns:
        Path to saved .pptx file. Raises ValueError if city not found.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        ctx = _assemble_land_review_context(session, land_input, include_map=False)
        manifest = _build_default_manifest(ctx, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    city_slug = land_input.get("city", "unknown").lower().replace(" ", "_")
    district_slug = land_input.get("district", "site").lower().replace(" ", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"land_review_{city_slug}_{district_slug}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
