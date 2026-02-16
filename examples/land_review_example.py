"""Example demonstrating land review automation system."""

from src.db.connection import get_session
from src.reports.land_review import generate_land_review_report


def example_hcmc_district2():
    """Example: 35ha land site in HCMC District 2 (Thao Dien area)."""
    land_input = {
        "city": "Ho Chi Minh City",
        "district": "District 2",
        "ward": "Thao Dien",
        "land_area_ha": 35.0,
        "latitude": 10.8042,  # Near Masteri Thao Dien
        "longitude": 106.7394,
        "land_use": "residential",
        "development_type": "mixed-use",
        "target_segment": "M-I",
        "transportation": "5 min to Thu Thiem Bridge, 15 min to District 1 CBD",
        "landmarks": [
            "Adjacent to Thu Thiem New Urban Area",
            "Near Metro Line 1 (under construction)",
            "Saigon River waterfront access"
        ],
        "strengths": [
            "Prime riverside location with skyline views",
            "Adjacent to established expat community",
            "Close to international schools (BIS, AIS)",
            "High-income demographic area"
        ],
        "weaknesses": [
            "High competition from Vinhomes, Masteri brands",
            "Land acquisition cost premium for prime location",
            "Seasonal flood risk near riverfront"
        ]
    }

    with get_session() as session:
        report = generate_land_review_report(session, land_input)

        output_file = "output/land_review_hcmc_district2_35ha.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Report generated: {output_file}")
        print(f"\nSummary:")
        print(f"- Location: {land_input['city']}, {land_input['district']}")
        print(f"- Land Area: {land_input['land_area_ha']} hectares")
        print(f"- Target Segment: {land_input['target_segment']}")
        print(f"- Coordinates: {land_input['latitude']}, {land_input['longitude']}")


def example_hanoi_tay_ho():
    """Example: 20ha land site in Hanoi Tay Ho district."""
    land_input = {
        "city": "Hanoi",
        "district": "Tay Ho",
        "land_area_ha": 20.0,
        "latitude": 21.0567,  # Near West Lake
        "longitude": 105.8234,
        "land_use": "residential",
        "development_type": "apartment",
        "target_segment": "H-I",
        "transportation": "West Lake waterfront, 10 min to Ba Dinh district",
        "landmarks": [
            "West Lake scenic area",
            "Near foreign embassies",
            "International schools nearby"
        ],
        "strengths": [
            "Premium West Lake location",
            "Established expat residential area",
            "Scenic lake views",
            "Proximity to diplomatic quarter"
        ],
        "weaknesses": [
            "Limited development area due to zoning",
            "Traffic congestion during peak hours",
            "Mature market with established competitors"
        ]
    }

    with get_session() as session:
        report = generate_land_review_report(session, land_input)

        output_file = "output/land_review_hanoi_tay_ho_20ha.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Report generated: {output_file}")
        print(f"\nSummary:")
        print(f"- Location: {land_input['city']}, {land_input['district']}")
        print(f"- Land Area: {land_input['land_area_ha']} hectares")
        print(f"- Target Segment: {land_input['target_segment']}")


def example_binh_duong_affordable():
    """Example: 45ha affordable housing in Binh Duong."""
    land_input = {
        "city": "Binh Duong",
        "district": "Thuan An",
        "land_area_ha": 45.0,
        "land_use": "residential",
        "development_type": "apartment",
        "target_segment": "A-I",
        "strengths": [
            "Adjacent to industrial zones (high worker demand)",
            "Low land acquisition cost",
            "Government support for affordable housing",
            "Growing industrial workforce"
        ],
        "weaknesses": [
            "Limited infrastructure (schools, hospitals)",
            "Distance from HCMC center (30-40 min)",
            "Lower income demographic",
            "Limited public transportation"
        ]
    }

    with get_session() as session:
        report = generate_land_review_report(session, land_input)

        output_file = "output/land_review_binh_duong_thuan_an_45ha.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Report generated: {output_file}")
        print(f"\nSummary:")
        print(f"- Location: {land_input['city']}, {land_input['district']}")
        print(f"- Land Area: {land_input['land_area_ha']} hectares")
        print(f"- Target Segment: {land_input['target_segment']} (Affordable Housing)")


if __name__ == "__main__":
    print("=" * 60)
    print("Land Review Automation - Example Reports")
    print("=" * 60)
    print()

    print("[1] HCMC District 2 - Mid-Range Riverside Development")
    print("-" * 60)
    example_hcmc_district2()
    print()

    print("[2] Hanoi Tay Ho - High-End West Lake Development")
    print("-" * 60)
    example_hanoi_tay_ho()
    print()

    print("[3] Binh Duong Thuan An - Affordable Worker Housing")
    print("-" * 60)
    example_binh_duong_affordable()
    print()

    print("=" * 60)
    print("All reports generated successfully!")
    print("Check the 'output/' directory for full reports.")
    print("=" * 60)
