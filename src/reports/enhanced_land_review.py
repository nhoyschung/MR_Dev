"""Enhanced land review report generation (township-scale sites like HP 25ha)."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import LandSite
from src.reports.renderer import render_template


def _assemble_enhanced_site_context(session: Session, land_site_id: int) -> Optional[dict]:
    """LandSite + all child tables → report context dict.

    Returns None if the land site is not found.
    """
    site = session.get(LandSite, land_site_id)
    if not site:
        return None

    zones = sorted(site.zones, key=lambda z: z.zone_code)
    competitors = sorted(site.competitors, key=lambda c: (c.distance_km or 999))
    price_targets = sorted(site.price_targets, key=lambda p: p.product_type)
    customers = list(site.target_customers)
    specs = list(site.specifications)
    swot = list(site.swot_items)
    dev_phases = sorted(site.development_phases, key=lambda p: p.phase_number)

    # Group SWOT items
    swot_grouped = {"S": [], "W": [], "O": [], "T": []}
    for item in swot:
        swot_grouped.get(item.swot_type, []).append(item.description)

    # Group competitors by distance band
    comp_by_band: dict[str, list] = {}
    for c in competitors:
        band = c.distance_band or "unknown"
        comp_by_band.setdefault(band, []).append({
            "name": c.competitor_name,
            "developer": c.developer,
            "distance_km": c.distance_km,
            "total_units": c.total_units or c.phase_units,
            "townhouse_price": c.townhouse_price_usd_m2,
            "shophouse_price": c.shophouse_price_usd_m2,
            "villa_price": c.villa_price_usd_m2,
            "status": c.status,
            "launch_date": c.launch_date,
            "handover_date": c.handover_date,
        })

    return {
        "generated_date": date.today().isoformat(),
        "site_name": site.name,
        "city": site.city_text,
        "district": site.district_text,
        "land_area_ha": site.land_area_ha,
        "development_type": site.development_type,
        "recommended_grade": site.recommended_grade,
        "positioning": site.positioning,
        "total_units_target": site.total_units_target,
        "zones": [
            {
                "zone_code": z.zone_code,
                "area_ha": z.area_ha,
                "far": z.far,
                "strengths": z.strengths,
                "weaknesses": z.weaknesses,
            }
            for z in zones
        ],
        "competitors": [
            {
                "name": c.competitor_name,
                "developer": c.developer,
                "distance_km": c.distance_km,
                "distance_band": c.distance_band,
                "total_units": c.total_units or c.phase_units,
                "townhouse_price": c.townhouse_price_usd_m2,
                "shophouse_price": c.shophouse_price_usd_m2,
                "villa_price": c.villa_price_usd_m2,
                "status": c.status,
                "launch_date": c.launch_date,
                "handover_date": c.handover_date,
            }
            for c in competitors
        ],
        "comp_by_band": comp_by_band,
        "price_targets": [
            {
                "product_type": p.product_type,
                "price_usd_m2": p.price_usd_m2,
                "total_price_vnd_bil": p.total_price_vnd_bil,
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
        "specifications": [
            {
                "spec_type": s.spec_type,
                "value_text": s.value_text,
                "value_numeric": s.value_numeric,
                "direction": s.direction,
                "status": s.status,
                "notes": s.notes,
            }
            for s in specs
        ],
        "development_phases": [
            {
                "phase_number": p.phase_number,
                "phase_name": p.phase_name,
                "zone_code": p.zone_code,
                "product_types": p.product_types,
                "unit_count": p.unit_count,
                "launch_target": p.launch_target,
                "strategy_notes": p.strategy_notes,
            }
            for p in dev_phases
        ],
    }


def generate_enhanced_land_review(session: Session, land_site_id: int) -> Optional[str]:
    """Generate enhanced land review as Markdown.

    Returns None if the land site is not found.
    """
    context = _assemble_enhanced_site_context(session, land_site_id)
    if not context:
        return None
    return render_template("enhanced_land_review.md.j2", **context)
