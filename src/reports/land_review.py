"""Land review and site analysis report generation."""

from datetime import date
from typing import Optional

from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

from src.db.models import (
    Project, District, City, PriceRecord, GradeDefinition,
    SupplyRecord, ReportPeriod, Developer
)
from src.reports.renderer import render_template
from src.utils.geo_utils import (
    find_nearby_projects, find_competitors_by_grade, get_district_from_coords
)
from src.utils.infrastructure_scoring import get_district_infrastructure_score
from src.utils.regulatory_data import get_regulatory_info, estimate_max_units
from src.reports.location_map import create_competitor_map, save_map_to_file


# Grade groupings for segmentation
GRADE_SEGMENTS = {
    "Super-Luxury": ["SL"],
    "Luxury": ["L"],
    "High-End": ["H-I", "H-II"],
    "Mid-Range": ["M-I", "M-II", "M-III"],
    "Affordable": ["A-I", "A-II"],
}


def _infer_target_segment(land_input: dict) -> str:
    """Infer target market segment from land input."""
    target = land_input.get("target_segment", "")

    # If explicit target segment
    if target:
        for segment, grades in GRADE_SEGMENTS.items():
            if target in grades:
                return segment

    # Infer from land use and area
    land_use = land_input.get("land_use", "").lower()
    area_ha = land_input.get("land_area_ha", 0)

    if land_use == "luxury" or area_ha > 50:
        return "Luxury"
    elif land_use == "affordable" or area_ha < 10:
        return "Affordable"
    else:
        return "Mid-Range"


def _get_target_grades(segment: str) -> list[str]:
    """Get grade codes for a market segment."""
    return GRADE_SEGMENTS.get(segment, ["M-I", "M-II", "M-III"])


def _analyze_location(
    session: Session,
    land_input: dict,
    city: City,
    district: Optional[District],
) -> dict:
    """Analyze location characteristics and accessibility."""
    lat = land_input.get("latitude")
    lon = land_input.get("longitude")

    location_analysis = {
        "city": city.name_en,
        "district": district.name_en if district else land_input.get("district", "Unknown"),
        "ward": land_input.get("ward", "N/A"),
        "accessibility": [],
        "strengths": [],
        "weaknesses": [],
        "infrastructure_score": None,
        "regulatory_info": None,
    }

    # Regulatory information
    if district:
        reg_info = get_regulatory_info(district.name_en)
        if reg_info:
            location_analysis["regulatory_info"] = reg_info

            # Add constraints to weaknesses if applicable
            if reg_info.flood_zone:
                location_analysis["weaknesses"].append("Located in flood risk zone - mitigation required")
            if reg_info.protected_area:
                location_analysis["weaknesses"].append("Protected/heritage area - additional approvals required")
            if reg_info.max_plot_ratio and reg_info.max_plot_ratio < 3.0:
                location_analysis["weaknesses"].append(f"Low plot ratio ({reg_info.max_plot_ratio}) limits development density")

    # Infrastructure scoring
    if district:
        infra_score = get_district_infrastructure_score(district.name_en)
        if infra_score:
            location_analysis["infrastructure_score"] = infra_score
            score = infra_score["total_score"]
            grade = infra_score["grade"]

            # Add to accessibility notes
            location_analysis["accessibility"].append(
                f"Infrastructure Score: {score}/100 (Grade {grade})"
            )

            # Add strengths/weaknesses based on score
            if score >= 80:
                location_analysis["strengths"].append(f"Excellent infrastructure (Grade {grade})")
            elif score >= 60:
                location_analysis["strengths"].append(f"Good infrastructure (Grade {grade})")
            elif score < 50:
                location_analysis["weaknesses"].append(f"Limited infrastructure (Grade {grade})")

    # Basic accessibility analysis
    if district:
        if district.district_type == "urban":
            location_analysis["accessibility"].append("Central urban location with established infrastructure")
            location_analysis["strengths"].append("Prime urban location")
        elif district.district_type == "suburban":
            location_analysis["accessibility"].append("Suburban area with developing infrastructure")
            location_analysis["weaknesses"].append("Distance from city center")

    # Add transportation notes if provided
    if land_input.get("transportation"):
        location_analysis["accessibility"].append(land_input["transportation"])

    # Nearby landmarks
    if land_input.get("landmarks"):
        location_analysis["accessibility"].extend(land_input["landmarks"])

    return location_analysis


def _analyze_market(
    session: Session,
    city: City,
    district: Optional[District],
    target_grades: list[str],
    latest_period: ReportPeriod,
) -> dict:
    """Analyze market supply, demand, and pricing trends."""
    market_data = {
        "supply_summary": {},
        "price_trends": {},
        "absorption_rates": {},
    }

    # Supply analysis by grade
    if district:
        supply_stmt = (
            select(
                Project.grade_primary,
                func.sum(SupplyRecord.new_supply).label("total_supply"),
                func.avg(SupplyRecord.absorption_rate_pct).label("avg_absorption")
            )
            .join(Project, SupplyRecord.project_id == Project.id)
            .where(
                SupplyRecord.district_id == district.id,
                SupplyRecord.period_id == latest_period.id,
                Project.grade_primary.in_(target_grades)
            )
            .group_by(Project.grade_primary)
        )
        supply_data = session.execute(supply_stmt).all()

        for grade, supply, absorption in supply_data:
            market_data["supply_summary"][grade] = {
                "new_supply": int(supply or 0),
                "absorption_rate": round(float(absorption or 0), 1),
            }

    # Price trends by grade
    if district:
        price_stmt = (
            select(
                Project.grade_primary,
                func.avg(PriceRecord.price_usd_per_m2).label("avg_price"),
                func.min(PriceRecord.price_usd_per_m2).label("min_price"),
                func.max(PriceRecord.price_usd_per_m2).label("max_price"),
            )
            .join(Project, PriceRecord.project_id == Project.id)
            .where(
                Project.district_id == district.id,
                PriceRecord.period_id == latest_period.id,
                Project.grade_primary.in_(target_grades),
                PriceRecord.price_usd_per_m2.isnot(None)
            )
            .group_by(Project.grade_primary)
        )
        price_data = session.execute(price_stmt).all()

        for grade, avg, min_p, max_p in price_data:
            market_data["price_trends"][grade] = {
                "avg_price_m2": int(avg or 0),
                "price_range": f"${int(min_p or 0):,} - ${int(max_p or 0):,}",
            }

    return market_data


def _find_competitors(
    session: Session,
    land_input: dict,
    target_grades: list[str],
    radius_km: float = 5.0,
) -> list[dict]:
    """Find and analyze competitor projects."""
    lat = land_input.get("latitude")
    lon = land_input.get("longitude")

    if not lat or not lon:
        return []

    # Find nearby competitors with matching grades
    competitors = find_competitors_by_grade(
        session, lat, lon, target_grades, radius_km, limit=10
    )

    results = []
    for project, distance in competitors:
        competitor_data = {
            "name": project.name,
            "distance_km": round(distance, 2),
            "grade": project.grade_primary,
            "total_units": project.total_units,
            "status": project.status,
            "developer": project.developer.name_en if project.developer else "N/A",
        }

        # Get latest price if available
        latest_price = session.execute(
            select(PriceRecord)
            .where(PriceRecord.project_id == project.id)
            .order_by(PriceRecord.period_id.desc())
            .limit(1)
        ).scalar_one_or_none()

        if latest_price:
            competitor_data["price_m2"] = int(latest_price.price_usd_per_m2 or 0)

        results.append(competitor_data)

    return results


def _generate_swot_analysis(
    land_input: dict,
    location_data: dict,
    market_data: dict,
    competitors: list[dict],
) -> dict:
    """Generate SWOT analysis based on all gathered data."""
    swot = {
        "strengths": location_data.get("strengths", []).copy(),
        "weaknesses": location_data.get("weaknesses", []).copy(),
        "opportunities": [],
        "threats": [],
    }

    # Add custom SWOT from input
    if land_input.get("strengths"):
        swot["strengths"].extend(land_input["strengths"])
    if land_input.get("weaknesses"):
        swot["weaknesses"].extend(land_input["weaknesses"])

    # Market-based opportunities
    total_supply = sum(
        data.get("new_supply", 0)
        for data in market_data.get("supply_summary", {}).values()
    )
    avg_absorption = sum(
        data.get("absorption_rate", 0)
        for data in market_data.get("supply_summary", {}).values()
    ) / max(len(market_data.get("supply_summary", {})), 1)

    if avg_absorption > 70:
        swot["opportunities"].append(f"High market absorption rate ({avg_absorption:.0f}%) indicates strong demand")
    if total_supply < 1000:
        swot["opportunities"].append("Limited new supply in the area creates market opportunity")

    # Competitor-based threats
    if len(competitors) > 5:
        swot["threats"].append(f"High competition with {len(competitors)} nearby projects")

    nearby_luxury = sum(1 for c in competitors if c.get("grade") in ["SL", "L", "H-I"])
    if nearby_luxury > 3:
        swot["threats"].append("Strong competition from established luxury brands")

    return swot


def _recommend_product_mix(
    session: Session,
    land_input: dict,
    target_grades: list[str],
    market_data: dict,
    regulatory_info=None,
) -> dict:
    """Recommend optimal product mix based on market analysis."""
    land_area_ha = land_input.get("land_area_ha", 0)
    land_area_m2 = land_area_ha * 10000

    # Default unit mix percentages by segment
    unit_mix = {
        "1BR": 20,
        "2BR": 40,
        "3BR": 30,
        "4BR+": 10,
    }

    # Adjust based on segment
    segment = _infer_target_segment(land_input)
    if segment in ["Luxury", "Super-Luxury"]:
        unit_mix = {"2BR": 20, "3BR": 40, "4BR+": 30, "Penthouse": 10}
    elif segment == "Affordable":
        unit_mix = {"Studio": 20, "1BR": 40, "2BR": 30, "3BR": 10}

    # Estimate total units based on regulatory constraints or default
    if regulatory_info and regulatory_info.max_plot_ratio:
        estimated_units = estimate_max_units(land_area_m2, regulatory_info.max_plot_ratio)
    else:
        # Default: assuming 1,500 m2 per unit average
        estimated_units = int(land_area_m2 / 1500)

    recommendations = {
        "estimated_total_units": estimated_units,
        "unit_mix": unit_mix,
        "development_phases": 1 if estimated_units < 1000 else 2,
        "recommended_grades": target_grades,
        "max_plot_ratio": regulatory_info.max_plot_ratio if regulatory_info else None,
        "max_building_height_m": regulatory_info.max_building_height_m if regulatory_info else None,
        "max_building_floors": regulatory_info.max_building_floors if regulatory_info else None,
    }

    return recommendations


def _pricing_strategy(
    market_data: dict,
    target_grades: list[str],
    segment: str,
) -> dict:
    """Generate pricing strategy recommendations."""
    price_trends = market_data.get("price_trends", {})

    if not price_trends:
        return {
            "recommended_range": "Market data insufficient",
            "positioning": "Require additional market research",
        }

    # Calculate average market price
    avg_prices = [data["avg_price_m2"] for data in price_trends.values()]
    market_avg = sum(avg_prices) / len(avg_prices) if avg_prices else 0

    # Positioning strategy
    if segment in ["Luxury", "Super-Luxury"]:
        positioning = "Premium positioning at 10-15% above market average"
        price_multiplier = 1.125
    elif segment == "Affordable":
        positioning = "Competitive pricing at 5-10% below market average"
        price_multiplier = 0.925
    else:
        positioning = "Market-aligned pricing with quality differentiation"
        price_multiplier = 1.0

    recommended_price = int(market_avg * price_multiplier)

    return {
        "market_average_m2": f"${int(market_avg):,}",
        "recommended_price_m2": f"${recommended_price:,}",
        "positioning": positioning,
        "target_grades": target_grades,
    }


def _assemble_land_review_context(
    session: Session,
    land_input: dict,
    include_map: bool = True,
) -> dict:
    """Assemble all data needed for a land review report.

    Shared by both the Markdown renderer and the PPTX generator.

    Args:
        session: Database session
        land_input: Dictionary with land information (city required).
        include_map: Whether to generate the HTML competitor map (expensive).

    Returns:
        Context dict. Raises ValueError if city not found.
    """
    # Get city
    city_name = land_input.get("city")
    city = session.execute(
        select(City).where(City.name_en == city_name)
    ).scalar_one_or_none()

    if not city:
        raise ValueError(f"City '{city_name}' not found in database")

    # Get district
    district = None
    district_name = land_input.get("district")
    if district_name:
        district = session.execute(
            select(District).where(
                District.name_en == district_name,
                District.city_id == city.id
            )
        ).scalar_one_or_none()

    # If coordinates provided but no district, infer from nearby projects
    if not district and land_input.get("latitude") and land_input.get("longitude"):
        district = get_district_from_coords(
            session,
            land_input["latitude"],
            land_input["longitude"],
            city_id=city.id
        )

    # Get latest period
    latest_period = session.execute(
        select(ReportPeriod).order_by(ReportPeriod.year.desc(), ReportPeriod.half.desc())
    ).scalars().first()

    # Determine target segment and grades
    segment = _infer_target_segment(land_input)
    target_grades = _get_target_grades(segment)

    # Perform analyses
    location_data = _analyze_location(session, land_input, city, district)
    market_data = _analyze_market(session, city, district, target_grades, latest_period)
    competitors = _find_competitors(session, land_input, target_grades, radius_km=5.0)
    swot = _generate_swot_analysis(land_input, location_data, market_data, competitors)
    product_mix = _recommend_product_mix(session, land_input, target_grades, market_data, location_data.get("regulatory_info"))
    pricing = _pricing_strategy(market_data, target_grades, segment)

    # Generate competitor location map if coordinates provided (markdown only)
    competitor_map_html = None
    if include_map and land_input.get("latitude") and land_input.get("longitude") and competitors:
        competitor_projects = find_competitors_by_grade(
            session,
            land_input["latitude"],
            land_input["longitude"],
            target_grades,
            radius_km=5.0,
            limit=10
        )

        competitor_map_html = create_competitor_map(
            land_lat=land_input["latitude"],
            land_lon=land_input["longitude"],
            competitors=competitor_projects,
            land_name=f"{city.name_en} {district.name_en if district else ''} Land Site",
            zoom_start=13,
        )

    return {
        "generated_date": date.today().isoformat(),
        "land_input": land_input,
        "city": city.name_en,
        "district": district.name_en if district else land_input.get("district", "N/A"),
        "ward": land_input.get("ward", "N/A"),
        "land_area_ha": land_input.get("land_area_ha", 0),
        "land_area_m2": land_input.get("land_area_ha", 0) * 10000,
        "development_type": land_input.get("development_type", "mixed-use"),
        "target_segment": segment,
        "target_grades": target_grades,
        "location_analysis": location_data,
        "market_analysis": market_data,
        "competitors": competitors,
        "competitor_count": len(competitors),
        "competitor_map": competitor_map_html,
        "swot_analysis": swot,
        "product_recommendations": product_mix,
        "pricing_strategy": pricing,
        "period": f"{latest_period.year}-{latest_period.half}" if latest_period else "N/A",
    }


def generate_land_review_report(
    session: Session,
    land_input: dict,
) -> str:
    """Generate comprehensive land review report.

    Args:
        session: Database session
        land_input: Dictionary with land information
            Required: city, land_area_ha
            Optional: district, ward, latitude, longitude, land_use,
                     development_type, target_segment, strengths, weaknesses

    Returns:
        Rendered markdown report string
    """
    context = _assemble_land_review_context(session, land_input, include_map=True)
    return render_template("land_review.md.j2", **context)
