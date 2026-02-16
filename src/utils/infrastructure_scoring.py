"""Infrastructure scoring system for location quality assessment."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InfrastructureData:
    """Infrastructure data for a district."""
    # Public Transport (0-30 points)
    metro_stations: int = 0
    bus_routes: int = 0

    # Roads & Highways (0-20 points)
    highway_access: bool = False
    major_roads: int = 0

    # Education (0-20 points)
    international_schools: int = 0
    local_schools: int = 0
    universities: int = 0

    # Healthcare (0-15 points)
    hospitals: int = 0
    clinics: int = 0

    # Commercial (0-15 points)
    shopping_malls: int = 0
    supermarkets: int = 0

    # District type bonus (urban/suburban)
    district_type: Optional[str] = None


def calculate_infrastructure_score(infra: InfrastructureData) -> dict:
    """Calculate comprehensive infrastructure score (0-100).

    Args:
        infra: Infrastructure data for the district

    Returns:
        Dict with total score and breakdown by category
    """
    scores = {}

    # Public Transport (0-30 points)
    metro_score = min(infra.metro_stations * 10, 20)  # Max 20 for metro
    bus_score = min(infra.bus_routes * 2, 10)  # Max 10 for buses
    scores['public_transport'] = metro_score + bus_score

    # Roads & Highways (0-20 points)
    highway_score = 10 if infra.highway_access else 0
    road_score = min(infra.major_roads * 2, 10)
    scores['roads_highways'] = highway_score + road_score

    # Education (0-20 points)
    intl_school_score = min(infra.international_schools * 5, 10)
    local_school_score = min(infra.local_schools * 2, 5)
    university_score = min(infra.universities * 3, 5)
    scores['education'] = intl_school_score + local_school_score + university_score

    # Healthcare (0-15 points)
    hospital_score = min(infra.hospitals * 5, 10)
    clinic_score = min(infra.clinics * 1, 5)
    scores['healthcare'] = hospital_score + clinic_score

    # Commercial (0-15 points)
    mall_score = min(infra.shopping_malls * 5, 10)
    market_score = min(infra.supermarkets * 1, 5)
    scores['commercial'] = mall_score + market_score

    # Calculate total
    total_before_bonus = sum(scores.values())

    # District type bonus (0-10 points)
    bonus = 0
    if infra.district_type == "urban":
        bonus = 10
    elif infra.district_type == "suburban":
        bonus = 5
    scores['district_bonus'] = bonus

    total_score = min(total_before_bonus + bonus, 100)

    return {
        'total_score': total_score,
        'breakdown': scores,
        'grade': _score_to_grade(total_score)
    }


def _score_to_grade(score: int) -> str:
    """Convert infrastructure score to letter grade.

    Args:
        score: Total infrastructure score (0-100)

    Returns:
        Letter grade (A+, A, B+, B, C+, C, D)
    """
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C+"
    elif score >= 50:
        return "C"
    else:
        return "D"


# Preset infrastructure profiles for known districts
DISTRICT_INFRASTRUCTURE = {
    # HCMC Districts
    "District 1": InfrastructureData(
        metro_stations=2, bus_routes=15,
        highway_access=True, major_roads=8,
        international_schools=3, local_schools=10, universities=2,
        hospitals=5, clinics=20,
        shopping_malls=8, supermarkets=15,
        district_type="urban"
    ),
    "District 2": InfrastructureData(
        metro_stations=1, bus_routes=10,
        highway_access=True, major_roads=5,
        international_schools=5, local_schools=8, universities=1,
        hospitals=3, clinics=12,
        shopping_malls=4, supermarkets=10,
        district_type="urban"
    ),
    "District 7": InfrastructureData(
        metro_stations=1, bus_routes=12,
        highway_access=True, major_roads=6,
        international_schools=4, local_schools=10, universities=1,
        hospitals=3, clinics=15,
        shopping_malls=6, supermarkets=12,
        district_type="urban"
    ),
    "Binh Thanh": InfrastructureData(
        metro_stations=1, bus_routes=18,
        highway_access=True, major_roads=7,
        international_schools=2, local_schools=12, universities=1,
        hospitals=4, clinics=18,
        shopping_malls=5, supermarkets=14,
        district_type="urban"
    ),
    "Thu Duc City": InfrastructureData(
        metro_stations=0, bus_routes=8,
        highway_access=True, major_roads=4,
        international_schools=1, local_schools=6, universities=2,
        hospitals=2, clinics=10,
        shopping_malls=3, supermarkets=8,
        district_type="suburban"
    ),

    # Hanoi Districts
    "Ba Dinh": InfrastructureData(
        metro_stations=2, bus_routes=20,
        highway_access=True, major_roads=10,
        international_schools=4, local_schools=15, universities=3,
        hospitals=6, clinics=25,
        shopping_malls=6, supermarkets=18,
        district_type="urban"
    ),
    "Tay Ho": InfrastructureData(
        metro_stations=1, bus_routes=10,
        highway_access=False, major_roads=4,
        international_schools=6, local_schools=8, universities=0,
        hospitals=2, clinics=10,
        shopping_malls=3, supermarkets=10,
        district_type="urban"
    ),
    "Dong Da": InfrastructureData(
        metro_stations=2, bus_routes=18,
        highway_access=True, major_roads=8,
        international_schools=3, local_schools=14, universities=4,
        hospitals=5, clinics=22,
        shopping_malls=7, supermarkets=16,
        district_type="urban"
    ),
    "Cau Giay": InfrastructureData(
        metro_stations=1, bus_routes=15,
        highway_access=True, major_roads=6,
        international_schools=2, local_schools=10, universities=3,
        hospitals=3, clinics=15,
        shopping_malls=5, supermarkets=12,
        district_type="urban"
    ),
    "Nam Tu Liem": InfrastructureData(
        metro_stations=0, bus_routes=8,
        highway_access=True, major_roads=5,
        international_schools=1, local_schools=8, universities=1,
        hospitals=2, clinics=8,
        shopping_malls=4, supermarkets=10,
        district_type="suburban"
    ),

    # Binh Duong Districts
    "Thu Dau Mot": InfrastructureData(
        metro_stations=0, bus_routes=6,
        highway_access=True, major_roads=4,
        international_schools=0, local_schools=5, universities=1,
        hospitals=2, clinics=6,
        shopping_malls=2, supermarkets=6,
        district_type="urban"
    ),
    "Thuan An": InfrastructureData(
        metro_stations=0, bus_routes=4,
        highway_access=True, major_roads=3,
        international_schools=0, local_schools=4, universities=0,
        hospitals=1, clinics=4,
        shopping_malls=1, supermarkets=5,
        district_type="suburban"
    ),
}


def get_district_infrastructure_score(district_name: str) -> Optional[dict]:
    """Get infrastructure score for a known district.

    Args:
        district_name: District name (English)

    Returns:
        Infrastructure score dict or None if district not found
    """
    infra_data = DISTRICT_INFRASTRUCTURE.get(district_name)
    if infra_data:
        return calculate_infrastructure_score(infra_data)
    return None
