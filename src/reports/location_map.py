"""Location map visualization for land review reports."""

from typing import Optional

try:
    import folium
    from folium import Circle, Marker, Popup, Icon
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False


# Grade color mapping
GRADE_COLORS = {
    "SL": "darkred",
    "L": "red",
    "H-I": "orange",
    "H-II": "lightred",
    "M-I": "blue",
    "M-II": "lightblue",
    "M-III": "cadetblue",
    "M": "lightblue",
    "A-I": "green",
    "A-II": "lightgreen",
    "A": "lightgreen",
}


def create_competitor_map(
    land_lat: float,
    land_lon: float,
    competitors: list[tuple],  # List of (Project, distance) tuples
    land_name: str = "Target Land",
    zoom_start: int = 13,
) -> Optional[str]:
    """Create an interactive map showing target land and competitor locations.

    Args:
        land_lat: Target land latitude
        land_lon: Target land longitude
        competitors: List of (Project, distance) tuples
        land_name: Name/description for target land
        zoom_start: Initial zoom level (default 13)

    Returns:
        HTML string of the map, or None if folium not available
    """
    if not FOLIUM_AVAILABLE:
        return None

    # Create base map centered on target land
    m = folium.Map(
        location=[land_lat, land_lon],
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
    )

    # Add distance circles (1km, 3km, 5km)
    for radius_km, color, opacity in [(1, "green", 0.2), (3, "blue", 0.15), (5, "red", 0.1)]:
        Circle(
            location=[land_lat, land_lon],
            radius=radius_km * 1000,  # Convert to meters
            color=color,
            fill=True,
            fillOpacity=opacity,
            weight=2,
            popup=f"{radius_km}km radius",
        ).add_to(m)

    # Add target land marker (large star icon)
    target_popup = folium.Popup(
        f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="margin: 0; color: darkred;">🎯 {land_name}</h4>
            <hr style="margin: 5px 0;">
            <b>Coordinates:</b><br>
            {land_lat:.4f}, {land_lon:.4f}
        </div>
        """,
        max_width=250,
    )

    Marker(
        location=[land_lat, land_lon],
        popup=target_popup,
        icon=Icon(color="red", icon="star", prefix="fa"),
    ).add_to(m)

    # Add competitor project markers
    for project, distance in competitors:
        if not project.latitude or not project.longitude:
            continue

        # Determine marker color based on grade
        grade = project.grade_primary or "M"
        marker_color = GRADE_COLORS.get(grade, "gray")

        # Build popup content
        developer_name = project.developer.name_en if project.developer else "N/A"
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4 style="margin: 0; color: {marker_color};">{project.name}</h4>
            <hr style="margin: 5px 0;">
            <table style="width: 100%; font-size: 12px;">
                <tr>
                    <td><b>Grade:</b></td>
                    <td>{grade}</td>
                </tr>
                <tr>
                    <td><b>Distance:</b></td>
                    <td>{distance:.2f} km</td>
                </tr>
                <tr>
                    <td><b>Units:</b></td>
                    <td>{project.total_units:,} units</td>
                </tr>
                <tr>
                    <td><b>Status:</b></td>
                    <td>{project.status}</td>
                </tr>
                <tr>
                    <td><b>Developer:</b></td>
                    <td>{developer_name}</td>
                </tr>
            </table>
        </div>
        """

        competitor_popup = folium.Popup(popup_html, max_width=300)

        Marker(
            location=[project.latitude, project.longitude],
            popup=competitor_popup,
            icon=Icon(color=marker_color, icon="building", prefix="fa"),
        ).add_to(m)

    # Return HTML string
    return m._repr_html_()


def save_map_to_file(
    html_content: str,
    file_path: str,
) -> bool:
    """Save map HTML content to file.

    Args:
        html_content: HTML string from create_competitor_map()
        file_path: Output file path (should end with .html)

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            # Wrap in full HTML document
            full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Land Review - Competitor Location Map</title>
</head>
<body style="margin: 0; padding: 0;">
    {html_content}
</body>
</html>
"""
            f.write(full_html)
        return True
    except Exception as e:
        print(f"Error saving map: {e}")
        return False


def embed_map_in_markdown(html_content: str) -> str:
    """Embed map HTML in markdown format.

    Args:
        html_content: HTML string from create_competitor_map()

    Returns:
        Markdown string with embedded HTML iframe
    """
    return f"""
### Competitor Location Map

<details>
<summary>Click to view interactive map</summary>

{html_content}

</details>

**Map Legend:**
- 🎯 Red Star: Target land location
- 🏢 Building Icons: Competitor projects (color-coded by grade)
- Circles: Distance radii (Green=1km, Blue=3km, Red=5km)
- Click on markers for project details
"""
