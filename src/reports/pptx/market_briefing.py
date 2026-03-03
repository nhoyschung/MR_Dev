"""PPTX generator: Market Briefing (7-slide template).

Slide structure:
  1. Cover
  2. KPI Dashboard  (project counts, total units, avg price, pipeline value)
  3. Grade Distribution Chart  (bar chart — project count by grade)
  4. Grade Price Matrix Table  (all grades: segment, projects, avg price, price band)
  5. Active Projects Table  (actual project names, grades, districts, prices, units)
  6. Supply Pipeline Table  (status breakdown: projects + total units)
  7. Conclusion  (verdict based on market depth + price coverage)

Key fix: uses latest available price for each project (any period), not just the
current period, so the tables are populated even when current-period records are sparse.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.market_briefing import _assemble_briefing_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest

# Grade ordering for display
_GRADE_ORDER = ["SL", "L", "H-I", "H-II", "M-I", "M-II", "M-III", "A-I", "A-II"]


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    """Build a data-rich manifest from _assemble_briefing_context() output.

    Uses project_details (latest price, any period) for full data coverage.
    """
    slides: list[dict] = []
    details = ctx.get("project_details", [])

    # ── Derived stats from project_details (latest price, any period) ──────
    priced = [p for p in details if p["price_usd"] > 0]
    selling = [p for p in details if p["status"] == "selling"]
    selling_priced = [p for p in selling if p["price_usd"] > 0]
    completed = [p for p in details if p["status"] == "completed"]
    under_const = [p for p in details if p["status"] == "under-construction"]

    total_units_selling = sum(p["total_units"] for p in selling)
    total_units_all = sum(p["total_units"] for p in details)
    avg_price = (sum(p["price_usd"] for p in priced) / len(priced)) if priced else 0

    # Price range across all priced projects
    all_prices = sorted(p["price_usd"] for p in priced)
    price_min = all_prices[0] if all_prices else 0
    price_max = all_prices[-1] if all_prices else 0

    # ── Slide 1: Cover ─────────────────────────────────────────────────────
    slides.append({
        "index": 1, "type": "cover",
        "title": f"{ctx['city_name']} Residential Market",
        "subtitle": "Market Intelligence Briefing  ·  NHO-PD Analysis",
        "city": ctx["city_name"],
        "period": ctx["period"],
        "report_type": "Market Briefing",
        "date": ctx["generated_date"],
    })

    # ── Slide 2: KPI Dashboard ─────────────────────────────────────────────
    kpis = [
        {"label": "Tracked Projects",
         "value": str(ctx["project_count"]),
         "delta": f"{ctx['active_selling']} selling · {len(completed)} completed",
         "color": "blue"},
        {"label": "Actively Selling",
         "value": str(ctx["active_selling"]),
         "delta": f"{total_units_selling:,} units in pipeline",
         "color": "green"},
        {"label": "Avg Price (USD/m²)",
         "value": f"${avg_price:,.0f}" if avg_price else "N/A",
         "delta": f"Range: ${price_min:,.0f} – ${price_max:,.0f}" if price_min else None,
         "color": "amber"},
        {"label": "Projects w/ Price Data",
         "value": str(len(priced)),
         "delta": f"{len(priced)/ctx['project_count']*100:.0f}% coverage",
         "color": "blue"},
        {"label": "Total Units (All)",
         "value": f"{total_units_all:,}",
         "delta": f"{total_units_selling:,} selling",
         "color": "blue"},
    ]
    if ctx.get("avg_absorption", 0) > 0:
        kpis.append({
            "label": "Absorption Rate",
            "value": f"{ctx['avg_absorption']:.1f}%",
            "delta": None,
            "color": "green" if ctx["avg_absorption"] > 60 else "amber",
        })

    # Market assessment narrative
    selling_ratio = ctx["active_selling"] / ctx["project_count"] * 100
    price_coverage = len(priced) / ctx["project_count"] * 100
    note_parts = [
        f"{ctx['city_name']} residential market tracks {ctx['project_count']} projects "
        f"({ctx['active_selling']} actively selling, {len(completed)} completed, "
        f"{ctx['under_construction']} under construction).",
    ]
    if avg_price > 0:
        note_parts.append(
            f"Weighted average price across {len(priced)} priced projects: "
            f"${avg_price:,.0f}/m² (range: ${price_min:,.0f}–${price_max:,.0f})."
        )
    note_parts.append(
        f"Active selling pipeline: {total_units_selling:,} residential units. "
        f"Total tracked inventory: {total_units_all:,} units across all statuses."
    )

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{ctx['city_name']} — Market Dashboard · {ctx['period']}",
        "kpis": kpis,
        "note": " ".join(note_parts),
    })

    # ── Slide 3: Grade Distribution Chart ─────────────────────────────────
    # Use project_details for count (not grade_distribution which uses period prices)
    grade_counts: dict[str, int] = {}
    for p in details:
        g = p["grade"]
        if g and g != "N/A":
            grade_counts[g] = grade_counts.get(g, 0) + 1

    grade_data = [
        {"grade": g, "count": grade_counts[g]}
        for g in _GRADE_ORDER if g in grade_counts
    ]
    if not grade_data:
        grade_data = [{"grade": g["code"], "count": g["project_count"]}
                      for g in ctx["grades"] if g["project_count"] > 0]

    grade_note_parts = []
    for g in _GRADE_ORDER:
        cnt = grade_counts.get(g, 0)
        if cnt > 0:
            grade_note_parts.append(f"{g}: {cnt}")
    grade_note = "  ·  ".join(grade_note_parts)

    slides.append({
        "index": 3, "type": "chart",
        "title": "Project Count by Grade Tier",
        "chart_type": "grade_distribution",
        "chart_params": {"grade_data": grade_data},
        "caption": f"Grade breakdown: {grade_note}",
        "right_panel_text": (
            "Grade classification (NHO-PD):\n\n"
            "• SL — Super-Luxury (>$15,000)\n"
            "• L  — Luxury ($7,001–$15,000)\n"
            "• H-I — High-End I ($5,001–$7,000)\n"
            "• H-II — High-End II ($3,001–$5,000)\n"
            "• M-I — Mid-Range I ($2,001–$3,000)\n"
            "• M-II — Mid-Range II ($1,501–$2,000)\n"
            "• M-III — Mid-Range III ($1,001–$1,500)\n"
            "• A-I — Affordable I (<$1,000)"
        ),
    })

    # ── Slide 4: Grade Price Matrix ────────────────────────────────────────
    # Build by-grade stats from project_details (latest price, any period)
    grade_stats: dict[str, dict] = {}
    for p in details:
        g = p["grade"]
        if not g or g == "N/A":
            continue
        if g not in grade_stats:
            grade_stats[g] = {"count": 0, "prices": [], "units": 0}
        grade_stats[g]["count"] += 1
        grade_stats[g]["units"] += p["total_units"]
        if p["price_usd"] > 0:
            grade_stats[g]["prices"].append(p["price_usd"])

    grade_rows = []
    for g in _GRADE_ORDER:
        if g not in grade_stats:
            continue
        st = grade_stats[g]
        prices = st["prices"]
        grade_def = next((x for x in ctx["grades"] if x["code"] == g), {})
        seg = grade_def.get("segment", "").title()
        if prices:
            avg_g = sum(prices) / len(prices)
            price_band = f"${min(prices):,.0f} – ${max(prices):,.0f}"
            avg_str = f"${avg_g:,.0f}"
        else:
            price_band = f"${grade_def.get('min_price',0):,.0f} – ${grade_def.get('max_price',0):,.0f}" \
                if grade_def.get("min_price") else "—"
            avg_str = "—"
        grade_rows.append([
            g, seg, str(st["count"]),
            f"{st['units']:,}" if st["units"] else "—",
            avg_str, price_band,
        ])

    slides.append({
        "index": 4, "type": "table",
        "title": "Grade Distribution & Pricing Matrix",
        "headers": ["Grade", "Segment", "Projects", "Total Units", "Avg Price/m²", "Price Band (USD)"],
        "rows": grade_rows if grade_rows else [["No data", "—", "—", "—", "—", "—"]],
        "caption": (
            f"Price data from latest available period per project. "
            f"{len(priced)} of {ctx['project_count']} projects have price records."
        ),
        "grade_col_index": 0,
    })

    # ── Slide 5: Active Projects Table ─────────────────────────────────────
    # Sort selling projects by price desc, then all others
    selling_sorted = sorted(selling, key=lambda p: p["price_usd"], reverse=True)
    top_projects = selling_sorted[:12]  # show top 12

    proj_rows = []
    for p in top_projects:
        price_str = f"${p['price_usd']:,.0f}" if p["price_usd"] > 0 else "—"
        units_str = f"{p['total_units']:,}" if p["total_units"] else "—"
        proj_rows.append([
            p["name"][:28],
            p["grade"],
            p["district"],
            price_str,
            units_str,
        ])

    slides.append({
        "index": 5, "type": "table",
        "title": f"Active Selling Projects · {ctx['city_name']} ({ctx['period']})",
        "headers": ["Project", "Grade", "District", "Price (USD/m²)", "Units"],
        "rows": proj_rows if proj_rows else [["No active projects", "—", "—", "—", "—"]],
        "caption": (
            f"Showing top {len(top_projects)} of {ctx['active_selling']} actively selling projects "
            f"(ranked by price). "
            + (f"Total selling pipeline: {total_units_selling:,} units."
               if total_units_selling else "")
        ),
        "grade_col_index": 1,
    })

    # ── Slide 6: Supply Pipeline by Status ─────────────────────────────────
    pipeline = ctx.get("supply_pipeline", [])
    supply_rows = [
        [p["status"].replace("-", " ").title(), str(p["count"]), f"{p['units']:,}"]
        for p in pipeline
    ]
    # Add total row
    total_proj = sum(p["count"] for p in pipeline)
    total_units = sum(p["units"] for p in pipeline)
    supply_rows.append(["TOTAL", str(total_proj), f"{total_units:,}"])

    slides.append({
        "index": 6, "type": "table",
        "title": "Supply Pipeline by Development Status",
        "headers": ["Status", "Projects", "Total Units"],
        "rows": supply_rows if supply_rows else [["No data", "—", "—"]],
        "caption": (
            f"Total tracked inventory: {total_units:,} units across {total_proj} projects. "
            f"Selling pipeline accounts for {total_units_selling:,} units "
            f"({total_units_selling/total_units*100:.0f}% of total)."
            if total_units > 0 else None
        ),
        "grade_col_index": None,
    })

    # ── Slide 7: Conclusion ─────────────────────────────────────────────────
    # Verdict logic: use market depth, not just absorption rate
    if len(selling) >= 15 and avg_price >= 3000:
        verdict, badge_color = "ACTIVE MARKET", "green"
    elif len(selling) >= 8:
        verdict, badge_color = "MODERATE MARKET", "amber"
    else:
        verdict, badge_color = "EARLY STAGE", "red"

    bullets = []
    bullets.append(
        f"{ctx['city_name']} tracks {ctx['project_count']} projects: "
        f"{ctx['active_selling']} selling / {len(completed)} completed / "
        f"{ctx['under_construction']} under construction."
    )
    if avg_price > 0:
        bullets.append(
            f"Average price: ${avg_price:,.0f}/m² across {len(priced)} priced projects "
            f"(range ${price_min:,.0f} – ${price_max:,.0f}/m²)."
        )
    if total_units_selling > 0:
        bullets.append(
            f"Active selling pipeline: {total_units_selling:,} residential units."
        )
    # Dominant grade
    if grade_counts:
        dominant = max(grade_counts, key=grade_counts.get)
        bullets.append(
            f"Dominant grade: {dominant} with {grade_counts[dominant]} projects "
            f"({grade_counts[dominant]/ctx['project_count']*100:.0f}% of total)."
        )
    if grade_stats.get("L") or grade_stats.get("H-I"):
        lux_count = grade_counts.get("L", 0) + grade_counts.get("H-I", 0) + grade_counts.get("H-II", 0)
        bullets.append(
            f"Premium supply (L / H-I / H-II): {lux_count} projects — "
            "high-end segment remains active."
        )

    slides.append({
        "index": 7, "type": "conclusion",
        "title": "Market Conclusion & Outlook",
        "verdict": verdict,
        "bullets": bullets[:5],
        "badge_label": verdict,
        "badge_color": badge_color,
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "market_briefing",
        "language": language,
        "params": {
            "city": ctx["city_name"],
            "year": ctx.get("year"),
            "half": ctx.get("half"),
        },
        "slides": slides,
    }


def generate_market_briefing_pptx(
    session: Session,
    city_name: str,
    year: int,
    half: str,
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate a 7-slide market briefing PPTX.

    Args:
        session: Database session.
        city_name: City to query (e.g. "Ho Chi Minh City").
        year: Report year.
        half: Report half ("H1" or "H2").
        content_override: Pre-built manifest (from pptx-content-writer or ko-translator).
        language: "en" or "ko".

    Returns:
        Path to saved .pptx file, or None if data unavailable.
    """
    if content_override is not None:
        manifest = content_override
        lang = manifest.get("language", language)
    else:
        ctx = _assemble_briefing_context(session, city_name, year, half)
        if ctx is None:
            return None
        manifest = _build_default_manifest(ctx, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    slug = city_name.lower().replace(" ", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_briefing_{slug}_{year}_{half}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
