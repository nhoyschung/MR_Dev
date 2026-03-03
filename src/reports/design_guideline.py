"""Design guideline report generation (e.g. HP 7.2ha Kien An)."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import LandSite, DesignGuideline, SportParkFacility
from src.reports.renderer import render_template


def _assemble_design_guideline_context(
    session: Session, land_site_id: int,
) -> Optional[dict]:
    """DesignGuideline + product specs + case studies + sport park + competitors → context.

    Returns None if the land site or its design guideline is not found.
    """
    site = session.get(LandSite, land_site_id)
    if not site:
        return None

    guidelines = site.design_guidelines
    if not guidelines:
        return None
    dg = guidelines[0]  # primary guideline

    product_specs = [
        {
            "product_type": s.product_type,
            "ratio_pct": s.ratio_pct,
            "floors": s.floors,
            "unit_count": s.unit_count,
            "unit_size_min_m2": s.unit_size_min_m2,
            "unit_size_max_m2": s.unit_size_max_m2,
            "typical_size_m2": s.typical_size_m2,
            "target_price_usd_m2": s.target_price_usd_m2,
            "target_price_vnd_mil": s.target_price_vnd_mil,
            "expected_launch": s.expected_launch,
        }
        for s in dg.product_specs
    ]

    # Group design case studies by category
    case_studies_by_cat: dict[str, list] = {}
    for cs in dg.case_studies:
        cat = cs.reference_category
        case_studies_by_cat.setdefault(cat, []).append({
            "project_name": cs.project_name,
            "developer": cs.developer,
            "city_text": cs.city_text,
            "design_style": cs.design_style,
            "design_highlight": cs.design_highlight,
            "reference_purpose": cs.reference_purpose,
        })

    # Group competitors by product category
    competitors_by_cat: dict[str, list] = {}
    for c in site.competitors:
        cat = c.product_category or "other"
        price = (
            c.townhouse_price_usd_m2 or c.shophouse_price_usd_m2
            or c.apt_price_usd_m2 or c.villa_price_usd_m2
        )
        competitors_by_cat.setdefault(cat, []).append({
            "name": c.competitor_name,
            "developer": c.developer,
            "distance_km": c.distance_km,
            "phase_units": c.phase_units,
            "unit_size_min": c.unit_size_min,
            "unit_size_max": c.unit_size_max,
            "floors": c.floors,
            "price_usd_m2": price,
            "launch_date": c.launch_date,
            "handover_date": c.handover_date,
            "absorption_note": c.absorption_note,
        })

    # Sport park benchmarks
    sport_parks = session.query(SportParkFacility).all()
    sport_park_list = [
        {
            "name": sp.case_study_name or f"Site {sp.land_site_id}",
            "park_area_ha": sp.park_area_ha,
            "clubhouse": sp.clubhouse_count or 0,
            "tennis": sp.tennis_courts or 0,
            "badminton": sp.badminton_courts or 0,
            "basketball": sp.mini_basketball_courts or 0,
            "football": sp.mini_football_courts or 0,
            "playground": sp.kids_playgrounds or 0,
            "pool": sp.pool_count or 0,
            "kids_pool": sp.kids_pool_count or 0,
            "jacuzzi": sp.jacuzzi_count or 0,
            "outdoor_gym": sp.outdoor_gym_count or 0,
            "picnic": sp.picnic_lawn_count or 0,
            "bbq": sp.bbq_count or 0,
            "jogging": sp.jogging_track_count or 0,
        }
        for sp in sport_parks
    ]

    # Views
    views = [
        {
            "direction": v.direction,
            "view_type": v.view_type,
            "view_target": v.view_target,
            "impact_on_positioning": v.impact_on_positioning,
        }
        for v in site.views
    ]

    return {
        "generated_date": date.today().isoformat(),
        "site_name": site.name,
        "city": site.city_text,
        "district": site.district_text,
        "land_area_ha": site.land_area_ha,
        "total_units_target": site.total_units_target,
        "main_road_name": site.main_road_name,
        "secondary_road_name": site.secondary_road_name,
        "option_scenario": dg.option_scenario,
        "design_concept": dg.design_concept,
        "orientation_constraints": dg.orientation_constraints,
        "buffer_requirements": dg.buffer_requirements,
        "premiumization_strategy": dg.premiumization_strategy,
        "facade_direction": dg.facade_direction,
        "product_specs": product_specs,
        "case_studies_by_category": case_studies_by_cat,
        "competitors_by_category": competitors_by_cat,
        "sport_parks": sport_park_list,
        "views": views,
    }


def generate_design_guideline(session: Session, land_site_id: int) -> Optional[str]:
    """Generate design guideline report as Markdown.

    Returns None if the land site or its design guideline is not found.
    """
    context = _assemble_design_guideline_context(session, land_site_id)
    if not context:
        return None
    return render_template("design_guideline.md.j2", **context)
