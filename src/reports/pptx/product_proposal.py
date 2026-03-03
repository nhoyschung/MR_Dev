"""PPTX generator: Product Development Proposal (11-slide template, HP 35ha style).

Slide structure:
  1.  Cover — "Product Development Proposal"
  2.  KPI Dashboard — total units (high-rise/low-rise split), zones count, concept
  3.  Section Divider — "01 Zone & Product Strategy"
  4.  Zone Breakdown Table — zones with area, units, anchors, benchmark projects
  5.  FS Planning Table — product types, prices, units, launch timing
  6.  Chart: Zone Product Mix — chart_type="zone_product_mix"
  7.  Section Divider — "02 Market & Strategy"
  8.  SWOT Analysis
  9.  Development Directions Table — 3 directions with concepts and amenities
  10. Chart: Phase Price Progression (or competitor distance band fallback)
  11. Conclusion — verdict based on development concept viability
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.product_proposal import _assemble_proposal_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    """Build a data-rich manifest from _assemble_proposal_context() output."""
    slides: list[dict] = []

    zones = ctx.get("zones", [])
    price_targets = ctx.get("price_targets", [])
    swot = ctx.get("swot", {})
    directions = ctx.get("development_directions", [])
    case_studies = ctx.get("case_studies", [])
    competitors_by_band = ctx.get("competitors_by_band", {})
    target_customers = ctx.get("target_customers", [])

    total_highrise = ctx.get("total_highrise_units", 0)
    total_lowrise = ctx.get("total_lowrise_units", 0)
    total_units = ctx.get("total_units_target", 0)

    # ── Slide 1: Cover ─────────────────────────────────────────────────────
    slides.append({
        "index": 1, "type": "cover",
        "title": "Product Development Proposal",
        "subtitle": (
            f"{ctx.get('development_concept', '')} · "
            f"{ctx.get('land_area_ha', 0)} ha · {ctx.get('site_name', '')}"
        ),
        "city": ctx.get("city", ""),
        "period": ctx.get("district", ""),
        "report_type": "Product Proposal",
        "date": ctx.get("generated_date", ""),
    })

    # ── Slide 2: KPI Dashboard ─────────────────────────────────────────────
    kpis = [
        {"label": "Total Units Target", "value": f"{total_units:,}",
         "delta": f"High-rise {total_highrise:,} · Low-rise {total_lowrise:,}",
         "color": "blue"},
        {"label": "Land Area", "value": f"{ctx.get('land_area_ha', 0)} ha",
         "delta": None, "color": "green"},
        {"label": "Zones", "value": str(len(zones)),
         "delta": f"{len([z for z in zones if z.get('key_anchor')])} with anchors",
         "color": "blue"},
        {"label": "Development Type",
         "value": ctx.get("development_type", "Mixed-use").title(),
         "delta": None, "color": "amber"},
        {"label": "Product Types", "value": str(len(price_targets)),
         "delta": None, "color": "blue"},
    ]
    if target_customers:
        kpis.append({
            "label": "Target Segments",
            "value": str(len(target_customers)),
            "delta": None, "color": "green",
        })

    note = (
        f"{ctx.get('site_name', '')} is a {ctx.get('land_area_ha', 0)} ha "
        f"{ctx.get('development_type', 'mixed-use')} development in "
        f"{ctx.get('district', '')}, {ctx.get('city', '')}. "
        f"Concept: {ctx.get('development_concept', 'N/A')}. "
        f"Planned across {len(zones)} zones with {total_units:,} total units "
        f"({total_highrise:,} high-rise, {total_lowrise:,} low-rise)."
    )

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{ctx.get('site_name', 'Site')} — Development Overview",
        "kpis": kpis,
        "note": note,
    })

    # ── Slide 3: Section Divider — Zone & Product Strategy ─────────────────
    slides.append({
        "index": 3, "type": "section_divider",
        "number": "01",
        "title": "Zone & Product Strategy",
        "subtitle": f"{len(zones)} zones · {total_units:,} units planned",
    })

    # ── Slide 4: Zone Breakdown Table ──────────────────────────────────────
    zone_headers = [
        "Zone", "Area (ha)", "High-rise", "Low-rise",
        "Key Anchor", "Benchmark",
    ]
    zone_rows = []
    for z in zones:
        zone_rows.append([
            z.get("zone_code", ""),
            f"{z.get('area_ha', 0):.1f}",
            f"{z.get('highrise_units_planned', 0):,}",
            f"{z.get('lowrise_units_planned', 0):,}",
            z.get("key_anchor", "—") or "—",
            z.get("benchmark_project", "—") or "—",
        ])
    # Total row
    total_area = sum(z.get("area_ha", 0) for z in zones)
    zone_rows.append([
        "TOTAL",
        f"{total_area:.1f}",
        f"{total_highrise:,}",
        f"{total_lowrise:,}",
        "—", "—",
    ])

    strengths_summary = []
    weaknesses_summary = []
    for z in zones[:3]:
        if z.get("strengths"):
            strengths_summary.append(f"{z['zone_code']}: {z['strengths'][:60]}")
        if z.get("weaknesses"):
            weaknesses_summary.append(f"{z['zone_code']}: {z['weaknesses'][:60]}")

    zone_caption_parts = []
    if strengths_summary:
        zone_caption_parts.append("Strengths — " + "; ".join(strengths_summary))
    if weaknesses_summary:
        zone_caption_parts.append("Risks — " + "; ".join(weaknesses_summary))
    zone_caption = ". ".join(zone_caption_parts)[:250] or None

    slides.append({
        "index": 4, "type": "table",
        "title": "Zone Breakdown & Anchor Strategy",
        "headers": zone_headers,
        "rows": zone_rows if zone_rows else [["No zones defined", "—", "—", "—", "—", "—"]],
        "caption": zone_caption,
        "grade_col_index": None,
    })

    # ── Slide 5: FS Planning Table ─────────────────────────────────────────
    fs_headers = [
        "Product Type", "Price (USD/m\u00b2)", "Units",
        "Unit Size (m\u00b2)", "Total Price (VND bil)", "Launch",
    ]
    fs_rows = []
    for pt in price_targets:
        fs_rows.append([
            pt.get("product_type", ""),
            f"${pt.get('price_usd_m2', 0):,.0f}",
            f"{pt.get('unit_count', 0):,}",
            f"{pt.get('unit_size_m2', 0):.0f}",
            f"{pt.get('total_price_vnd_bil', 0):,.1f}",
            pt.get("launch", "—") or "—",
        ])

    slides.append({
        "index": 5, "type": "table",
        "title": "Feasibility Study — Product & Pricing Plan",
        "headers": fs_headers,
        "rows": fs_rows if fs_rows else [["No products defined", "—", "—", "—", "—", "—"]],
        "caption": (
            f"{len(price_targets)} product types planned for "
            f"{total_units:,} total units."
        ),
        "grade_col_index": None,
    })

    # ── Slide 6: Chart — Zone Product Mix ──────────────────────────────────
    zones_chart_data = [
        {
            "zone_code": z.get("zone_code", ""),
            "highrise_units": z.get("highrise_units_planned", 0),
            "lowrise_units": z.get("lowrise_units_planned", 0),
        }
        for z in zones
    ]

    slides.append({
        "index": 6, "type": "chart",
        "title": "Zone Product Mix — High-rise vs Low-rise",
        "chart_type": "zone_product_mix",
        "chart_params": {"zones_data": zones_chart_data},
        "caption": (
            f"{len(zones)} zones, {total_highrise:,} high-rise units, "
            f"{total_lowrise:,} low-rise units."
        ),
        "right_panel_text": None,
    })

    # ── Slide 7: Section Divider — Market & Strategy ───────────────────────
    slides.append({
        "index": 7, "type": "section_divider",
        "number": "02",
        "title": "Market & Strategy",
        "subtitle": "SWOT · Development Directions · Benchmarks",
    })

    # ── Slide 8: SWOT Analysis ─────────────────────────────────────────────
    slides.append({
        "index": 8, "type": "swot",
        "title": "SWOT Analysis",
        "strengths": swot.get("S", swot.get("strengths", []))[:4],
        "weaknesses": swot.get("W", swot.get("weaknesses", []))[:4],
        "opportunities": swot.get("O", swot.get("opportunities", []))[:4],
        "threats": swot.get("T", swot.get("threats", []))[:4],
    })

    # ── Slide 9: Development Directions Table ──────────────────────────────
    dir_headers = [
        "Direction", "Concept", "Standard Amenities",
        "Premium Amenities", "Driving Amenities",
    ]
    dir_rows = []
    for d in directions[:3]:
        dir_rows.append([
            f"D{d.get('direction_number', '')} — {d.get('direction_name', '')}",
            d.get("concept_keywords", "—") or "—",
            d.get("standard_amenities", "—") or "—",
            d.get("premium_amenities", "—") or "—",
            d.get("driving_amenities", "—") or "—",
        ])

    slides.append({
        "index": 9, "type": "table",
        "title": "Development Directions & Amenity Strategy",
        "headers": dir_headers,
        "rows": dir_rows if dir_rows else [["No directions defined", "—", "—", "—", "—"]],
        "caption": (
            f"{len(directions)} development direction(s) evaluated."
        ),
        "grade_col_index": None,
    })

    # ── Slide 10: Chart — Phase Price Progression or Competitor Band ───────
    # Use phase_price_progression if case studies have phase data;
    # otherwise fall back to competitor_distance_band.
    has_phase_data = any(cs.get("total_units") for cs in case_studies)

    if has_phase_data and case_studies:
        phases_data = [
            {
                "project_name": cs.get("project_name", ""),
                "total_units": cs.get("total_units", 0),
                "land_area_ha": cs.get("land_area_ha", 0),
                "concept": cs.get("positioning_concept", ""),
            }
            for cs in case_studies
        ]
        slides.append({
            "index": 10, "type": "chart",
            "title": "Case Study Benchmarks — Phase Progression",
            "chart_type": "phase_price_progression",
            "chart_params": {"phases_data": phases_data},
            "caption": (
                f"{len(case_studies)} case study project(s) benchmarked."
            ),
            "right_panel_text": None,
        })
    else:
        # Fallback: competitor distance band chart
        comp_chart_data = []
        for band, comps in competitors_by_band.items():
            for c in comps:
                comp_chart_data.append({
                    "name": c.get("name", c.get("project_name", "")),
                    "distance_band": band,
                    **{k: v for k, v in c.items() if k not in ("name", "project_name")},
                })
        slides.append({
            "index": 10, "type": "chart",
            "title": "Competitor Landscape by Distance Band",
            "chart_type": "competitor_distance_band",
            "chart_params": {"competitors_data": comp_chart_data},
            "caption": (
                f"{len(comp_chart_data)} competitor(s) across "
                f"{len(competitors_by_band)} distance band(s)."
            ),
            "right_panel_text": None,
        })

    # ── Slide 11: Conclusion ───────────────────────────────────────────────
    strengths_count = len(swot.get("S", swot.get("strengths", [])))
    weaknesses_count = len(swot.get("W", swot.get("weaknesses", [])))

    if strengths_count > weaknesses_count and total_units >= 1000:
        verdict, badge_color = "HIGHLY VIABLE", "green"
    elif strengths_count >= weaknesses_count:
        verdict, badge_color = "VIABLE WITH CONDITIONS", "amber"
    else:
        verdict, badge_color = "REQUIRES FURTHER STUDY", "red"

    bullets = [
        f"Site: {ctx.get('site_name', '')} — "
        f"{ctx.get('land_area_ha', 0)} ha in {ctx.get('district', '')}, "
        f"{ctx.get('city', '')}",
        f"Concept: {ctx.get('development_concept', 'N/A')}",
        f"Target: {total_units:,} units across {len(zones)} zones "
        f"({total_highrise:,} high-rise, {total_lowrise:,} low-rise)",
    ]
    if price_targets:
        price_range_low = min(pt.get("price_usd_m2", 0) for pt in price_targets)
        price_range_high = max(pt.get("price_usd_m2", 0) for pt in price_targets)
        bullets.append(
            f"Price range: ${price_range_low:,.0f} – ${price_range_high:,.0f}/m\u00b2 "
            f"across {len(price_targets)} product types"
        )
    if directions:
        bullets.append(
            f"{len(directions)} development direction(s): "
            + ", ".join(d.get("direction_name", "") for d in directions[:3])
        )

    slides.append({
        "index": 11, "type": "conclusion",
        "title": "Development Verdict",
        "verdict": verdict,
        "bullets": bullets[:5],
        "badge_label": verdict,
        "badge_color": badge_color,
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "product_proposal",
        "language": language,
        "params": {
            "site_name": ctx.get("site_name"),
            "city": ctx.get("city"),
            "district": ctx.get("district"),
            "land_area_ha": ctx.get("land_area_ha"),
        },
        "slides": slides,
    }


def generate_product_proposal_pptx(
    session: Session,
    land_site_id: int,
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate an 11-slide product development proposal PPTX.

    Args:
        session: Database session.
        land_site_id: ID of the land site to generate proposal for.
        content_override: Pre-built manifest (from pptx-content-writer or ko-translator).
        language: "en" or "ko".

    Returns:
        Path to saved .pptx file, or None if context is unavailable.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        ctx = _assemble_proposal_context(session, land_site_id)
        if ctx is None:
            return None
        manifest = _build_default_manifest(ctx, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    site_slug = (
        ctx.get("site_name", "site") if not content_override
        else manifest.get("params", {}).get("site_name", "site")
    )
    site_slug = site_slug.lower().replace(" ", "_")[:30]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"product_proposal_{site_slug}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
