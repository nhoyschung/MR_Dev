"""Extract unit types and sales statuses from market analysis pass files."""

import re
from pathlib import Path
from typing import Any, Optional

from src.extractors.base_extractor import BaseExtractor
from src.utils.text_parser import (
    extract_unit_types,
    extract_absorption,
    extract_facilities,
    extract_number,
)

# Market pass2 files contain detailed project profiles
PASS2_FILES: dict[str, dict[str, str | int]] = {
    "hcmc_pass2.txt": {"city": "Ho Chi Minh City", "city_id": 1},
    "hanoi_pass2.txt": {"city": "Hanoi", "city_id": 2},
    "binh_duong_pass2.txt": {"city": "Binh Duong", "city_id": 3},
}

# Project detail header in pass2: starts with project name, followed by structured fields
PROJECT_DETAIL_PATTERN = re.compile(
    r"(?:Project\s+Name\s*:\s*(?P<name>.+)|"
    r"^(?P<num>\d+)\.\s+(?P<name2>[A-Z][A-Z0-9\s&\-–'.()]+))",
    re.MULTILINE,
)

# Structured fields in project profiles
DEVELOPER_PATTERN = re.compile(r"Developer\s*:\s*(.+)", re.IGNORECASE)
LOCATION_PATTERN = re.compile(r"Location\s*:\s*(.+)", re.IGNORECASE)
BLOCKS_FLOORS_PATTERN = re.compile(
    r"Blocks?/Floors?\s*:\s*(\d+)\s*[B/]\s*(\d+)[-–]?(\d+)?F?",
    re.IGNORECASE,
)
UNITS_PATTERN = re.compile(
    r"No\.\s+of\s+Units\s*:\s*([\d,]+)",
    re.IGNORECASE,
)
LAUNCH_PATTERN = re.compile(
    r"Launch/Handover\s*:\s*(.+)",
    re.IGNORECASE,
)
AVG_PRICE_PATTERN = re.compile(
    r"Avg\.?\s+(?:primary\s+)?price\s*\(?USD/m2\)?\s*:\s*([\d,.]+)",
    re.IGNORECASE,
)
UNIT_SIZE_SECTION = re.compile(
    r"Unit\s+Sizes?\s*\(?m2\)?\s*:\s*\n?((?:\s*[\d.]*\s*BR.*\n?)+)",
    re.IGNORECASE,
)
# "Sale status" appears on its own line; absorption data follows on subsequent lines.
# We capture up to 3 lines after the header to handle multi-line sale descriptions.
SALE_STATUS_PATTERN = re.compile(
    r"Sale\s+status\s*:?\s*\n((?:.*\n?){1,3})",
    re.IGNORECASE,
)

# Simpler pattern for project name in pages without "Project Name:" format
PAGE_PROJECT_NAME = re.compile(
    r"^(?:(?:\d+\.?\s+)?(?:THE\s+|A&T\s+)?[A-Z][A-Z\s\-–&'.0-9]+)"
    r"(?:\s*[-–]\s*\(?P\d+\)?.*)?$",
    re.MULTILINE,
)


class MarketPassExtractor(BaseExtractor):
    """Extract unit types and sales data from market analysis pass2 files."""

    def __init__(self, source_dir: Path, output_dir: Path) -> None:
        super().__init__(source_dir, output_dir)

    def extract(self) -> dict[str, int]:
        unit_types_data: list[dict[str, Any]] = []
        sales_status_data: list[dict[str, Any]] = []
        facilities_data: list[dict[str, Any]] = []

        for filename, city_info in PASS2_FILES.items():
            try:
                text = self.read_source(filename)
            except FileNotFoundError:
                continue

            pages = self.split_by_pages(text)
            city_name = city_info["city"]

            for page_num, page_content in pages.items():
                project_name = self._detect_project_name(page_content)
                if not project_name:
                    continue

                # Extract unit types from unit size sections
                utypes = extract_unit_types(page_content)
                for ut in utypes:
                    record = {
                        "project_name": project_name,
                        "city": city_name,
                        "type_name": ut["type_name"],
                        "area_min": ut["area_min"],
                        "area_max": ut["area_max"],
                        "gross_area_m2": ut["area_mid"],
                        "typical_layout_description": f"{ut['area_min']}-{ut['area_max']}m2" if ut["area_min"] != ut["area_max"] else f"{ut['area_min']}m2",
                    }
                    self.add_meta(record, filename, page=page_num, confidence=0.85)
                    unit_types_data.append(record)

                # Extract sales status (absorption)
                sale_match = SALE_STATUS_PATTERN.search(page_content)
                if sale_match:
                    # Join captured lines and try to find absorption data
                    sale_text = sale_match.group(1).strip()
                    absorption = extract_absorption(sale_text)
                    if absorption:
                        total_units = self._extract_total_units(page_content)
                        record = {
                            "project_name": project_name,
                            "city": city_name,
                            "sales_rate_pct": absorption["rate_pct"],
                            "sold_units": absorption["sold_units"],
                            "launched_units": absorption["total_units"] or total_units,
                            "available_units": (
                                (absorption["total_units"] or 0) - (absorption["sold_units"] or 0)
                                if absorption["total_units"] and absorption["sold_units"]
                                else None
                            ),
                            "sale_description": sale_text.strip(),
                        }
                        self.add_meta(record, filename, page=page_num, confidence=0.85)
                        sales_status_data.append(record)

                # Extract facilities
                facs = extract_facilities(page_content)
                for fac in facs:
                    record = {
                        "project_name": project_name,
                        "city": city_name,
                        "facility_type": fac["facility_type"],
                        "description": fac["description"],
                    }
                    self.add_meta(record, filename, page=page_num, confidence=0.7)
                    facilities_data.append(record)

        results: dict[str, int] = {}

        self.write_json("market_unit_types.json", unit_types_data)
        results["market_unit_types.json"] = len(unit_types_data)

        self.write_json("market_sales_statuses.json", sales_status_data)
        results["market_sales_statuses.json"] = len(sales_status_data)

        self.write_json("market_facilities.json", facilities_data)
        results["market_facilities.json"] = len(facilities_data)

        return results

    def _detect_project_name(self, page_content: str) -> Optional[str]:
        """Try to detect a project name from page content."""
        # Method 1: "Project Name: XXX"
        match = re.search(r"Project\s+Name\s*:\s*(.+)", page_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Method 2: Numbered project header at top of page
        lines = [l.strip() for l in page_content.split("\n") if l.strip()]
        # Skip common non-project lines
        skip_patterns = [
            "National Housing",
            "MARKET ANALYSIS",
            "MARKET OVERVIEW",
            "CONTENTS",
            "PART ",
            "Source:",
            "CONCLUSION",
            "HCMC",
            "HANOI",
            "BINH DUONG",
            "PROJECT SUMMARY",
            "PROJECT DETAIL",
            "DEVELOPMENT PRODUCT",
            "PRODUCT DEVELOPMENT",
            "LOCATION MAP",
        ]

        for line in lines[:8]:
            if any(s in line for s in skip_patterns):
                continue
            # Check for project-like header
            m = re.match(
                r"^(?:\d+\.?\s+)?([A-Z][A-Z0-9\s\-–&'.()]+)(?:\s*[-–].*)?$",
                line,
            )
            if m and len(m.group(1).strip()) > 3:
                name = m.group(1).strip()
                # Filter out section headers
                if name not in (
                    "SUPPLY", "TRANSACTION", "PRICE", "GRADE", "ZONE",
                    "SUMMARY", "OVERVIEW", "ANALYSIS", "ON SALES",
                    "UPCOMING", "PROJECT DETAIL", "APPENDIX",
                    "PROJECT SUMMARY", "DEVELOPMENT PRODUCT",
                    "PRODUCT DEVELOPMENT", "LOCATION MAP",
                    "SITE PLAN", "FLOOR PLAN", "UNIT MIX",
                ):
                    return name

        return None

    @staticmethod
    def _extract_total_units(text: str) -> Optional[int]:
        match = UNITS_PATTERN.search(text)
        if match:
            val = extract_number(match.group(1))
            return int(val) if val else None
        return None
