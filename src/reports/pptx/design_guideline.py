"""PPTX generator: Design Guideline (9-slide template).

Slide structure:
  1.  Cover
  2.  KPI Dashboard (area, total units, product mix ratios, facade direction)
  3.  Section Divider — "01 Design Specifications"
  4.  Product Specs Table (type, ratio%, floors, unit size, target price)
  5.  PD Review Notes Table (constraints, orientation, buffer, premiumization)
  6.  Section Divider — "02 References & Benchmarks"
  7.  Competitor Benchmark Table (by product category, top entries)
  8.  Case Study Gallery Table (by category: project, style, highlight)
  9.  Conclusion (verdict based on design concept clarity)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.design_guideline import _assemble_design_guideline_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    """Build a 9-slide manifest from _assemble_design_guideline_context() output."""
    slides: list[dict] = []
    product_specs = ctx.get("product_specs", [])
    competitors_by_cat = ctx.get("competitors_by_category", {})
    case_studies_by_cat = ctx.get("case_studies_by_category", {})
    sport_benchmarks = ctx.get("sport_park_benchmarks", [])

    # ── Slide 1: Cover ──────────────────────────────────────────────────────
    design_concept = ctx.get("design_concept", "")
    slides.append({
        "index": 1, "type": "cover",
        "title": "Design Guideline",
        "subtitle": (
            f"{design_concept[:60]} · "
            f"{ctx.get('land_area_ha', 0)} ha"
        ),
        "city": ctx.get("city", ""),
        "period": ctx.get("district", ""),
        "report_type": "Design Guideline",
        "date": ctx.get("generated_date", ""),
    })

    # ── Slide 2: KPI Dashboard ──────────────────────────────────────────────
    total_units = sum(s.get("unit_count", 0) for s in product_specs)

    kpis = [
        {"label": "Land Area", "value": f"{ctx.get('land_area_ha', 0)} ha",
         "delta": None, "color": "blue"},
        {"label": "Total Units", "value": f"{total_units:,}",
         "delta": f"{len(product_specs)} product types", "color": "green"},
    ]

    # Add ratio KPIs for each product type (up to 3)
    for spec in product_specs[:3]:
        kpis.append({
            "label": spec.get("product_type", "N/A"),
            "value": f"{spec.get('ratio_pct', 0):.0f}%",
            "delta": f"{spec.get('unit_count', 0)} units",
            "color": "amber",
        })

    facade = ctx.get("facade_direction", "")
    if facade:
        kpis.append({
            "label": "Facade Direction",
            "value": facade[:20],
            "delta": None,
            "color": "blue",
        })

    note_parts = [
        f"{ctx.get('site_name', 'Site')}: {ctx.get('land_area_ha', 0)} ha "
        f"in {ctx.get('district', '')}, {ctx.get('city', '')}.",
        f"Design concept: {design_concept[:100]}." if design_concept else "",
        f"Total planned units: {total_units:,} across {len(product_specs)} product types.",
    ]

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{ctx.get('site_name', 'Site')} — Design Overview",
        "kpis": kpis[:6],
        "note": " ".join(p for p in note_parts if p),
    })

    # ── Slide 3: Section Divider — Design Specifications ────────────────────
    slides.append({
        "index": 3, "type": "section_divider",
        "number": "01",
        "title": "Design Specifications",
        "subtitle": f"{ctx.get('site_name', 'Site')} · Product Mix & Constraints",
    })

    # ── Slide 4: Product Specs Table ────────────────────────────────────────
    spec_headers = ["Product Type", "Ratio %", "Floors", "Unit Count",
                    "Typical Size (m²)", "Target Price (USD/m²)"]
    spec_rows = []
    for s in product_specs:
        spec_rows.append([
            s.get("product_type", "N/A"),
            f"{s.get('ratio_pct', 0):.0f}%",
            str(s.get("floors", "N/A")),
            f"{s.get('unit_count', 0):,}",
            f"{s.get('typical_size_m2', 0):.0f}",
            f"${s.get('target_price_usd_m2', 0):,}" if s.get("target_price_usd_m2") else "N/A",
        ])
    # Total row
    if spec_rows:
        total_ratio = sum(s.get("ratio_pct", 0) for s in product_specs)
        spec_rows.append([
            "TOTAL", f"{total_ratio:.0f}%", "—",
            f"{total_units:,}", "—", "—",
        ])

    slides.append({
        "index": 4, "type": "table",
        "title": "Product Specifications & Mix",
        "headers": spec_headers,
        "rows": spec_rows or [["No product specs", "—", "—", "—", "—", "—"]],
        "caption": None,
        "grade_col_index": None,
    })

    # ── Slide 5: PD Review Notes Table ──────────────────────────────────────
    pd_rows = [
        ["Design Concept", design_concept or "N/A"],
        ["Orientation Constraints", ctx.get("orientation_constraints", "N/A") or "N/A"],
        ["Buffer Requirements", ctx.get("buffer_requirements", "N/A") or "N/A"],
        ["Premiumization Strategy", ctx.get("premiumization_strategy", "N/A") or "N/A"],
        ["Facade Direction", facade or "N/A"],
    ]

    slides.append({
        "index": 5, "type": "table",
        "title": "PD Review Notes — Design Constraints",
        "headers": ["Parameter", "Details"],
        "rows": pd_rows,
        "caption": None,
        "grade_col_index": None,
    })

    # ── Slide 6: Section Divider — References & Benchmarks ──────────────────
    slides.append({
        "index": 6, "type": "section_divider",
        "number": "02",
        "title": "References & Benchmarks",
        "subtitle": "Competitor Analysis · Case Studies",
    })

    # ── Slide 7: Competitor Benchmark Table ─────────────────────────────────
    comp_headers = ["Category", "Project", "Developer", "Price (USD/m²)", "Highlight"]
    comp_rows = []
    for category, comps in competitors_by_cat.items():
        for c in comps[:3]:  # Top 3 per category
            comp_rows.append([
                category[:20],
                str(c.get("project_name", c.get("name", "N/A")))[:25],
                str(c.get("developer", "N/A"))[:20],
                f"${c.get('price_usd_m2', 0):,}" if c.get("price_usd_m2") else "N/A",
                str(c.get("design_highlight", c.get("highlight", "")))[:35],
            ])

    slides.append({
        "index": 7, "type": "table",
        "title": "Competitor Benchmarks by Product Category",
        "headers": comp_headers,
        "rows": comp_rows or [["No competitor data", "—", "—", "—", "—"]],
        "caption": f"{len(competitors_by_cat)} product categories benchmarked.",
        "grade_col_index": None,
    })

    # ── Slide 8: Case Study Gallery Table ───────────────────────────────────
    cs_headers = ["Category", "Project", "Design Style", "Highlight"]
    cs_rows = []
    for category, studies in case_studies_by_cat.items():
        for cs in studies[:3]:  # Top 3 per category
            cs_rows.append([
                category[:20],
                str(cs.get("project_name", "N/A"))[:25],
                str(cs.get("design_style", "N/A"))[:25],
                str(cs.get("design_highlight", ""))[:40],
            ])

    # Append sport park benchmarks if available
    if sport_benchmarks:
        for sb in sport_benchmarks[:3]:
            cs_rows.append([
                "Sport Park",
                str(sb.get("case_study_name", "N/A"))[:25],
                f"{sb.get('park_area_ha', 0)} ha",
                "Benchmark facility",
            ])

    slides.append({
        "index": 8, "type": "table",
        "title": "Design Case Study Gallery",
        "headers": cs_headers,
        "rows": cs_rows or [["No case studies", "—", "—", "—"]],
        "caption": f"{len(case_studies_by_cat)} categories with reference projects.",
        "grade_col_index": None,
    })

    # ── Slide 9: Conclusion ─────────────────────────────────────────────────
    concept_text = (design_concept or "").strip()
    has_specs = len(product_specs) > 0
    has_references = len(competitors_by_cat) > 0 or len(case_studies_by_cat) > 0

    if concept_text and has_specs and has_references:
        verdict, badge_color = "DESIGN READY", "green"
    elif concept_text and has_specs:
        verdict, badge_color = "CONCEPT DEFINED", "amber"
    else:
        verdict, badge_color = "REQUIRES DESIGN INPUT", "red"

    bullets = [
        f"Site: {ctx.get('site_name', 'N/A')} — "
        f"{ctx.get('land_area_ha', 0)} ha in {ctx.get('district', '')}, {ctx.get('city', '')}",
        f"Design concept: {concept_text[:80]}" if concept_text else "Design concept: not defined",
        f"Product mix: {len(product_specs)} types, {total_units:,} total units",
    ]
    if facade:
        bullets.append(f"Facade direction: {facade}")
    if competitors_by_cat:
        total_comps = sum(len(v) for v in competitors_by_cat.values())
        bullets.append(
            f"{total_comps} competitor references across "
            f"{len(competitors_by_cat)} categories"
        )

    slides.append({
        "index": 9, "type": "conclusion",
        "title": "Design Guideline Verdict",
        "verdict": verdict,
        "bullets": bullets[:5],
        "badge_label": verdict,
        "badge_color": badge_color,
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "design_guideline",
        "language": language,
        "params": {
            "site_name": ctx.get("site_name"),
            "land_site_id": ctx.get("land_site_id"),
        },
        "slides": slides,
    }


def generate_design_guideline_pptx(
    session: Session,
    land_site_id: int,
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate a 9-slide design guideline PPTX.

    Args:
        session: Database session.
        land_site_id: ID of the land site.
        content_override: Pre-built manifest (from AI content writer or translator).
        language: "en" or "ko".

    Returns:
        Path to saved .pptx file, or None if data unavailable.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        ctx = _assemble_design_guideline_context(session, land_site_id)
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
    filename = f"design_guideline_{site_slug}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
