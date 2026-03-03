"""Vietnamese price, area, and name parsers for scraped real estate data."""

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Price Parsing
# ---------------------------------------------------------------------------

# Pattern: "2.5 tỷ", "2,5 tỷ", "2.5 ty", "800 triệu", "800 trieu"
_PRICE_TY_PATTERN = re.compile(
    r"([\d.,]+)\s*(?:tỷ|ty|tỉ|ti)\b", re.IGNORECASE
)
_PRICE_TRIEU_PATTERN = re.compile(
    r"([\d.,]+)\s*(?:triệu|trieu|tr)\b", re.IGNORECASE
)
# Price per m2 pattern: "45 triệu/m²", "45tr/m2"
_PRICE_PER_SQM_PATTERN = re.compile(
    r"([\d.,]+)\s*(?:triệu|trieu|tr)\s*/\s*m[²2]", re.IGNORECASE
)
# Bare number (assumed VND if large enough)
_BARE_NUMBER_PATTERN = re.compile(r"^[\d.,]+$")


def _parse_number(s: str) -> float:
    """Parse a Vietnamese-formatted number (dots for thousands, commas for decimals)."""
    s = s.strip()
    # If both . and , exist, the last one is the decimal separator
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            # Comma is decimal: 2.500,5 → 2500.5
            s = s.replace(".", "").replace(",", ".")
        else:
            # Dot is decimal: 2,500.5 → 2500.5
            s = s.replace(",", "")
    elif "," in s:
        # Could be decimal separator (2,5) or thousands (2,500)
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(",", ".")  # Decimal: 2,5 → 2.5
        else:
            s = s.replace(",", "")  # Thousands: 2,500 → 2500
    elif "." in s:
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) <= 2:
            pass  # Already decimal: 2.5
        elif len(parts) > 2:
            # Multiple dots = thousands separator: 2.500.000 → 2500000
            s = s.replace(".", "")

    return float(s)


def parse_price_vnd(text: str) -> Optional[float]:
    """Parse a Vietnamese price string to VND.

    Examples:
        "2.5 tỷ"   → 2_500_000_000
        "800 triệu" → 800_000_000
        "45 triệu/m²" → 45_000_000  (total, not per sqm)
    """
    if not text:
        return None

    text = text.strip()

    # Try "X tỷ" (billion VND)
    match = _PRICE_TY_PATTERN.search(text)
    if match:
        value = _parse_number(match.group(1))
        # Check for additional "X triệu" after tỷ: "2 tỷ 500 triệu"
        remainder = text[match.end():]
        trieu_match = _PRICE_TRIEU_PATTERN.search(remainder)
        if trieu_match:
            value += _parse_number(trieu_match.group(1)) / 1000
        return value * 1_000_000_000

    # Try "X triệu" (million VND)
    match = _PRICE_TRIEU_PATTERN.search(text)
    if match:
        value = _parse_number(match.group(1))
        return value * 1_000_000

    # Try bare large number (> 1M assumed VND)
    cleaned = re.sub(r"[^\d.,]", "", text)
    if cleaned and _BARE_NUMBER_PATTERN.match(cleaned):
        value = _parse_number(cleaned)
        if value >= 1_000_000:
            return value

    return None


def parse_price_per_sqm(text: str) -> Optional[float]:
    """Parse a price-per-sqm string to VND/m².

    Examples:
        "45 triệu/m²" → 45_000_000
        "120 tr/m2"    → 120_000_000
    """
    if not text:
        return None

    match = _PRICE_PER_SQM_PATTERN.search(text)
    if match:
        value = _parse_number(match.group(1))
        return value * 1_000_000

    return None


# ---------------------------------------------------------------------------
# Area Parsing
# ---------------------------------------------------------------------------

_AREA_PATTERN = re.compile(
    r"([\d.,]+)\s*m[²2]?", re.IGNORECASE
)


def parse_area_sqm(text: str) -> Optional[float]:
    """Parse area string to square meters.

    Examples:
        "65 m²" → 65.0
        "85.5 m2" → 85.5
        "120m²" → 120.0
    """
    if not text:
        return None

    match = _AREA_PATTERN.search(text)
    if match:
        value = _parse_number(match.group(1))
        if 5 <= value <= 10_000:  # Reasonable sqm range
            return value

    return None


# ---------------------------------------------------------------------------
# Name Parsing
# ---------------------------------------------------------------------------

_PROJECT_PREFIXES = re.compile(
    r"^(?:Dự\s+[Áá]n|Du\s+an|Căn\s+hộ|Can\s+ho|Chung\s+cư|Chung\s+cu)\s+",
    re.IGNORECASE,
)


def clean_project_name(name: str) -> str:
    """Clean a project name by stripping common Vietnamese prefixes.

    Examples:
        "Dự án Vinhomes Grand Park" → "Vinhomes Grand Park"
        "Căn hộ The Infiniti" → "The Infiniti"
    """
    if not name:
        return name
    name = name.strip()
    name = _PROJECT_PREFIXES.sub("", name)
    return name.strip()


def extract_slug_from_url(url: str) -> Optional[str]:
    """Extract the project slug from a BDS URL.

    Example:
        "https://batdongsan.com.vn/du-an/vinhomes-grand-park" → "vinhomes-grand-park"
    """
    if not url:
        return None
    match = re.search(r"/du-an/([\w-]+)", url)
    if match:
        return match.group(1)
    return None


# ---------------------------------------------------------------------------
# Office Rent Parsing
# ---------------------------------------------------------------------------

# VND/m²/month patterns:
# "350 nghìn/m²/tháng", "350.000đ/m²/tháng", "350k/m2/thang"
_RENT_NGHIN_PER_SQM = re.compile(
    r"([\d.,]+)\s*(?:nghìn|ngan|nghin|k)\s*/\s*m[²2]", re.IGNORECASE
)
_RENT_DONG_PER_SQM = re.compile(
    r"([\d.,]+)\s*(?:đ|d|vnd)?\s*/\s*m[²2]", re.IGNORECASE
)
_RENT_TRIEU_PER_SQM = re.compile(
    r"([\d.,]+)\s*(?:triệu|trieu|tr)\s*/\s*m[²2]", re.IGNORECASE
)

# USD/m²/month patterns:
# "$20/m²/tháng", "20 USD/m²/tháng", "20usd/m2"
_RENT_USD_PER_SQM = re.compile(
    r"(?:\$|USD)\s*([\d.,]+)\s*/\s*m[²2]|"
    r"([\d.,]+)\s*(?:USD|usd|dollar)\s*/\s*m[²2]",
    re.IGNORECASE,
)

# Total monthly rent (need area to compute per-m²):
# "100 triệu/tháng", "50tr/tháng"
_RENT_TOTAL_TRIEU = re.compile(
    r"([\d.,]+)\s*(?:triệu|trieu|tr)\s*/\s*(?:tháng|thang|th)\b", re.IGNORECASE
)
_RENT_TOTAL_NGHIN = re.compile(
    r"([\d.,]+)\s*(?:nghìn|ngan|nghin|k)\s*/\s*(?:tháng|thang|th)\b", re.IGNORECASE
)


def parse_rent_vnd_per_m2_month(text: str, area_m2: float | None = None) -> float | None:
    """Parse office rent text to VND/m²/month.

    Examples:
        "350 nghìn/m²/tháng"   → 350_000
        "350.000đ/m²/tháng"    → 350_000
        "5 triệu/m²/tháng"     → 5_000_000
        "100 triệu/tháng" (area_m2=200) → 500_000  (total÷area)
    """
    if not text:
        return None

    # 1. nghìn/m² pattern (most common for offices)
    m = _RENT_NGHIN_PER_SQM.search(text)
    if m:
        return _parse_number(m.group(1)) * 1_000

    # 2. triệu/m² pattern
    m = _RENT_TRIEU_PER_SQM.search(text)
    if m:
        return _parse_number(m.group(1)) * 1_000_000

    # 3. Bare đ or VND number per m² (e.g. "350.000đ/m²")
    m = _RENT_DONG_PER_SQM.search(text)
    if m:
        val = _parse_number(m.group(1))
        # Sanity: VND/m²/month for offices is typically 100k–5M
        if 10_000 <= val <= 10_000_000:
            return val

    # 4. Total monthly rent → divide by area
    m_total = _RENT_TOTAL_TRIEU.search(text)
    if m_total and area_m2 and area_m2 > 0:
        total_vnd = _parse_number(m_total.group(1)) * 1_000_000
        return total_vnd / area_m2

    m_total = _RENT_TOTAL_NGHIN.search(text)
    if m_total and area_m2 and area_m2 > 0:
        total_vnd = _parse_number(m_total.group(1)) * 1_000
        return total_vnd / area_m2

    return None


def parse_rent_usd_per_m2_month(text: str) -> float | None:
    """Parse office rent text to USD/m²/month.

    Examples:
        "$20/m²/tháng"    → 20.0
        "20 USD/m²/tháng" → 20.0
        "25usd/m2"        → 25.0
    """
    if not text:
        return None

    m = _RENT_USD_PER_SQM.search(text)
    if m:
        raw = m.group(1) or m.group(2)
        val = _parse_number(raw)
        # Sanity: USD/m²/month typically $5–$200
        if 5 <= val <= 200:
            return val

    return None


def parse_office_floor(text: str) -> str | None:
    """Extract floor number/range from office listing text.

    Examples:
        "Tầng 5" → "5"
        "Tầng 3-5" → "3-5"
        "Tầng trệt" → "G"
    """
    if not text:
        return None
    text = text.strip()
    if re.search(r"trệt|tret|ground", text, re.IGNORECASE):
        return "G"
    m = re.search(r"[Tt]ầng\s*([\d]+-[\d]+|\d+)", text)
    if m:
        return m.group(1)
    m = re.search(r"(\d+)", text)
    if m:
        return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Integer Parsing
# ---------------------------------------------------------------------------

_INT_PATTERN = re.compile(r"(\d+)")


def parse_int_from_text(text: str) -> Optional[int]:
    """Extract first integer from text.

    Examples:
        "3 phòng ngủ" → 3
        "2 toilet" → 2
    """
    if not text:
        return None
    match = _INT_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return None
