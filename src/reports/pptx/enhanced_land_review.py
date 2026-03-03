"""PPTX generator: Enhanced Land Review — township-scale (10-slide template).

Slide structure:
  1.  Cover — "Enhanced Land Review", subtitle with site/city/area
  2.  KPI Dashboard — land area, total units, positioning, zone count, competitor count
  3.  Section Divider — "01 Market Analysis"
  4.  Competitor Pricing Table — top competitors with product type prices
  5.  FS Planning Table — product types, units, prices, launch
  6.  Section Divider — "02 Strategic Assessment"
  7.  SWOT Analysis
  8.  Target Customers Table — segments with ratios and profiles
  9.  Site Zones Table — zone code, area, FAR, strengths, weaknesses
  10. Conclusion — verdict based on competitor count and positioning
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.enhanced_land_review import _assemble_enhanced_site_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    """Build 10-slide manifest from _assemble_enhanced_site_context() output."""
    slides: list[dict] = []

    competitors = ctx.get("competitors", [])
    zones = ctx.get("zones", [])
    price_targets = ctx.get("price_targets", [])
    customers = ctx.get("target_customers", [])
    swot = ctx.get("swot", {})
    total_units = ctx.get("total_units_target") or 0

    # ── Slide 1: Cover ────────────────────────────────────────────────────
    slides.append({
        "index": 1, "type": "cover",
        "title": "Enhanced Land Review",
        "subtitle": (
            f"{ctx.get('site_name', 'Site')} · "
            f"{ctx.get('city', '')} · "
            f"{ctx.get('land_area_ha', 0)} ha"
        ),
        "city": ctx.get("city", ""),
        "period": ctx.get("generated_date", ""),
        "report_type": "Enhanced Land Review",
        "date": ctx.get("generated_date", ""),
    })

    # ── Slide 2: KPI Dashboard ────────────────────────────────────────────
    kpis = [
        {
            "label": "Land Area",
            "value": f"{ctx.get('land_area_ha', 0)} ha",
            "delta": None,
            "color": "blue",
        },
        {
            "label": "Total Units Target",
            "value": f"{total_units:,}" if total_units else "TBD",
            "delta": None,
            "color": "green",
        },
        {
            "label": "Positioning",
            "value": (ctx.get("positioning") or "N/A")[:25],
            "delta": ctx.get("recommended_grade"),
            "color": "amber",
        },
        {
            "label": "Site Zones",
            "value": str(len(zones)),
            "delta": None,
            "color": "blue",
        },
        {
            "label": "Competitors",
            "value": str(len(competitors)),
            "delta": None,
            "color": "red" if len(competitors) > 8 else "green",
        },
    ]

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{ctx.get('site_name', 'Site')} — Key Metrics",
        "kpis": kpis,
        "note": (
            f"{ctx.get('site_name', 'Site')}: {ctx.get('land_area_ha', 0)} ha "
            f"{ctx.get('development_type', 'mixed-use')} site in "
            f"{ctx.get('district', '')}, {ctx.get('city', '')}. "
            f"Grade recommendation: {ctx.get('recommended_grade', 'N/A')}. "
            f"{len(zones)} development zone(s), "
            f"{len(competitors)} competitor project(s) tracked."
        ),
    })

    # ── Slide 3: Section Divider — Market Analysis ────────────────────────
    slides.append({
        "index": 3, "type": "section_divider",
        "number": "01",
        "title": "Market Analysis",
        "subtitle": "Competitor Pricing & FS Planning",
    })

    # ── Slide 4: Competitor Pricing Table ─────────────────────────────────
    comp_rows = []
    for c in competitors[:10]:
        th = c.get("townhouse_price")
        sh = c.get("shophouse_price")
        vl = c.get("villa_price")
        comp_rows.append([
            (c.get("name") or "N/A")[:25],
            c.get("developer") or "N/A",
            f"{c.get('total_units', 0):,}" if c.get("total_units") else "—",
            f"${th:,.0f}" if th else "—",
            f"${sh:,.0f}" if sh else "—",
            f"${vl:,.0f}" if vl else "—",
            (c.get("status") or "N/A").title(),
        ])

    slides.append({
        "index": 4, "type": "table",
        "title": "Competitor Pricing Overview",
        "headers": [
            "Project", "Developer", "Units",
            "TH (USD/m²)", "SH (USD/m²)", "Villa (USD/m²)", "Status",
        ],
        "rows": comp_rows or [["No competitors", "—", "—", "—", "—", "—", "—"]],
        "caption": f"{len(competitors)} competitor project(s) identified across all distance bands.",
        "grade_col_index": None,
    })

    # ── Slide 5: FS Planning Table (Price Targets) ────────────────────────
    fs_rows = []
    for pt in price_targets:
        fs_rows.append([
            pt.get("product_type", "N/A"),
            f"{pt.get('unit_count', 0):,}" if pt.get("unit_count") else "—",
            f"{pt.get('unit_size_m2', 0):,.0f} m²" if pt.get("unit_size_m2") else "—",
            f"${pt.get('price_usd_m2', 0):,.0f}" if pt.get("price_usd_m2") else "—",
            f"{pt.get('total_price_vnd_bil', 0):,.1f} B" if pt.get("total_price_vnd_bil") else "—",
            pt.get("launch") or "TBD",
        ])

    slides.append({
        "index": 5, "type": "table",
        "title": "FS Planning — Product Types & Pricing",
        "headers": [
            "Product Type", "Units", "Size (m²)",
            "Price (USD/m²)", "Total (VND Bil)", "Launch",
        ],
        "rows": fs_rows or [["No pricing targets defined", "—", "—", "—", "—", "—"]],
        "caption": (
            f"Total target: {total_units:,} units"
            if total_units else None
        ),
        "grade_col_index": None,
    })

    # ── Slide 6: Section Divider — Strategic Assessment ───────────────────
    slides.append({
        "index": 6, "type": "section_divider",
        "number": "02",
        "title": "Strategic Assessment",
        "subtitle": "SWOT · Target Customers · Site Zones",
    })

    # ── Slide 7: SWOT Analysis ────────────────────────────────────────────
    slides.append({
        "index": 7, "type": "swot",
        "title": "SWOT Analysis",
        "strengths": swot.get("S", [])[:4],
        "weaknesses": swot.get("W", [])[:4],
        "opportunities": swot.get("O", [])[:4],
        "threats": swot.get("T", [])[:4],
    })

    # ── Slide 8: Target Customers Table ───────────────────────────────────
    cust_rows = []
    for tc in customers:
        cust_rows.append([
            tc.get("segment_name", "N/A"),
            f"{tc.get('ratio_pct', 0)}%" if tc.get("ratio_pct") is not None else "—",
            tc.get("purpose") or "—",
            (tc.get("profile") or "—")[:40],
            (tc.get("target_products") or "—")[:30],
        ])

    slides.append({
        "index": 8, "type": "table",
        "title": "Target Customer Segments",
        "headers": ["Segment", "Ratio", "Purpose", "Profile", "Target Products"],
        "rows": cust_rows or [["No segments defined", "—", "—", "—", "—"]],
        "caption": None,
        "grade_col_index": None,
    })

    # ── Slide 9: Site Zones Table ─────────────────────────────────────────
    zone_rows = []
    for z in zones:
        zone_rows.append([
            z.get("zone_code", "N/A"),
            f"{z.get('area_ha', 0):.1f} ha" if z.get("area_ha") else "—",
            f"{z.get('far', 0):.2f}" if z.get("far") else "—",
            (z.get("strengths") or "—")[:45],
            (z.get("weaknesses") or "—")[:45],
        ])

    slides.append({
        "index": 9, "type": "table",
        "title": "Site Zone Breakdown",
        "headers": ["Zone", "Area", "FAR", "Strengths", "Weaknesses"],
        "rows": zone_rows or [["No zones defined", "—", "—", "—", "—"]],
        "caption": f"{len(zones)} zone(s) totalling {ctx.get('land_area_ha', 0)} ha.",
        "grade_col_index": None,
    })

    # ── Slide 10: Conclusion ──────────────────────────────────────────────
    comp_count = len(competitors)
    positioning = ctx.get("positioning") or ""

    if comp_count <= 3 and "premium" in positioning.lower():
        verdict, badge_color = "HIGHLY VIABLE", "green"
    elif comp_count <= 6:
        verdict, badge_color = "MODERATELY VIABLE", "amber"
    else:
        verdict, badge_color = "COMPETITIVE — REQUIRES STUDY", "red"

    bullets = [
        f"Site: {ctx.get('land_area_ha', 0)} ha in "
        f"{ctx.get('district', '')}, {ctx.get('city', '')}",
        f"Development type: {ctx.get('development_type', 'N/A')}",
        f"Recommended grade: {ctx.get('recommended_grade', 'N/A')}",
    ]
    if total_units:
        bullets.append(f"Target: {total_units:,} units across {len(zones)} zone(s)")
    if competitors:
        bullets.append(f"{comp_count} competitor(s) tracked in surrounding area")
    if positioning:
        bullets.append(f"Positioning: {positioning[:60]}")

    slides.append({
        "index": 10, "type": "conclusion",
        "title": "Development Verdict",
        "verdict": verdict,
        "bullets": bullets[:5],
        "badge_label": verdict,
        "badge_color": badge_color,
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "enhanced_land_review",
        "language": language,
        "params": {
            "site_name": ctx.get("site_name"),
            "city": ctx.get("city"),
            "land_area_ha": ctx.get("land_area_ha"),
        },
        "slides": slides,
    }


def generate_enhanced_land_review_pptx(
    session: Session,
    land_site_id: int,
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate a 10-slide enhanced land review PPTX (township-scale).

    Args:
        session: Database session.
        land_site_id: Primary key of the LandSite record.
        content_override: Pre-built manifest (from pptx-content-writer or ko-translator).
        language: "en" or "ko".

    Returns:
        Path to saved .pptx file, or None if land site not found.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        ctx = _assemble_enhanced_site_context(session, land_site_id)
        if ctx is None:
            return None
        manifest = _build_default_manifest(ctx, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    site_slug = (
        manifest.get("params", {}).get("site_name", "site")
        or "site"
    ).lower().replace(" ", "_")[:30]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enhanced_land_review_{site_slug}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
