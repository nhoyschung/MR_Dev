"""PPTX generator: Compact Land Review (8-slide template).

Slide structure:
  1.  Cover
  2.  KPI Dashboard (area, units, grade, rental yield, CBD distance, road info)
  3.  PD Suggestion Table (2-col key metrics + pd_suggestion text)
  4.  SWOT Analysis
  5.  Competitor Table (name, developer, price, units, sold%, absorption note)
  6.  Chart: Competitor Unit Mix
  7.  Chart: Absorption Timeline
  8.  Conclusion (verdict based on pd_suggestion tone + competitor intensity)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.compact_land_review import _assemble_compact_review_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    """Build an 8-slide manifest from _assemble_compact_review_context() output."""
    slides: list[dict] = []
    competitors = ctx.get("competitors", [])
    price_targets = ctx.get("price_targets", [])
    swot = ctx.get("swot", {})
    target_customers = ctx.get("target_customers", [])

    # ── Slide 1: Cover ──────────────────────────────────────────────────────
    slides.append({
        "index": 1, "type": "cover",
        "title": "Compact Land Review",
        "subtitle": (
            f"{ctx.get('site_name', 'Site')} · "
            f"Grade {ctx.get('recommended_grade', 'N/A')} · "
            f"{ctx.get('land_area_ha', 0)} ha"
        ),
        "city": ctx.get("city", ""),
        "period": ctx.get("district", ""),
        "report_type": "Compact Land Review",
        "date": ctx.get("generated_date", ""),
    })

    # ── Slide 2: KPI Dashboard ──────────────────────────────────────────────
    kpis = [
        {"label": "Land Area", "value": f"{ctx.get('land_area_ha', 0)} ha",
         "delta": None, "color": "blue"},
        {"label": "Total Units Target",
         "value": f"{ctx.get('total_units_target', 0):,}",
         "delta": None, "color": "green"},
        {"label": "Recommended Grade",
         "value": ctx.get("recommended_grade", "N/A"),
         "delta": None, "color": "amber"},
        {"label": "Rental Yield",
         "value": f"{ctx.get('rental_yield_pct', 0):.1f}%",
         "delta": None, "color": "green"},
        {"label": "CBD Distance",
         "value": f"{ctx.get('distance_to_cbd_km', 0):.1f} km",
         "delta": None, "color": "blue"},
    ]

    main_road = ctx.get("main_road_name", "")
    main_road_w = ctx.get("main_road_width_m", 0)
    secondary_road = ctx.get("secondary_road_name", "")
    if main_road:
        kpis.append({
            "label": "Main Road",
            "value": main_road[:20],
            "delta": f"{main_road_w}m wide" if main_road_w else None,
            "color": "blue",
        })

    note_parts = [
        f"{ctx.get('site_name', 'Site')}: {ctx.get('land_area_ha', 0)} ha "
        f"in {ctx.get('district', '')}, {ctx.get('city', '')}.",
        f"Development type: {ctx.get('development_type', 'N/A')}.",
        f"Target units: {ctx.get('total_units_target', 0):,}.",
    ]
    if secondary_road:
        note_parts.append(f"Secondary road: {secondary_road}.")

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{ctx.get('site_name', 'Site')} — Key Metrics",
        "kpis": kpis,
        "note": " ".join(note_parts),
    })

    # ── Slide 3: PD Suggestion Table ────────────────────────────────────────
    pd_rows = [
        ["Site Name", ctx.get("site_name", "N/A")],
        ["City / District", f"{ctx.get('city', '')} / {ctx.get('district', '')}"],
        ["Land Area", f"{ctx.get('land_area_ha', 0)} ha"],
        ["Development Type", ctx.get("development_type", "N/A")],
        ["Recommended Grade", ctx.get("recommended_grade", "N/A")],
        ["Total Units Target", f"{ctx.get('total_units_target', 0):,}"],
        ["Rental Yield", f"{ctx.get('rental_yield_pct', 0):.1f}%"],
        ["CBD Distance", f"{ctx.get('distance_to_cbd_km', 0):.1f} km"],
    ]

    # Add price targets
    for pt in price_targets[:3]:
        pd_rows.append([
            f"{pt.get('product_type', 'N/A')} Price",
            f"${pt.get('price_usd_m2', 0):,}/m² · "
            f"{pt.get('unit_count', 0)} units · "
            f"{pt.get('unit_size_m2', 0)} m²",
        ])

    pd_suggestion = ctx.get("pd_suggestion", "")
    caption = pd_suggestion[:300] if pd_suggestion else None

    slides.append({
        "index": 3, "type": "table",
        "title": "PD Review — Key Metrics & Suggestion",
        "headers": ["Parameter", "Value"],
        "rows": pd_rows,
        "caption": caption,
        "grade_col_index": None,
    })

    # ── Slide 4: SWOT Analysis ──────────────────────────────────────────────
    slides.append({
        "index": 4, "type": "swot",
        "title": "SWOT Analysis",
        "strengths": swot.get("S", [])[:4],
        "weaknesses": swot.get("W", [])[:4],
        "opportunities": swot.get("O", [])[:4],
        "threats": swot.get("T", [])[:4],
    })

    # ── Slide 5: Competitor Table ───────────────────────────────────────────
    comp_headers = [
        "Project", "Developer", "Price (USD/m²)",
        "Units", "Sold %", "Absorption Note",
    ]
    comp_rows = []
    for c in competitors[:7]:
        comp_rows.append([
            str(c.get("project_name", c.get("name", "N/A")))[:25],
            str(c.get("developer", "N/A"))[:20],
            f"${c.get('apt_price_usd_m2', 0):,}" if c.get("apt_price_usd_m2") else "N/A",
            str(c.get("total_units", "N/A")),
            f"{c.get('sold_pct', 0):.0f}%" if c.get("sold_pct") is not None else "N/A",
            str(c.get("absorption_note", ""))[:30],
        ])

    slides.append({
        "index": 5, "type": "table",
        "title": "Competitor Overview (Top 7)",
        "headers": comp_headers,
        "rows": comp_rows or [["No competitors found", "—", "—", "—", "—", "—"]],
        "caption": f"{len(competitors)} total competitors identified.",
        "grade_col_index": None,
    })

    # ── Slide 6: Chart — Competitor Unit Mix ────────────────────────────────
    unit_mix_data = []
    for c in competitors[:7]:
        mix = c.get("unit_mix", {})
        if mix:
            unit_mix_data.append({
                "name": c.get("project_name", c.get("name", "N/A")),
                "studio_pct": mix.get("studio_pct", 0),
                "br1_1wc_pct": mix.get("br1_1wc_pct", 0),
                "br2_pct": mix.get("br2_pct", 0),
                "br3_pct": mix.get("br3_pct", 0),
            })

    slides.append({
        "index": 6, "type": "chart",
        "title": "Competitor Unit Mix Comparison",
        "chart_type": "competitor_unit_mix",
        "chart_params": {"competitors_data": unit_mix_data},
        "caption": "Unit mix breakdown by bedroom type across nearby competitors.",
        "right_panel_text": None,
    })

    # ── Slide 7: Chart — Absorption Timeline ───────────────────────────────
    absorption_data = []
    for c in competitors[:7]:
        if c.get("sold_pct") is not None:
            absorption_data.append({
                "name": c.get("project_name", c.get("name", "N/A")),
                "sold_pct": c.get("sold_pct", 0),
                "absorption_note": c.get("absorption_note", ""),
            })

    slides.append({
        "index": 7, "type": "chart",
        "title": "Competitor Absorption Timeline",
        "chart_type": "absorption_timeline",
        "chart_params": {"absorption_data": absorption_data},
        "caption": "Sales absorption progress across competitor projects.",
        "right_panel_text": None,
    })

    # ── Slide 8: Conclusion ─────────────────────────────────────────────────
    pd_text = (pd_suggestion or "").lower()
    competitor_count = len(competitors)

    if "recommend" in pd_text or "viable" in pd_text or "favorable" in pd_text:
        verdict, badge_color = "RECOMMENDED", "green"
    elif "caution" in pd_text or "risk" in pd_text or competitor_count > 5:
        verdict, badge_color = "PROCEED WITH CAUTION", "amber"
    else:
        verdict, badge_color = "UNDER REVIEW", "red"

    bullets = [
        f"Site: {ctx.get('site_name', 'N/A')} — "
        f"{ctx.get('land_area_ha', 0)} ha in {ctx.get('district', '')}, {ctx.get('city', '')}",
        f"Target: {ctx.get('total_units_target', 0):,} units, "
        f"Grade {ctx.get('recommended_grade', 'N/A')}",
        f"Rental yield: {ctx.get('rental_yield_pct', 0):.1f}%, "
        f"CBD distance: {ctx.get('distance_to_cbd_km', 0):.1f} km",
        f"{competitor_count} competitors identified in the area",
    ]

    if target_customers:
        top_seg = target_customers[0]
        bullets.append(
            f"Primary target: {top_seg.get('segment_name', 'N/A')} "
            f"({top_seg.get('ratio_pct', 0)}%)"
        )

    slides.append({
        "index": 8, "type": "conclusion",
        "title": "Development Verdict",
        "verdict": verdict,
        "bullets": bullets[:5],
        "badge_label": verdict,
        "badge_color": badge_color,
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "compact_land_review",
        "language": language,
        "params": {
            "site_name": ctx.get("site_name"),
            "land_site_id": ctx.get("land_site_id"),
        },
        "slides": slides,
    }


def generate_compact_land_review_pptx(
    session: Session,
    land_site_id: int,
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate an 8-slide compact land review PPTX.

    Args:
        session: Database session.
        land_site_id: ID of the land site to review.
        content_override: Pre-built manifest (from AI content writer or translator).
        language: "en" or "ko".

    Returns:
        Path to saved .pptx file, or None if data unavailable.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        ctx = _assemble_compact_review_context(session, land_site_id)
        if ctx is None:
            return None
        manifest = _build_default_manifest(ctx, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    params = manifest.get("params", {})
    site_slug = (
        params.get("site_name") or str(land_site_id)
    ).lower().replace(" ", "_")[:30]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"compact_land_review_{site_slug}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
