"""Zoning and regulatory data for districts."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RegulatoryInfo:
    """Regulatory and zoning information for a district."""
    # Zoning
    zoning_type: str  # residential, commercial, mixed-use, industrial

    # Development Restrictions
    max_plot_ratio: Optional[float] = None  # FAR (Floor Area Ratio)
    max_building_height_m: Optional[float] = None  # Maximum height in meters
    max_building_floors: Optional[int] = None  # Maximum number of floors

    # Density Control
    min_lot_size_m2: Optional[float] = None  # Minimum lot size
    max_lot_coverage_pct: Optional[float] = None  # Maximum lot coverage percentage

    # Environmental Constraints
    flood_zone: bool = False
    protected_area: bool = False
    environmental_impact_required: bool = False

    # Setback Requirements
    front_setback_m: Optional[float] = None
    side_setback_m: Optional[float] = None

    # Additional Notes
    notes: Optional[str] = None


# Regulatory profiles for known districts
DISTRICT_REGULATIONS = {
    # HCMC Districts
    "District 1": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=8.0,
        max_building_height_m=150.0,
        max_building_floors=40,
        min_lot_size_m2=300.0,
        max_lot_coverage_pct=60.0,
        flood_zone=False,
        protected_area=True,  # Some heritage areas
        environmental_impact_required=True,
        front_setback_m=5.0,
        side_setback_m=3.0,
        notes="Central business district with strict heritage preservation zones"
    ),

    "District 2": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=5.0,
        max_building_height_m=120.0,
        max_building_floors=35,
        min_lot_size_m2=500.0,
        max_lot_coverage_pct=50.0,
        flood_zone=True,  # Near Saigon River
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=6.0,
        side_setback_m=4.0,
        notes="Thu Thiem New Urban Area - special planning regulations apply"
    ),

    "District 7": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=4.5,
        max_building_height_m=100.0,
        max_building_floors=30,
        min_lot_size_m2=400.0,
        max_lot_coverage_pct=45.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=5.0,
        side_setback_m=3.5,
        notes="Phu My Hung master-planned community with additional design guidelines"
    ),

    "Binh Thanh": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=6.0,
        max_building_height_m=110.0,
        max_building_floors=32,
        min_lot_size_m2=350.0,
        max_lot_coverage_pct=55.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=5.0,
        side_setback_m=3.0,
        notes="Inner city district with established infrastructure"
    ),

    "Thu Duc City": RegulatoryInfo(
        zoning_type="residential",
        max_plot_ratio=3.5,
        max_building_height_m=80.0,
        max_building_floors=25,
        min_lot_size_m2=600.0,
        max_lot_coverage_pct=40.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=6.0,
        side_setback_m=4.0,
        notes="Innovation district with high-tech development incentives"
    ),

    # Hanoi Districts
    "Ba Dinh": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=7.0,
        max_building_height_m=140.0,
        max_building_floors=38,
        min_lot_size_m2=400.0,
        max_lot_coverage_pct=60.0,
        flood_zone=False,
        protected_area=True,  # Government quarter
        environmental_impact_required=True,
        front_setback_m=5.0,
        side_setback_m=3.0,
        notes="Capital's political center with strict building restrictions near government buildings"
    ),

    "Tay Ho": RegulatoryInfo(
        zoning_type="residential",
        max_plot_ratio=4.0,
        max_building_height_m=90.0,
        max_building_floors=28,
        min_lot_size_m2=500.0,
        max_lot_coverage_pct=45.0,
        flood_zone=False,
        protected_area=True,  # West Lake scenic area
        environmental_impact_required=True,
        front_setback_m=6.0,
        side_setback_m=4.0,
        notes="West Lake protection zone - additional environmental approvals required"
    ),

    "Dong Da": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=6.5,
        max_building_height_m=120.0,
        max_building_floors=34,
        min_lot_size_m2=350.0,
        max_lot_coverage_pct=55.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=5.0,
        side_setback_m=3.5,
        notes="Dense urban district with active redevelopment"
    ),

    "Cau Giay": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=5.5,
        max_building_height_m=110.0,
        max_building_floors=32,
        min_lot_size_m2=400.0,
        max_lot_coverage_pct=50.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=5.5,
        side_setback_m=3.5,
        notes="Tech and education hub with university zone restrictions"
    ),

    "Nam Tu Liem": RegulatoryInfo(
        zoning_type="residential",
        max_plot_ratio=3.0,
        max_building_height_m=75.0,
        max_building_floors=24,
        min_lot_size_m2=700.0,
        max_lot_coverage_pct=35.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=7.0,
        side_setback_m=5.0,
        notes="Suburban development with lower density requirements"
    ),

    # Binh Duong
    "Thu Dau Mot": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=4.0,
        max_building_height_m=85.0,
        max_building_floors=26,
        min_lot_size_m2=500.0,
        max_lot_coverage_pct=45.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=6.0,
        side_setback_m=4.0,
        notes="Provincial capital with moderate development intensity"
    ),

    "Thuan An": RegulatoryInfo(
        zoning_type="industrial",
        max_plot_ratio=2.5,
        max_building_height_m=60.0,
        max_building_floors=20,
        min_lot_size_m2=1000.0,
        max_lot_coverage_pct=40.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=7.0,
        side_setback_m=5.0,
        notes="Industrial zone with worker housing development allowed"
    ),

    "Di An": RegulatoryInfo(
        zoning_type="industrial",
        max_plot_ratio=3.0,
        max_building_height_m=70.0,
        max_building_floors=22,
        min_lot_size_m2=800.0,
        max_lot_coverage_pct=42.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=6.5,
        side_setback_m=4.5,
        notes="Industrial district transitioning to mixed-use residential"
    ),

    # Additional HCMC Districts
    "District 4": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=6.5,
        max_building_height_m=130.0,
        max_building_floors=36,
        min_lot_size_m2=350.0,
        max_lot_coverage_pct=55.0,
        flood_zone=True,  # Near Saigon River
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=5.0,
        side_setback_m=3.5,
        notes="Inner city district with river frontage - flood mitigation required"
    ),

    "District 9": RegulatoryInfo(
        zoning_type="residential",
        max_plot_ratio=3.5,
        max_building_height_m=80.0,
        max_building_floors=25,
        min_lot_size_m2=600.0,
        max_lot_coverage_pct=40.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=6.0,
        side_setback_m=4.5,
        notes="Eastern expansion zone with tech park development (now part of Thu Duc City)"
    ),

    "Binh Chanh": RegulatoryInfo(
        zoning_type="residential",
        max_plot_ratio=2.5,
        max_building_height_m=60.0,
        max_building_floors=20,
        min_lot_size_m2=800.0,
        max_lot_coverage_pct=35.0,
        flood_zone=True,  # Low-lying area
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=7.0,
        side_setback_m=5.0,
        notes="Suburban expansion zone with flood risk - drainage infrastructure required"
    ),

    # Additional Hanoi Districts
    "Thanh Xuan": RegulatoryInfo(
        zoning_type="mixed-use",
        max_plot_ratio=6.0,
        max_building_height_m=125.0,
        max_building_floors=35,
        min_lot_size_m2=400.0,
        max_lot_coverage_pct=55.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=5.0,
        side_setback_m=3.5,
        notes="Central district with active urban renewal and redevelopment"
    ),

    "Gia Lam": RegulatoryInfo(
        zoning_type="residential",
        max_plot_ratio=3.0,
        max_building_height_m=75.0,
        max_building_floors=24,
        min_lot_size_m2=700.0,
        max_lot_coverage_pct=38.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=6.5,
        side_setback_m=4.5,
        notes="Eastern suburban development zone near Noi Bai Airport"
    ),

    "Dong Anh": RegulatoryInfo(
        zoning_type="residential",
        max_plot_ratio=2.5,
        max_building_height_m=65.0,
        max_building_floors=21,
        min_lot_size_m2=900.0,
        max_lot_coverage_pct=35.0,
        flood_zone=False,
        protected_area=False,
        environmental_impact_required=True,
        front_setback_m=7.0,
        side_setback_m=5.0,
        notes="Northern suburban zone with lower density residential development"
    ),
}


def get_regulatory_info(district_name: str) -> Optional[RegulatoryInfo]:
    """Get regulatory information for a district.

    Args:
        district_name: District name (English)

    Returns:
        RegulatoryInfo object or None if district not found
    """
    return DISTRICT_REGULATIONS.get(district_name)


def calculate_max_gfa(land_area_m2: float, plot_ratio: float) -> float:
    """Calculate maximum Gross Floor Area (GFA) based on land area and plot ratio.

    Args:
        land_area_m2: Land area in square meters
        plot_ratio: Plot ratio (FAR - Floor Area Ratio)

    Returns:
        Maximum GFA in square meters
    """
    return land_area_m2 * plot_ratio


def estimate_max_units(land_area_m2: float, plot_ratio: float, avg_unit_size_m2: float = 75.0) -> int:
    """Estimate maximum number of units based on regulatory constraints.

    Args:
        land_area_m2: Land area in square meters
        plot_ratio: Plot ratio (FAR)
        avg_unit_size_m2: Average unit size (default 75m²)

    Returns:
        Estimated maximum number of units
    """
    max_gfa = calculate_max_gfa(land_area_m2, plot_ratio)
    # Assume 85% efficiency (15% for common areas, circulation, etc.)
    saleable_area = max_gfa * 0.85
    return int(saleable_area / avg_unit_size_m2)
