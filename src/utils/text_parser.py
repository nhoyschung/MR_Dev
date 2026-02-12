"""Helpers for parsing extracted PDF text into structured data."""

import re
from typing import Optional


def extract_number(text: str) -> Optional[float]:
    """Extract the first number from a string, handling commas."""
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def extract_price_vnd(text: str) -> Optional[float]:
    """Extract VND price (in million/m2) from text."""
    patterns = [
        r"([\d,.]+)\s*(?:triệu|trieu|mil|million)\s*/?\s*m2",
        r"([\d,.]+)\s*tr/m2",
        r"([\d,.]+)\s*VND\s*mil/m2",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return extract_number(match.group(1))
    return None


def extract_price_usd(text: str) -> Optional[float]:
    """Extract USD price per m2 from text."""
    patterns = [
        r"\$?\s*([\d,.]+)\s*(?:USD|usd)\s*/?\s*m2",
        r"([\d,.]+)\s*USD/m2",
        r"\$([\d,.]+)/m2",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return extract_number(match.group(1))
    return None


def extract_unit_count(text: str) -> Optional[int]:
    """Extract unit count from text like '1,200 units'."""
    match = re.search(r"([\d,]+)\s*(?:units?|căn|can)", text, re.IGNORECASE)
    if match:
        val = extract_number(match.group(1))
        return int(val) if val else None
    return None


def extract_area_m2(text: str) -> Optional[float]:
    """Extract area in m2 from text."""
    match = re.search(r"([\d,.]+)\s*(?:m2|m²|sqm)", text, re.IGNORECASE)
    if match:
        return extract_number(match.group(1))
    return None


def extract_percentage(text: str) -> Optional[float]:
    """Extract percentage value from text."""
    match = re.search(r"([\d,.]+)\s*%", text)
    if match:
        return extract_number(match.group(1))
    return None


def normalize_district_name(name: str) -> str:
    """Normalize Vietnamese district names for matching.

    Handles variations like 'Q.1', 'Quan 1', 'District 1', 'Q1'.
    """
    name = name.strip()
    # Normalize "Q." or "Quan" prefix
    name = re.sub(r"^(?:Q\.|Quan|Quận)\s*", "District ", name, flags=re.IGNORECASE)
    # Normalize "TP." prefix for Thu Duc etc.
    name = re.sub(r"^(?:TP\.|Thanh pho|Thành phố)\s*", "", name, flags=re.IGNORECASE)
    return name.strip()


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize line endings."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sections(text: str, heading_pattern: str = r"^#{1,3}\s+") -> dict[str, str]:
    """Split text into sections by markdown-style headings."""
    sections: dict[str, str] = {}
    current_heading = ""
    current_content: list[str] = []

    for line in text.split("\n"):
        if re.match(heading_pattern, line):
            if current_heading:
                sections[current_heading] = "\n".join(current_content).strip()
            current_heading = re.sub(heading_pattern, "", line).strip()
            current_content = []
        else:
            current_content.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_content).strip()

    return sections


# ---------------------------------------------------------------------------
# Compiled Patterns for Data Extraction Pipeline
# ---------------------------------------------------------------------------

PAGE_PATTERN = re.compile(r"^---\s*Page\s+(\d+)\s*---$", re.MULTILINE)

# Matches: BLOCK A – 40F, BLOCK B, Block A, BLOCK TOCHI, GIO DONG 1, WEST 1
BLOCK_PATTERN = re.compile(
    r"(?:BLOCK|Block|Tower|TOWER)\s+([A-Z0-9][A-Z0-9\s]*?)(?:\s*[-–—:]\s*(\d+)F)?(?=\s*[:\n]|$)",
    re.IGNORECASE,
)

# Matches: 1F: Shophouse, 2-4F: Mall + Officetel, 5-19F & 21-39: Apt
FLOOR_FUNCTION_PATTERN = re.compile(
    r"(\d+)(?:\s*[-–]\s*(\d+))?F\s*(?:&\s*(\d+)(?:\s*[-–]\s*(\d+))?)?\s*:\s*(.+)",
)

# Matches: 1BR: 56.6 - 61, Studio: 49.14, 2.5BR: 76.8, PH DL: 143.9 - 372.2
UNIT_TYPE_AREA_PATTERN = re.compile(
    r"([\d.]*\s*BR|Studio|Penthouse|PH(?:\s+DL)?|Officetel|Shophouse|Duplex|DL|SH|SA|Condotel)"
    r"\s*[:/]?\s*([\d,.]+)\s*(?:[-–]\s*([\d,.]+))?\s*(?:m2|m²)?",
    re.IGNORECASE,
)

# Matches: Sold 97% (809/836 units), Sold out, Sold 99.5% (613/616 units) in 3 weeks
ABSORPTION_PATTERN = re.compile(
    r"Sold\s+(?:out|(\d+\.?\d*)\s*%\s*\((\d[\d,]*)\s*/\s*(\d[\d,]*)\s*units?\))",
    re.IGNORECASE,
)

# Facility keywords mapped to facility_type categories
FACILITY_KEYWORDS: dict[str, list[str]] = {
    "pool": ["pool", "swimming", "lagoon", "infinity pool", "sky pool"],
    "gym": ["gym", "fitness", "sky gym"],
    "park": ["garden", "park", "green", "landscape", "lawn"],
    "commercial": ["mall", "retail", "shophouse", "commercial", "shop", "market",
                    "café", "cafe", "restaurant", "bar", "sky bar", "skybar"],
    "school": ["school", "kindergarten", "kindergarden", "education"],
    "playground": ["playground", "kids", "children", "kid's", "game room",
                   "pickleball", "pickle ball", "basketball", "sport"],
    "clubhouse": ["community room", "clubhouse", "lounge", "meeting room",
                   "library", "co-working", "coworking", "event room", "salon", "spa"],
    "security": ["security", "guard", "check-point", "checkpoint", "cctv", "guard house"],
    "parking": ["parking", "basement", "EV charge"],
}

# Access control type detection
ACCESS_CONTROL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("building_gated", re.compile(r"Building\s+gated", re.IGNORECASE)),
    ("site_gated", re.compile(r"Site\s+gated", re.IGNORECASE)),
    ("fence_gated", re.compile(r"Fence\s+gated", re.IGNORECASE)),
    ("gated", re.compile(r"Gated\s+type", re.IGNORECASE)),
    ("open", re.compile(r"Open(?:ed)?\s+type", re.IGNORECASE)),
]

# Price factor table detection
FACTOR_INCREASED_PATTERN = re.compile(r"FACTORS?_INCREASED\s+PRICE", re.IGNORECASE)
FACTOR_DECREASED_PATTERN = re.compile(r"FACTORS?_DECREASED\s+PRICE", re.IGNORECASE)

# Factor check mark in tables
FACTOR_CHECK_PATTERN = re.compile(r"[üûö✓✗✔⊠]")

# Secondary price increase by district
PRICE_INCREASE_RATE_PATTERN = re.compile(
    r"([\d,.]+)\s*%",
)

# Project header in casestudy: "01 AVA CENTER", "02 VISTA VERDE", etc.
CASESTUDY_PROJECT_PATTERN = re.compile(
    r"^(?P<number>\d{2})\s+(?P<name>[A-Z][A-Z\s&\-–'.()0-9]+?)(?:\s*[-–]\s*.+)?$",
    re.MULTILINE,
)


def extract_blocks(text: str) -> list[dict[str, Optional[str | int]]]:
    """Extract block/tower info from project text.

    Returns list of {block_name, floors, floor_functions}.
    """
    blocks: list[dict[str, Optional[str | int]]] = []
    seen_names: set[str] = set()

    for match in BLOCK_PATTERN.finditer(text):
        name = match.group(1).strip()
        floors = int(match.group(2)) if match.group(2) else None

        if name in seen_names:
            continue
        seen_names.add(name)

        # Try to extract floor functions following this block header
        start = match.end()
        # Get text until the next block header or end of section
        next_block = BLOCK_PATTERN.search(text, start)
        end = next_block.start() if next_block else min(start + 500, len(text))
        block_text = text[start:end]

        floor_funcs = []
        for fm in FLOOR_FUNCTION_PATTERN.finditer(block_text):
            floor_from = int(fm.group(1))
            floor_to = int(fm.group(2)) if fm.group(2) else floor_from
            function = fm.group(5).strip()
            floor_funcs.append(f"{floor_from}-{floor_to}F: {function}" if floor_to != floor_from else f"{floor_from}F: {function}")

        blocks.append({
            "block_name": name,
            "floors": floors,
            "floor_functions": floor_funcs if floor_funcs else None,
        })

    return blocks


def extract_unit_types(text: str) -> list[dict[str, Optional[str | float]]]:
    """Extract unit type and area ranges from text.

    Returns list of {type_name, area_min, area_max, area_mid}.
    """
    types: list[dict[str, Optional[str | float]]] = []
    seen: set[str] = set()

    for match in UNIT_TYPE_AREA_PATTERN.finditer(text):
        type_name = match.group(1).strip()
        area_min_str = match.group(2).replace(",", "")
        area_max_str = match.group(3).replace(",", "") if match.group(3) else None

        try:
            area_min = float(area_min_str)
        except ValueError:
            continue

        area_max = float(area_max_str) if area_max_str else area_min

        key = f"{type_name}:{area_min}"
        if key in seen:
            continue
        seen.add(key)

        types.append({
            "type_name": type_name,
            "area_min": area_min,
            "area_max": area_max,
            "area_mid": round((area_min + area_max) / 2, 1),
        })

    return types


def extract_absorption(text: str) -> Optional[dict[str, Optional[float | int]]]:
    """Extract sales/absorption data from text.

    Returns {rate_pct, sold_units, total_units} or None.
    """
    match = ABSORPTION_PATTERN.search(text)
    if not match:
        # Check for "Sold out" or "100%"
        if re.search(r"Sold\s+out|100\s*%", text, re.IGNORECASE):
            return {"rate_pct": 100.0, "sold_units": None, "total_units": None}
        return None

    rate = float(match.group(1)) if match.group(1) else 100.0
    sold = int(match.group(2).replace(",", "")) if match.group(2) else None
    total = int(match.group(3).replace(",", "")) if match.group(3) else None

    return {"rate_pct": rate, "sold_units": sold, "total_units": total}


def extract_facilities(text: str) -> list[dict[str, str]]:
    """Extract facility mentions from text using keyword matching.

    Returns list of {facility_type, description}.
    """
    facilities: list[dict[str, str]] = []
    text_lower = text.lower()
    seen_types: set[str] = set()

    for facility_type, keywords in FACILITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                if facility_type not in seen_types:
                    # Find the original context line
                    for line in text.split("\n"):
                        if keyword.lower() in line.lower():
                            facilities.append({
                                "facility_type": facility_type,
                                "description": line.strip(),
                            })
                            seen_types.add(facility_type)
                            break
                    else:
                        facilities.append({
                            "facility_type": facility_type,
                            "description": keyword,
                        })
                        seen_types.add(facility_type)
                break

    return facilities


def extract_access_control(text: str) -> Optional[dict[str, str]]:
    """Detect access control type from text.

    Returns {control_type, description} or None.
    """
    for control_type, pattern in ACCESS_CONTROL_PATTERNS:
        match = pattern.search(text)
        if match:
            # Grab surrounding context for description
            start = max(0, match.start() - 10)
            end = min(len(text), match.end() + 100)
            context = text[start:end].replace("\n", " ").strip()
            return {"control_type": control_type, "description": context}
    return None
