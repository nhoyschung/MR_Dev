"""Tests for geographic utilities."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, City, District, Project, Developer
from src.utils.geo_utils import (
    haversine_distance,
    find_nearby_projects,
    find_competitors_by_grade,
    get_district_from_coords,
    calculate_centroid,
)


@pytest.fixture
def session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test data
    city = City(id=1, name_en="Test City", name_vi="Thành phố Test", region="South")
    district1 = District(id=1, city_id=1, name_en="District 1", district_type="urban")
    district2 = District(id=2, city_id=1, name_en="District 2", district_type="suburban")

    developer = Developer(id=1, name_en="Test Developer")

    # Projects in District 1 (near each other)
    proj1 = Project(
        id=1, name="Project A", district_id=1, developer_id=1,
        latitude=10.8000, longitude=106.7000, grade_primary="M-I"
    )
    proj2 = Project(
        id=2, name="Project B", district_id=1, developer_id=1,
        latitude=10.8050, longitude=106.7050, grade_primary="M-II"
    )
    proj3 = Project(
        id=3, name="Project C", district_id=1, developer_id=1,
        latitude=10.8100, longitude=106.7100, grade_primary="H-I"
    )

    # Projects in District 2 (far away)
    proj4 = Project(
        id=4, name="Project D", district_id=2, developer_id=1,
        latitude=10.9000, longitude=106.8000, grade_primary="M-I"
    )

    # Project without coordinates
    proj5 = Project(
        id=5, name="Project E", district_id=1, developer_id=1,
        grade_primary="M-III"
    )

    session.add_all([city, district1, district2, developer, proj1, proj2, proj3, proj4, proj5])
    session.commit()

    yield session
    session.close()


def test_haversine_distance():
    """Test Haversine distance calculation."""
    # Distance from HCMC to Hanoi (approximately 1160 km)
    hcmc_lat, hcmc_lon = 10.8231, 106.6297
    hanoi_lat, hanoi_lon = 21.0285, 105.8542

    distance = haversine_distance(hcmc_lat, hcmc_lon, hanoi_lat, hanoi_lon)

    # Should be approximately 1160 km (allow 10% margin)
    assert 1050 < distance < 1270

    # Distance from point to itself should be 0
    distance_zero = haversine_distance(hcmc_lat, hcmc_lon, hcmc_lat, hcmc_lon)
    assert distance_zero == 0.0

    # Short distance (1km approximation)
    lat1, lon1 = 10.8000, 106.7000
    lat2, lon2 = 10.8090, 106.7000  # ~1km north

    distance_short = haversine_distance(lat1, lon1, lat2, lon2)
    assert 0.9 < distance_short < 1.1


def test_find_nearby_projects(session):
    """Test finding projects within radius."""
    # Search near Project A (10.8000, 106.7000)
    nearby = find_nearby_projects(
        session,
        latitude=10.8000,
        longitude=106.7000,
        radius_km=10.0
    )

    # Should find Projects A, B, C (all in District 1, close to each other)
    # Should NOT find Project D (too far) or Project E (no coordinates)
    assert len(nearby) >= 1  # At least Project A
    assert len(nearby) <= 3  # Maximum A, B, C

    # Verify results are sorted by distance
    distances = [dist for _, dist in nearby]
    assert distances == sorted(distances)

    # Verify closest is Project A itself
    closest_project, closest_dist = nearby[0]
    assert closest_project.name == "Project A"
    assert closest_dist < 0.1  # Very close (basically same location)


def test_find_nearby_projects_with_city_filter(session):
    """Test finding nearby projects with city filter."""
    nearby = find_nearby_projects(
        session,
        latitude=10.8000,
        longitude=106.7000,
        radius_km=10.0,
        city_id=1
    )

    # All results should be from city 1
    for project, _ in nearby:
        assert project.district.city_id == 1


def test_find_competitors_by_grade(session):
    """Test finding competitor projects by grade."""
    # Search for M-I and M-II grade projects near Project A
    competitors = find_competitors_by_grade(
        session,
        latitude=10.8000,
        longitude=106.7000,
        grade_codes=["M-I", "M-II"],
        radius_km=10.0
    )

    # Should find Projects A (M-I) and B (M-II)
    # Should NOT find Project C (H-I) or D (too far) or E (no coords)
    assert len(competitors) >= 1

    # Verify all results match the specified grades
    for project, _ in competitors:
        assert project.grade_primary in ["M-I", "M-II"]


def test_find_competitors_by_grade_narrow_radius(session):
    """Test competitor search with narrow radius."""
    # Search with very small radius (should find only Project A)
    competitors = find_competitors_by_grade(
        session,
        latitude=10.8000,
        longitude=106.7000,
        grade_codes=["M-I", "M-II", "H-I"],
        radius_km=1.0  # Only 1km radius
    )

    # Should only find Project A (and maybe B if very close)
    assert len(competitors) >= 1
    assert competitors[0][0].name == "Project A"


def test_get_district_from_coords(session):
    """Test district inference from coordinates."""
    # Coordinates near Project A (District 1)
    district = get_district_from_coords(
        session,
        latitude=10.8010,
        longitude=106.7010,
        city_id=1
    )

    assert district is not None
    assert district.name_en == "District 1"


def test_get_district_from_coords_no_nearby(session):
    """Test district inference when no nearby projects."""
    # Coordinates far from any project
    district = get_district_from_coords(
        session,
        latitude=0.0,
        longitude=0.0,
        city_id=1
    )

    assert district is None


def test_calculate_centroid():
    """Test centroid calculation."""
    # Simple case: 4 corners of a square
    coords = [
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, 0.0),
        (1.0, 1.0),
    ]

    centroid_lat, centroid_lon = calculate_centroid(coords)

    # Centroid should be at (0.5, 0.5)
    assert abs(centroid_lat - 0.5) < 0.001
    assert abs(centroid_lon - 0.5) < 0.001


def test_calculate_centroid_single_point():
    """Test centroid with single coordinate."""
    coords = [(10.8000, 106.7000)]

    centroid_lat, centroid_lon = calculate_centroid(coords)

    # Centroid should be the same point
    assert centroid_lat == 10.8000
    assert centroid_lon == 106.7000


def test_calculate_centroid_empty_list():
    """Test centroid calculation with empty list."""
    with pytest.raises(ValueError, match="cannot be empty"):
        calculate_centroid([])


def test_find_nearby_projects_limit(session):
    """Test that limit parameter works correctly."""
    nearby = find_nearby_projects(
        session,
        latitude=10.8000,
        longitude=106.7000,
        radius_km=50.0,  # Large radius
        limit=2  # Only want 2 results
    )

    # Should return at most 2 results
    assert len(nearby) <= 2


def test_haversine_distance_edge_cases():
    """Test Haversine with edge cases."""
    # Poles
    north_pole_lat, north_pole_lon = 90.0, 0.0
    south_pole_lat, south_pole_lon = -90.0, 0.0

    distance_poles = haversine_distance(
        north_pole_lat, north_pole_lon,
        south_pole_lat, south_pole_lon
    )

    # Distance pole to pole should be approximately half Earth's circumference
    # Earth circumference ~40,075 km, so half ~20,037 km
    assert 19000 < distance_poles < 21000

    # Equator points
    eq_lat1, eq_lon1 = 0.0, 0.0
    eq_lat2, eq_lon2 = 0.0, 90.0

    distance_eq = haversine_distance(eq_lat1, eq_lon1, eq_lat2, eq_lon2)

    # Quarter of equator circumference ~10,000 km
    assert 9000 < distance_eq < 11000
