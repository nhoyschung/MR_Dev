"""Extract blocks, facilities, and sales points from mixed_use_casestudy_full.txt."""

import re
from pathlib import Path
from typing import Any, Optional

from src.extractors.base_extractor import BaseExtractor
from src.utils.text_parser import (
    BLOCK_PATTERN,
    FLOOR_FUNCTION_PATTERN,
    extract_blocks,
    extract_facilities,
    extract_access_control,
    extract_unit_types,
    extract_absorption,
    extract_number,
    extract_unit_count,
)

SOURCE_FILE = "mixed_use_casestudy_full.txt"

# Project header: "01 AVA CENTER", "09 HAPPY ONE MORRI – (P1) BLOCK TOCHI"
PROJECT_HEADER = re.compile(
    r"^(?P<number>\d{2})\s+(?P<name>[A-Z][A-Z0-9\s&\-–'.]+?)(?:\s*[-–]\s*(?:BUILDING SECTION|APT\b).*)?\s*$",
    re.MULTILINE,
)

# Location line patterns
LOCATION_PATTERN = re.compile(
    r"(?:Nam Tu Liem|Thanh My Loi|Tay Ho|Dong Da|Cau Giay|Thanh Xuan|Dong Anh|"
    r"Thuan An|Di An|Thu Dau Mot|Binh Chanh|Thu Duc|Van Phuc|Dong Hoa|Lang Ha)"
    r"(?:\s*,\s*(?:Ha Noi|HCMC|Binh Duong|BD))?",
    re.IGNORECASE,
)

# No. of Units pattern
UNITS_PATTERN = re.compile(
    r"(?:No\.\s+of\s+Units|Total\s+No\.\s+of\s+Units)\s*\n?\s*([\d,]+)",
    re.IGNORECASE,
)

# Primary price
PRICE_PATTERN = re.compile(
    r"Primary\s+Price\s*\n?\s*\(?USD(?:/m2)?\)?\s*\n?\s*([\d,]+)",
    re.IGNORECASE,
)

# Launch/Handover
LAUNCH_PATTERN = re.compile(
    r"(?:Launching\s*/?\s*Handover|Launch/Handover)\s*\n?\s*(\d{4}[-–Q\d/\s]+)",
    re.IGNORECASE,
)


class CasestudyExtractor(BaseExtractor):
    """Extract structured data from the mixed-use case study report."""

    def __init__(self, source_dir: Path, output_dir: Path) -> None:
        super().__init__(source_dir, output_dir)

    def extract(self) -> dict[str, int]:
        text = self.read_source(SOURCE_FILE)
        pages = self.split_by_pages(text)

        projects = self._merge_project_pages(pages)

        blocks_data: list[dict[str, Any]] = []
        facilities_data: list[dict[str, Any]] = []
        sales_points_data: list[dict[str, Any]] = []
        unit_types_data: list[dict[str, Any]] = []

        for proj in projects:
            name = proj["name"]
            content = proj["content"]
            page = proj["page"]

            # Extract blocks
            blocks = extract_blocks(content)
            for block in blocks:
                record = {
                    "project_name": name,
                    "block_name": block["block_name"],
                    "floors": block["floors"],
                    "floor_functions": block.get("floor_functions"),
                }
                self.add_meta(record, SOURCE_FILE, page=page, confidence=0.85)
                blocks_data.append(record)

            # Extract facilities
            facilities = extract_facilities(content)
            for fac in facilities:
                record = {
                    "project_name": name,
                    "facility_type": fac["facility_type"],
                    "description": fac["description"],
                }
                self.add_meta(record, SOURCE_FILE, page=page, confidence=0.8)
                facilities_data.append(record)

            # Extract access control as sales points
            access = extract_access_control(content)
            if access:
                record = {
                    "project_name": name,
                    "category": "design",
                    "description": f"Access: {access['control_type']} - {access['description']}",
                }
                self.add_meta(record, SOURCE_FILE, page=page, confidence=0.85)
                sales_points_data.append(record)

            # Extract unit types
            utypes = extract_unit_types(content)
            for ut in utypes:
                record = {
                    "project_name": name,
                    "type_name": ut["type_name"],
                    "area_min": ut["area_min"],
                    "area_max": ut["area_max"],
                    "gross_area_m2": ut["area_mid"],
                }
                self.add_meta(record, SOURCE_FILE, page=page, confidence=0.8)
                unit_types_data.append(record)

            # Extract total units and price as additional sales points
            total_units = self._extract_total_units(content)
            price = self._extract_price(content)

            if price:
                record = {
                    "project_name": name,
                    "category": "pricing",
                    "description": f"Primary price: ${price:,.0f} USD/m2",
                }
                self.add_meta(record, SOURCE_FILE, page=page, confidence=0.9)
                sales_points_data.append(record)

            # Extract absorption as sales point
            absorption = extract_absorption(content)
            if absorption and absorption["rate_pct"]:
                desc = f"Sales rate: {absorption['rate_pct']}%"
                if absorption["sold_units"] and absorption["total_units"]:
                    desc += f" ({absorption['sold_units']}/{absorption['total_units']} units)"
                record = {
                    "project_name": name,
                    "category": "pricing",
                    "description": desc,
                }
                self.add_meta(record, SOURCE_FILE, page=page, confidence=0.85)
                sales_points_data.append(record)

        # Write output files
        results: dict[str, int] = {}

        self.write_json("casestudy_blocks.json", blocks_data)
        results["casestudy_blocks.json"] = len(blocks_data)

        self.write_json("casestudy_facilities.json", facilities_data)
        results["casestudy_facilities.json"] = len(facilities_data)

        self.write_json("casestudy_sales_points.json", sales_points_data)
        results["casestudy_sales_points.json"] = len(sales_points_data)

        self.write_json("casestudy_unit_types.json", unit_types_data)
        results["casestudy_unit_types.json"] = len(unit_types_data)

        return results

    def _merge_project_pages(
        self, pages: dict[int, str]
    ) -> list[dict[str, Any]]:
        """Merge consecutive pages that belong to the same project."""
        projects: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for page_num in sorted(pages.keys()):
            content = pages[page_num]
            match = PROJECT_HEADER.search(content)
            if not match:
                # Continuation page — append to last project
                if projects:
                    projects[-1]["content"] += "\n" + content
                continue

            name = match.group("name").strip()
            # Skip "00 SUMMARY" and building section repeats
            if name == "SUMMARY" or name.startswith("00"):
                continue

            # Deduplicate: merge if same project seen before
            if name in seen_names:
                for p in projects:
                    if p["name"] == name:
                        p["content"] += "\n" + content
                        break
                continue

            seen_names.add(name)
            projects.append({
                "number": match.group("number"),
                "name": name,
                "page": page_num,
                "content": content,
            })

        return projects

    @staticmethod
    def _extract_total_units(text: str) -> Optional[int]:
        match = UNITS_PATTERN.search(text)
        if match:
            val = extract_number(match.group(1))
            return int(val) if val else None
        return None

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        match = PRICE_PATTERN.search(text)
        if match:
            return extract_number(match.group(1))
        return None
