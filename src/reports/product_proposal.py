"""Product development proposal report generation (e.g. HP 35ha)."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import LandSite, CaseStudyProject
from src.reports.renderer import render_template


def _assemble_proposal_context(session: Session, land_site_id: int) -> Optional[dict]:
    """LandSite + zones + case studies + development directions → context.

    Returns None if the land site is not found.
    """
    site = session.get(LandSite, land_site_id)
    if not site:
        return None

    zones = sorted(site.zones, key=lambda z: z.zone_code)
    competitors = sorted(site.competitors, key=lambda c: (c.distance_km or 999))
    price_targets = sorted(site.price_targets, key=lambda p: p.product_type)
    customers = list(site.target_customers)
    directions = sorted(site.development_directions, key=lambda d: d.direction_number)

    # SWOT
    swot_grouped = {"S": [], "W": [], "O": [], "T": []}
    for item in site.swot_items:
        swot_grouped.get(item.swot_type, []).append(item.description)

    # Case studies (all)
    case_studies = session.query(CaseStudyProject).all()
    case_study_list = []
    for cs in case_studies:
        phases = []
        for phase in sorted(cs.phases, key=lambda p: p.phase_code):
            unit_types = [
                {
                    "product_type": ut.product_type,
                    "unit_count": ut.unit_count,
                    "land_size_min_m2": ut.land_size_min_m2,
                    "land_size_max_m2": ut.land_size_max_m2,
                    "gfa_m2": ut.gfa_m2,
                    "avg_price_usd_m2": ut.avg_price_usd_m2,
                }
                for ut in phase.unit_types
            ]
            phases.append({
                "phase_code": phase.phase_code,
                "phase_name": phase.phase_name,
                "area_ha": phase.area_ha,
                "total_units": phase.total_units,
                "launch_date": phase.launch_date,
                "handover_date": phase.handover_date,
                "sales_status": phase.sales_status,
                "sold_pct": phase.sold_pct,
                "absorption_days": phase.absorption_days,
                "avg_price_usd_m2": phase.avg_price_usd_m2,
                "unit_types": unit_types,
            })
        case_study_list.append({
            "project_name": cs.project_name,
            "developer_name": cs.developer_name,
            "city_text": cs.city_text,
            "land_area_ha": cs.land_area_ha,
            "bcr_pct": cs.bcr_pct,
            "total_units": cs.total_units,
            "avg_price_usd_m2": cs.avg_price_usd_m2,
            "positioning_concept": cs.positioning_concept,
            "management_company": cs.management_company,
            "phases": phases,
        })

    return {
        "generated_date": date.today().isoformat(),
        "site_name": site.name,
        "city": site.city_text,
        "district": site.district_text,
        "land_area_ha": site.land_area_ha,
        "development_concept": site.development_concept,
        "total_units_target": site.total_units_target,
        "total_highrise_units": site.total_highrise_units,
        "total_lowrise_units": site.total_lowrise_units,
        "zones": [
            {
                "zone_code": z.zone_code,
                "area_ha": z.area_ha,
                "highrise_units_planned": z.highrise_units_planned,
                "lowrise_units_planned": z.lowrise_units_planned,
                "key_anchor": z.key_anchor,
                "phase_sequence": z.phase_sequence,
                "benchmark_project": z.benchmark_project,
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
            }
            for c in competitors
        ],
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
        "development_directions": [
            {
                "direction_number": d.direction_number,
                "direction_name": d.direction_name,
                "concept_keywords": d.concept_keywords,
                "standard_amenities": d.standard_amenities,
                "premium_amenities": d.premium_amenities,
                "driving_amenities": d.driving_amenities,
                "target_positioning": d.target_positioning,
            }
            for d in directions
        ],
        "swot": swot_grouped,
        "case_studies": case_study_list,
    }


def generate_product_proposal(session: Session, land_site_id: int) -> Optional[str]:
    """Generate product development proposal as Markdown.

    Returns None if the land site is not found.
    """
    context = _assemble_proposal_context(session, land_site_id)
    if not context:
        return None
    return render_template("product_proposal.md.j2", **context)
