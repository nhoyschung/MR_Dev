"""Geographic utilities for location-based analysis."""

import math
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Project, District


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate distance between two coordinates using Haversine formula.

    Args:
        lat1: Latitude of point 1 (decimal degrees)
        lon1: Longitude of point 1 (decimal degrees)
        lat2: Latitude of point 2 (decimal degrees)
        lon2: Longitude of point 2 (decimal degrees)

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth radius in kilometers

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def find_nearby_projects(
    session: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    city_id: Optional[int] = None,
    limit: int = 20,
) -> list[tuple[Project, float]]:
    """Find projects within a specified radius of a location.

    Args:
        session: Database session
        latitude: Target latitude
        longitude: Target longitude
        radius_km: Search radius in kilometers (default 5.0)
        city_id: Optional city filter
        limit: Maximum number of results (default 20)

    Returns:
        List of (Project, distance) tuples sorted by distance
    """
    # Get all projects with coordinates
    stmt = select(Project).where(
        Project.latitude.isnot(None),
        Project.longitude.isnot(None)
    )

    if city_id:
        stmt = stmt.join(District).where(District.city_id == city_id)

    projects = session.execute(stmt).scalars().all()

    # Calculate distances
    results = []
    for project in projects:
        if project.latitude and project.longitude:
            distance = haversine_distance(
                latitude, longitude,
                project.latitude, project.longitude
            )
            if distance <= radius_km:
                results.append((project, distance))

    # Sort by distance and limit
    results.sort(key=lambda x: x[1])
    return results[:limit]


def find_competitors_by_grade(
    session: Session,
    latitude: float,
    longitude: float,
    grade_codes: list[str],
    radius_km: float = 5.0,
    limit: int = 10,
) -> list[tuple[Project, float]]:
    """Find competitor projects of specific grades within radius.

    Args:
        session: Database session
        latitude: Target latitude
        longitude: Target longitude
        grade_codes: List of grade codes (e.g., ['M-I', 'M-II', 'M-III'])
        radius_km: Search radius in kilometers (default 5.0)
        limit: Maximum number of results (default 10)

    Returns:
        List of (Project, distance) tuples sorted by distance
    """
    # Get projects with coordinates and matching grades
    stmt = select(Project).where(
        Project.latitude.isnot(None),
        Project.longitude.isnot(None),
        Project.grade_primary.in_(grade_codes)
    )

    projects = session.execute(stmt).scalars().all()

    # Calculate distances
    results = []
    for project in projects:
        if project.latitude and project.longitude:
            distance = haversine_distance(
                latitude, longitude,
                project.latitude, project.longitude
            )
            if distance <= radius_km:
                results.append((project, distance))

    # Sort by distance and limit
    results.sort(key=lambda x: x[1])
    return results[:limit]


def get_district_from_coords(
    session: Session,
    latitude: float,
    longitude: float,
    city_id: Optional[int] = None,
    max_distance_km: float = 20.0,
) -> Optional[District]:
    """Estimate district based on coordinates by finding nearest project.

    Args:
        session: Database session
        latitude: Target latitude
        longitude: Target longitude
        city_id: Optional city filter
        max_distance_km: Maximum search distance (default 20.0)

    Returns:
        District object or None if no nearby projects found
    """
    nearby = find_nearby_projects(
        session, latitude, longitude,
        radius_km=max_distance_km,
        city_id=city_id,
        limit=5
    )

    if not nearby:
        return None

    # Return district of nearest project
    nearest_project, _ = nearby[0]
    return nearest_project.district


def calculate_centroid(coordinates: list[tuple[float, float]]) -> tuple[float, float]:
    """Calculate the geographic centroid of multiple coordinates.

    Args:
        coordinates: List of (latitude, longitude) tuples

    Returns:
        Tuple of (centroid_latitude, centroid_longitude)
    """
    if not coordinates:
        raise ValueError("Coordinates list cannot be empty")

    lat_sum = sum(lat for lat, _ in coordinates)
    lon_sum = sum(lon for _, lon in coordinates)

    count = len(coordinates)
    return (lat_sum / count, lon_sum / count)
