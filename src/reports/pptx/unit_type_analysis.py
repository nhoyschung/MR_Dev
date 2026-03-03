"""PPTX generator: Unit-Type Price Structure Analysis (7-slide template).

Slide structure:
  1. Cover — "Unit-Type Price Structure Analysis", subtitle: project name
  2. KPI Dashboard — CV%, is_inverted flag, price range, anomaly count
  3. Grouped Bar Chart — unit-type prices across subject + competitors
  4. Subject Detail Table — unit types with area, price, type_name
  5. Variance Comparison Chart — CV% comparison across projects
  6. Area vs Price Scatter — net area vs price per m2
  7. Conclusion — verdict based on is_inverted and anomaly count
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.config import OUTPUT_DIR
from src.reports.unit_type_analysis import _assemble_unit_type_context
from src.reports.pptx.builder import PptxBuilder
from src.reports.pptx.content_schema import SlideContentManifest


def _build_default_manifest(ctx: dict, language: str) -> SlideContentManifest:
    """Build a 7-slide manifest from _assemble_unit_type_context() output."""
    slides: list[dict] = []

    subject_prices = ctx.get("subject_prices", [])
    subject_variance = ctx.get("subject_variance") or {}
    comparison = ctx.get("comparison", {})
    anomalies = ctx.get("anomalies", [])
    competitor_details = ctx.get("competitor_details", [])

    # Derived stats
    usd_prices = [p["price_usd_per_m2"] for p in subject_prices if p.get("price_usd_per_m2")]
    price_min = min(usd_prices) if usd_prices else 0
    price_max = max(usd_prices) if usd_prices else 0
    cv_pct = subject_variance.get("cv_pct", 0.0)
    is_inverted = subject_variance.get("is_inverted", False)
    correlation = subject_variance.get("price_area_correlation", 0.0)

    # ── Slide 1: Cover ──────────────────────────────────────────────────────
    slides.append({
        "index": 1, "type": "cover",
        "title": "Unit-Type Price Structure Analysis",
        "subtitle": ctx["subject_name"],
        "city": "",
        "period": ctx.get("period", ""),
        "report_type": "Unit-Type Analysis",
        "date": ctx["generated_date"],
    })

    # ── Slide 2: KPI Dashboard ──────────────────────────────────────────────
    kpis = [
        {
            "label": "Price CV%",
            "value": f"{cv_pct:.1f}%",
            "delta": "Low dispersion" if cv_pct < 10 else "High dispersion",
            "color": "green" if cv_pct < 15 else "amber" if cv_pct < 25 else "red",
        },
        {
            "label": "Structure",
            "value": "INVERTED" if is_inverted else "NORMAL",
            "delta": f"Correlation: {correlation:+.2f}",
            "color": "red" if is_inverted else "green",
        },
        {
            "label": "Price Range (USD/m²)",
            "value": f"${price_min:,.0f} – ${price_max:,.0f}" if price_min else "N/A",
            "delta": f"{len(subject_prices)} unit types",
            "color": "blue",
        },
        {
            "label": "Anomalies Detected",
            "value": str(len(anomalies)),
            "delta": "No issues" if not anomalies else anomalies[0][:40],
            "color": "green" if not anomalies else "red",
        },
    ]

    market_avg_cv = comparison.get("market_avg_cv_pct", 0.0)
    cv_premium = comparison.get("subject_cv_premium", 0.0)
    if market_avg_cv > 0:
        kpis.append({
            "label": "Market Avg CV%",
            "value": f"{market_avg_cv:.1f}%",
            "delta": f"Subject premium: {cv_premium:+.1f}pp",
            "color": "blue",
        })

    note_parts = [
        f"{ctx['subject_name']} has {len(subject_prices)} unit types "
        f"with price coefficient of variation {cv_pct:.1f}%.",
    ]
    if is_inverted:
        note_parts.append(
            "ALERT: Price structure is inverted — larger units cost more per m2, "
            "contrary to typical market behaviour."
        )
    if anomalies:
        note_parts.append(f"{len(anomalies)} anomalies detected: {'; '.join(anomalies)}.")
    if market_avg_cv > 0:
        note_parts.append(
            f"Market average CV is {market_avg_cv:.1f}%; subject is "
            f"{cv_premium:+.1f}pp {'above' if cv_premium > 0 else 'below'} market."
        )

    slides.append({
        "index": 2, "type": "kpi_dashboard",
        "slide_title": f"{ctx['subject_name']} — Unit-Type KPIs · {ctx.get('period', '')}",
        "kpis": kpis,
        "note": " ".join(note_parts),
    })

    # ── Slide 3: Grouped Bar Chart ──────────────────────────────────────────
    # Build projects_data for the grouped bar: subject + competitors
    projects_data = [{
        "project_name": ctx["subject_name"],
        "unit_types": subject_prices,
    }]
    projects_data.extend(competitor_details)

    comp_names = ctx.get("competitor_names", [])
    chart_caption = (
        f"Unit-type price comparison: {ctx['subject_name']} vs "
        f"{', '.join(comp_names)}." if comp_names
        else f"Unit-type prices for {ctx['subject_name']}."
    )

    slides.append({
        "index": 3, "type": "chart",
        "title": "Unit-Type Price Comparison",
        "chart_type": "unit_type_grouped_bar",
        "chart_params": {"projects_data": projects_data},
        "caption": chart_caption,
        "right_panel_text": (
            "Grouped bar shows price per m² (USD) for each unit type "
            "across the subject project and its competitors.\n\n"
            "Look for:\n"
            "• Consistent pricing tiers\n"
            "• Inverted structures (larger → costlier per m²)\n"
            "• Outlier unit types"
        ),
    })

    # ── Slide 4: Subject Detail Table ───────────────────────────────────────
    detail_rows = []
    for ut in subject_prices:
        area_str = f"{ut['net_area_m2']:.1f}" if ut.get("net_area_m2") else "—"
        price_str = f"${ut['price_usd_per_m2']:,.0f}" if ut.get("price_usd_per_m2") else "—"
        detail_rows.append([
            ut.get("type_name", "—"),
            area_str,
            price_str,
        ])

    slides.append({
        "index": 4, "type": "table",
        "title": f"{ctx['subject_name']} — Unit-Type Detail",
        "headers": ["Unit Type", "Net Area (m²)", "Price (USD/m²)"],
        "rows": detail_rows if detail_rows else [["No data", "—", "—"]],
        "caption": (
            f"{len(subject_prices)} unit types. "
            f"Price range: ${price_min:,.0f} – ${price_max:,.0f}/m²."
            if price_min else None
        ),
        "grade_col_index": None,
    })

    # ── Slide 5: Variance Comparison Chart ──────────────────────────────────
    variance_data = []
    if subject_variance:
        variance_data.append({
            "project_name": ctx["subject_name"],
            "cv_pct": cv_pct,
            "is_inverted": is_inverted,
        })
    for comp_var in comparison.get("competitors", []):
        variance_data.append({
            "project_name": comp_var.get("project_name", "Competitor"),
            "cv_pct": comp_var.get("cv_pct", 0.0),
            "is_inverted": comp_var.get("is_inverted", False),
        })

    variance_caption = (
        f"CV% measures price dispersion across unit types. "
        f"Market average: {market_avg_cv:.1f}%."
        if market_avg_cv > 0
        else "CV% measures price dispersion across unit types."
    )

    slides.append({
        "index": 5, "type": "chart",
        "title": "Price Variance Comparison",
        "chart_type": "variance_comparison",
        "chart_params": {"variance_data": variance_data},
        "caption": variance_caption,
        "right_panel_text": (
            "Coefficient of Variation (CV%) reflects how much "
            "unit-type prices differ within a single project.\n\n"
            "• Low CV (<10%): Uniform pricing\n"
            "• Medium CV (10–20%): Normal differentiation\n"
            "• High CV (>20%): Wide pricing spread\n\n"
            "Red bars indicate inverted structures."
        ),
    })

    # ── Slide 6: Area vs Price Scatter ──────────────────────────────────────
    scatter_data = []
    for ut in subject_prices:
        if ut.get("net_area_m2") and ut.get("price_usd_per_m2"):
            scatter_data.append({
                "project_name": ctx["subject_name"],
                "type_name": ut.get("type_name", ""),
                "net_area_m2": ut["net_area_m2"],
                "price_usd_per_m2": ut["price_usd_per_m2"],
            })
    for cd in competitor_details:
        for ut in cd.get("unit_types", []):
            if ut.get("net_area_m2") and ut.get("price_usd_per_m2"):
                scatter_data.append({
                    "project_name": cd["project_name"],
                    "type_name": ut.get("type_name", ""),
                    "net_area_m2": ut["net_area_m2"],
                    "price_usd_per_m2": ut["price_usd_per_m2"],
                })

    scatter_caption = (
        f"Correlation: {correlation:+.2f}. "
        + ("Normal: larger units cost less per m²."
           if not is_inverted
           else "INVERTED: larger units cost more per m².")
    )

    slides.append({
        "index": 6, "type": "chart",
        "title": "Area vs Price Scatter",
        "chart_type": "area_price_scatter",
        "chart_params": {"scatter_data": scatter_data},
        "caption": scatter_caption,
        "right_panel_text": (
            "Each dot represents a unit type.\n\n"
            "Normal market: negative slope (larger → cheaper per m²).\n"
            "Inverted market: positive slope (larger → costlier per m²).\n\n"
            f"Subject correlation: {correlation:+.2f}"
        ),
    })

    # ── Slide 7: Conclusion ─────────────────────────────────────────────────
    if is_inverted and len(anomalies) >= 2:
        verdict, badge_color = "REQUIRES REVIEW", "red"
    elif is_inverted or len(anomalies) >= 1:
        verdict, badge_color = "CAUTION ADVISED", "amber"
    else:
        verdict, badge_color = "HEALTHY STRUCTURE", "green"

    bullets = []
    bullets.append(
        f"{ctx['subject_name']}: {len(subject_prices)} unit types, "
        f"CV {cv_pct:.1f}%."
    )
    if is_inverted:
        bullets.append(
            "Price structure is INVERTED — larger units are priced higher per m². "
            "This may indicate premium positioning or mispricing."
        )
    else:
        bullets.append(
            "Price structure follows normal pattern — larger units cost less per m²."
        )
    if anomalies:
        for a in anomalies[:3]:
            bullets.append(a)
    if market_avg_cv > 0:
        bullets.append(
            f"Subject CV ({cv_pct:.1f}%) vs market avg ({market_avg_cv:.1f}%): "
            f"{cv_premium:+.1f}pp."
        )
    if comp_names:
        bullets.append(
            f"Compared against {len(comp_names)} competitor(s): "
            f"{', '.join(comp_names)}."
        )

    slides.append({
        "index": 7, "type": "conclusion",
        "title": "Unit-Type Analysis — Verdict",
        "verdict": verdict,
        "bullets": bullets[:5],
        "badge_label": verdict,
        "badge_color": badge_color,
    })

    return {
        "job_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "report_type": "unit_type_analysis",
        "language": language,
        "params": {
            "project_name": ctx["subject_name"],
            "competitors": comp_names,
            "year": ctx.get("year"),
            "half": ctx.get("half"),
        },
        "slides": slides,
    }


def generate_unit_type_analysis_pptx(
    session: Session,
    project_name: str,
    competitor_names: list[str],
    year: int = 2025,
    half: str = "H2",
    content_override: Optional[SlideContentManifest] = None,
    language: str = "en",
) -> Optional[Path]:
    """Generate a 7-slide unit-type price structure analysis PPTX.

    Args:
        session: Database session.
        project_name: Subject project name.
        competitor_names: List of competitor project names.
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
        ctx = _assemble_unit_type_context(
            session, project_name, competitor_names, year, half
        )
        if ctx is None:
            return None
        manifest = _build_default_manifest(ctx, language)
        lang = language

    builder = PptxBuilder()
    builder.build_from_manifest(manifest)

    slug = project_name.lower().replace(" ", "_")[:30]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"unit_type_{slug}_{ts}_{lang}.pptx"
    output_path = OUTPUT_DIR / filename
    return builder.save(output_path)
