"""Compact land review report (small apartment sites like Di An 2.3ha)."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import LandSite
from src.reports.renderer import render_template


def _assemble_compact_review_context(session: Session, land_site_id: int) -> Optional[dict]:
    """LandSite + competitors (with unit mix) + views → context.

    Returns None if the land site is not found.
    """
    site = session.get(LandSite, land_site_id)
    if not site:
        return None

    competitors = sorted(site.competitors, key=lambda c: (c.distance_km or 999))
    price_targets = sorted(site.price_targets, key=lambda p: p.product_type)
    customers = list(site.target_customers)
    views = list(site.views)
    recommended = list(site.recommended_projects)

    # SWOT
    swot_grouped = {"S": [], "W": [], "O": [], "T": []}
    for item in site.swot_items:
        swot_grouped.get(item.swot_type, []).append(item.description)

    # Build competitor detail with unit mix
    comp_details = []
    for c in competitors:
        unit_mix = {}
        for field, label in [
            ("studio_pct", "Studio"),
            ("br1_1wc_pct", "1BR-1WC"),
            ("br1_5_1wc_pct", "1.5BR-1WC"),
            ("br2_1wc_pct", "2BR-1WC"),
            ("br2_2wc_pct", "2BR-2WC"),
            ("br2_5_2wc_pct", "2.5BR-2WC"),
            ("br3_2wc_pct", "3BR-2WC"),
        ]:
            val = getattr(c, field, None)
            if val:
                unit_mix[label] = val

        comp_details.append({
            "name": c.competitor_name,
            "developer": c.developer,
            "distance_km": c.distance_km,
            "distance_band": c.distance_band,
            "complex_area_ha": c.complex_area_ha,
            "complex_total_units": c.complex_total_units,
            "phase_code": c.phase_code,
            "phase_name": c.phase_name,
            "phase_units": c.phase_units,
            "apt_price_usd_m2": c.apt_price_usd_m2,
            "status": c.status,
            "launch_date": c.launch_date,
            "handover_date": c.handover_date,
            "sold_pct": c.sold_pct,
            "absorption_note": c.absorption_note,
            "unit_mix": unit_mix,
        })

    return {
        "generated_date": date.today().isoformat(),
        "site_name": site.name,
        "city": site.city_text,
        "district": site.district_text,
        "land_area_ha": site.land_area_ha,
        "development_type": site.development_type,
        "recommended_grade": site.recommended_grade,
        "total_units_target": site.total_units_target,
        "site_shape": site.site_shape,
        "frontage_count": site.frontage_count,
        "main_road_name": site.main_road_name,
        "main_road_width_m": site.main_road_width_m,
        "secondary_road_name": site.secondary_road_name,
        "secondary_road_width_m": site.secondary_road_width_m,
        "distance_to_cbd_km": site.distance_to_cbd_km,
        "distance_to_cbd_min": site.distance_to_cbd_min,
        "rental_yield_pct": site.rental_yield_pct,
        "pd_suggestion": site.pd_suggestion,
        "competitors": comp_details,
        "price_targets": [
            {
                "product_type": p.product_type,
                "price_usd_m2": p.price_usd_m2,
                "unit_size_m2": p.unit_size_m2,
                "unit_count": p.unit_count,
                "launch": p.launch,
            }
            for p in price_targets
        ],
        "target_customers": [
            {
                "segment_name": tc.segment_name,
                "ratio_pct": tc.ratio_pct,
                "purpose": tc.purpose,
                "profile": tc.profile,
                "target_products": tc.target_products,
            }
            for tc in customers
        ],
        "swot": swot_grouped,
        "views": [
            {
                "direction": v.direction,
                "view_type": v.view_type,
                "view_target": v.view_target,
                "impact_on_positioning": v.impact_on_positioning,
            }
            for v in views
        ],
        "recommended_projects": [
            {
                "project_name": r.project_name,
                "developer": r.developer,
                "grade": r.grade,
                "price_usd_m2": r.price_usd_m2,
                "sales_performance": r.sales_performance,
                "design_highlight": r.design_highlight,
                "recommendation_reason": r.recommendation_reason,
            }
            for r in recommended
        ],
    }


def generate_compact_land_review(session: Session, land_site_id: int) -> Optional[str]:
    """Generate compact land review as Markdown.

    Returns None if the land site is not found.
    """
    context = _assemble_compact_review_context(session, land_site_id)
    if not context:
        return None
    return render_template("compact_land_review.md.j2", **context)
