"""Extract price factors, district metrics, and segment summaries from sales_price files."""

import re
from pathlib import Path
from typing import Any, Optional

from src.extractors.base_extractor import BaseExtractor
from src.utils.text_parser import extract_number

PRICE_FILES = [
    "sales_price_pass1.txt",
    "sales_price_pass2.txt",
    "sales_price_pass3.txt",
]

# Factor table headers
FACTOR_INCREASED_HEADER = re.compile(r"FACTORS?_INCREASED\s+PRICE", re.IGNORECASE)
FACTOR_DECREASED_HEADER = re.compile(r"FACTORS?_DECREASED\s+PRICE", re.IGNORECASE)

# Factor columns in order (increase factors)
INCREASE_FACTOR_COLS = [
    "location", "supply_shortage", "construction",
    "urban_planning", "competitive_price", "neighborhood", "other",
]

# Factor columns (decrease factors)
DECREASE_FACTOR_COLS = [
    "old_project", "legal", "bank_loan",
    "oversupply", "management", "other",
]

# City section headers in the price analysis
CITY_SECTION = re.compile(
    r"02\.0[1-6]\s+(HO\s+CHI\s+MINH\s+CITY|BINH\s+DUONG|HA\s+LONG|HAI\s+PHONG|DA\s+NANG)",
    re.IGNORECASE,
)

# District-level price data pattern
DISTRICT_PRICE_PATTERN = re.compile(
    r"(?P<district>[A-Za-z\s]+\d*)\s*:\s*(?P<price>[\d,.]+)\s*(?:USD/m2)?",
)

# Average secondary price by district with change rate
DISTRICT_AVG_PATTERN = re.compile(
    r"(?P<district>D\d+|District\s+\d+|Thu\s+Duc|Binh\s+Thanh|Tan\s+Binh|"
    r"Phu\s+Nhuan|Go\s+Vap|Nha\s+Be|Binh\s+Chanh|Binh\s+Tan|Tan\s+Phu|"
    r"Thuan\s+An|Di\s+An|Thu\s+Dau\s+Mot|Tan\s+Uyen|Ben\s+Cat|"
    r"Hoan\s+Kiem|Ba\s+Dinh|Dong\s+Da|Tay\s+Ho|Cau\s+Giay|"
    r"Long\s+Bien|Nam\s+Tu\s+Liem|Ha\s+Dong|Hoang\s+Mai)"
    r"\s*[-:]?\s*(?P<price>[\d,.]+)\s*(?:USD/m2)?",
    re.IGNORECASE,
)

# Grade proportion pattern
GRADE_PROPORTION_PATTERN = re.compile(
    r"(?P<grade>Affordable|Mid-end|High-end|Luxury|Super[- ]?Luxury)"
    r"\s*(?:\((?P<range>[^)]+)\))?"
    r"\s*[:\s]*(?P<pct>[\d,.]+)\s*%",
    re.IGNORECASE,
)

# Average price increase rate
AVG_INCREASE_PATTERN = re.compile(
    r"(?:Avg\.?\s+)?(?:increase|secondary\s+price\s+increase)\s+(?:rate\s+)?(?:in\s+)?(?:\d{4}-H\d)?\s*:\s*([-\d,.]+)\s*%",
    re.IGNORECASE,
)

# Rate pattern: standalone percentage line like "13.20%" or "-5.77%"
RATE_LINE_PATTERN = re.compile(r"^(-?\d+\.?\d*)\s*%\s*$", re.MULTILINE)


class PricePassExtractor(BaseExtractor):
    """Extract price factors, metrics, and segment summaries from sales price files."""

    def __init__(self, source_dir: Path, output_dir: Path) -> None:
        super().__init__(source_dir, output_dir)

    def extract(self) -> dict[str, int]:
        factors_data: list[dict[str, Any]] = []
        district_metrics: list[dict[str, Any]] = []
        segment_summaries: list[dict[str, Any]] = []

        for filename in PRICE_FILES:
            try:
                text = self.read_source(filename)
            except FileNotFoundError:
                continue

            pages = self.split_by_pages(text)

            # Extract price change factors from pass2
            if "pass2" in filename:
                factors = self._extract_factors(text, filename)
                factors_data.extend(factors)

                metrics = self._extract_district_metrics(text, filename)
                district_metrics.extend(metrics)

            # Extract multi-period district metrics from pass3
            if "pass3" in filename:
                multi_metrics = self._extract_multi_period_district_metrics(
                    text, filename
                )
                district_metrics.extend(multi_metrics)

            # Extract segment summaries from pass1 and pass3
            if "pass1" in filename or "pass3" in filename:
                segments = self._extract_segments(text, filename)
                segment_summaries.extend(segments)

        results: dict[str, int] = {}

        self.write_json("price_factors.json", factors_data)
        results["price_factors.json"] = len(factors_data)

        self.write_json("district_metrics.json", district_metrics)
        results["district_metrics.json"] = len(district_metrics)

        self.write_json("segment_summaries.json", segment_summaries)
        results["segment_summaries.json"] = len(segment_summaries)

        return results

    def _extract_factors(
        self, text: str, filename: str
    ) -> list[dict[str, Any]]:
        """Extract price increase/decrease factor tables.

        The source format is multiline:
            Project Name              (line N)
            13.20%                    (line N+1)
            ü                         (line N+2, one or more checkmark lines)
            ü                         (line N+3)
            Description text          (line N+4, optional multi-line description)
        """
        factors: list[dict[str, Any]] = []

        # Process both increase and decrease sections
        for header_pattern, factor_type, factor_cols in [
            (FACTOR_INCREASED_HEADER, "increase", INCREASE_FACTOR_COLS),
            (FACTOR_DECREASED_HEADER, "decrease", DECREASE_FACTOR_COLS),
        ]:
            for match in header_pattern.finditer(text):
                section_start = match.end()
                # Find next section boundary (skip page breaks within section)
                next_section = re.search(
                    r"FACTORS?_(?:INCREASED|DECREASED)|02\.\d{2}\s+[A-Z]",
                    text[section_start:],
                )
                section_end = section_start + (next_section.start() if next_section else 5000)
                section_text = text[section_start:section_end]

                parsed = self._parse_factor_rows(section_text)
                for item in parsed:
                    # Determine checked factor columns from checkmarks
                    checked = self._detect_checked_factors(
                        item["checks_text"], factor_cols
                    )
                    for factor_cat in checked:
                        record = {
                            "project_name": item["project_name"],
                            "factor_type": factor_type,
                            "factor_category": factor_cat,
                            "rate_pct": item["rate"],
                            "description": item["description"] if item["description"] else None,
                        }
                        self.add_meta(record, filename, confidence=0.8)
                        factors.append(record)

        return factors

    @staticmethod
    def _parse_factor_rows(section_text: str) -> list[dict[str, Any]]:
        """Parse multiline factor table rows.

        Each row spans multiple lines:
        1. Project name (may span 2 lines for long names like "Midtown - (P2) The\\nSymphony")
        2. Rate line: "13.20%" or "-5.77%"
        3. Check marks: one or more lines of "ü"
        4. Description: text lines until the next project name or rate
        """
        rows: list[dict[str, Any]] = []
        lines = section_text.split("\n")

        # Skip the column header lines (Factors, Rate, HoH, (%), column names...)
        # Find where actual data starts by looking for the first rate line
        # after skipping column headers
        skip_words = {
            "factors", "rate", "rate hoh", "hoh", "(%)", "location", "supply",
            "shortage", "construc", "-tion", "urban", "planning", "competit",
            "-ive price", "neighbor", "-hood", "others", "details",
            "old project", "legal", "bank loan", "over", "manage", "-ment",
            "n/a", "market situation",
        }

        i = 0
        # Skip header lines
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.lower() in skip_words:
                i += 1
                continue
            # Check if this could be a rate line
            if re.match(r"^-?\d+\.?\d*\s*%$", line):
                break
            # Check if it's a project name (starts with a capital letter or digit)
            if re.match(r"^[A-Z0-9]", line) and line.lower() not in skip_words:
                break
            i += 1

        # Now parse: find rate lines and work backwards for project name
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Skip known non-data lines
            if line.lower() in skip_words or line == "-":
                i += 1
                continue

            # Skip page breaks
            if re.match(r"---\s*Page\s+\d+\s*---", line):
                i += 1
                continue

            # Look for a project name followed by a rate on the next line(s)
            project_lines: list[str] = []
            rate: Optional[float] = None

            # Collect project name lines.
            # Description text from the previous project may precede the
            # project name, so we accumulate all non-rate lines and only
            # keep the last 1-2 lines as the project name (descriptions
            # from previous projects are discarded).
            candidate_lines: list[str] = []
            while i < len(lines):
                line = lines[i].strip()
                if not line or line == "-":
                    i += 1
                    continue
                if re.match(r"---\s*Page\s+\d+\s*---", line):
                    i += 1
                    continue

                # Is this a rate line?
                rate_match = re.match(r"^(-?\d+\.?\d*)\s*%$", line)
                if rate_match:
                    rate = float(rate_match.group(1))
                    i += 1
                    break

                # Is this a checkmark line? (shouldn't be before rate)
                if re.match(r"^[üûö✓✔]+$", line):
                    break

                if line.lower() not in skip_words:
                    candidate_lines.append(line)
                i += 1

            # The actual project name is the last 1-2 candidate lines.
            # Earlier lines are description overflow from the previous row.
            # A project name starts with uppercase and is typically short.
            if candidate_lines:
                # Work backwards to find the project name start
                name_start = len(candidate_lines) - 1
                if name_start > 0:
                    prev = candidate_lines[name_start - 1]
                    # Include previous line if it looks like part of the name
                    # (starts with uppercase, short, no commas/colons)
                    if (re.match(r"^[A-Z]", prev) and
                            len(prev) < 40 and
                            "," not in prev and
                            ":" not in prev and
                            not any(kw in prev.lower() for kw in [
                                "handover", "degrad", "delay", "legal", "supply",
                                "construction", "newly", "good product", "macro",
                                "whole", "new project", "limited",
                            ])):
                        name_start -= 1

                project_lines = candidate_lines[name_start:]

            if not project_lines or rate is None:
                i += 1
                continue

            project_name = " ".join(project_lines).strip()
            # Clean up common artifacts
            project_name = re.sub(r"\s+", " ", project_name)

            # Filter out intro paragraphs captured as project names
            # Real project names are short (< 60 chars) and don't contain
            # sentence-like patterns
            if (len(project_name) > 60 or
                    "Compared to" in project_name or
                    "secondary price" in project_name.lower() or
                    "Main factors" in project_name):
                continue

            # Collect checkmarks and description
            checks: list[str] = []
            desc_lines: list[str] = []
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                if re.match(r"---\s*Page\s+\d+\s*---", line):
                    i += 1
                    continue

                # Checkmark line
                if re.match(r"^[üûö✓✔N/A]+$", line) or line == "N/A":
                    checks.append(line)
                    i += 1
                    continue

                # Is this the start of a new project or rate?
                if re.match(r"^-?\d+\.?\d*\s*%$", line):
                    break
                # New project name: capital letter start, not a description
                if (re.match(r"^[A-Z][A-Za-z0-9\s\-–&'.()]+$", line) and
                        len(line) > 3 and
                        not any(kw in line.lower() for kw in [
                            "whole", "new project", "limited", "high rental",
                            "urban", "macro", "newly", "supply", "developer",
                            "handover", "degraded", "late", "legal", "construction",
                            "delaying", "competitive",
                        ])):
                    # Peek: is next line a rate?
                    next_i = i + 1
                    while next_i < len(lines) and not lines[next_i].strip():
                        next_i += 1
                    if next_i < len(lines) and re.match(r"^-?\d+\.?\d*\s*%$", lines[next_i].strip()):
                        break

                # Description line
                desc_lines.append(line)
                i += 1

            checks_text = " ".join(checks)
            description = " ".join(desc_lines).strip()

            rows.append({
                "project_name": project_name,
                "rate": rate,
                "checks_text": checks_text,
                "description": description,
            })

        return rows

    def _detect_checked_factors(
        self, checks_text: str, columns: list[str]
    ) -> list[str]:
        """Detect which factor columns have checkmarks.

        The check marks (ü, ✓, etc.) appear in column order.
        If we can't reliably detect columns, return the first column as default.
        """
        # Count check marks
        check_marks = re.findall(r"[üûö✓✔]", checks_text)
        if not check_marks:
            # Try to infer from description keywords
            return self._infer_factors_from_description(checks_text, columns)

        # If we have exactly one check and can match to a keyword in description
        if len(check_marks) == 1:
            inferred = self._infer_factors_from_description(checks_text, columns)
            return inferred if inferred else [columns[0]]

        # Multiple checks - try to map positionally
        # Split by check marks and map to columns
        checked: list[str] = []
        parts = re.split(r"[üûö✓✔]", checks_text)
        for i, _mark in enumerate(check_marks):
            if i < len(columns):
                checked.append(columns[i])

        return checked if checked else [columns[0]]

    @staticmethod
    def _infer_factors_from_description(
        text: str, columns: list[str]
    ) -> list[str]:
        """Infer factor categories from description text."""
        text_lower = text.lower()
        keyword_map = {
            "location": ["location", "metro", "cbd", "riverside", "near"],
            "supply_shortage": ["supply shortage", "shortage", "not many", "few"],
            "construction": ["construction", "bridge", "road", "infrastructure"],
            "urban_planning": ["planning", "urban", "master plan"],
            "competitive_price": ["competitive", "price", "cheaper", "affordable"],
            "neighborhood": ["neighborhood", "facilities", "amenities", "park"],
            "old_project": ["old", "handover.*year", "degraded"],
            "legal": ["legal", "pink book", "license"],
            "bank_loan": ["bank", "loan", "interest"],
            "oversupply": ["oversupply", "over supply"],
            "management": ["management", "operation", "maintain"],
        }
        matched: list[str] = []
        for col in columns:
            if col in keyword_map:
                for kw in keyword_map[col]:
                    if re.search(kw, text_lower):
                        matched.append(col)
                        break
        return matched

    def _extract_district_metrics(
        self, text: str, filename: str
    ) -> list[dict[str, Any]]:
        """Extract district-level average prices and change rates."""
        metrics: list[dict[str, Any]] = []

        # Look for "SECONDARY PRICE INCREASE BY DISTRICT" sections
        sections = re.finditer(
            r"SECONDARY\s+PRICE\s+(?:INCREASE|CHANGE)\s+BY\s+DISTRICT",
            text,
            re.IGNORECASE,
        )

        for section_match in sections:
            start = section_match.end()
            # Get a chunk of text after the header
            chunk = text[start:start + 3000]

            # Detect city context
            city = self._detect_city_context(text[:start])

            # Look for average increase rate
            avg_match = AVG_INCREASE_PATTERN.search(chunk)
            avg_rate = float(avg_match.group(1)) if avg_match else None

            if avg_rate is not None and city:
                record = {
                    "city": city,
                    "metric_type": "avg_price_change_pct",
                    "value_numeric": avg_rate,
                    "value_text": f"Average secondary price increase rate",
                }
                self.add_meta(record, filename, confidence=0.9)
                metrics.append(record)

        # Also extract from specific district data in conclusion tables
        conclusion_pattern = re.compile(
            r"(?:Average\s+Secondary\s+Price\s*\(USD/M2\))\s*\n\s*([\d,.]+)\s+",
            re.IGNORECASE,
        )
        for match in conclusion_pattern.finditer(text):
            price = extract_number(match.group(1))
            if price:
                city = self._detect_city_context(text[:match.start()])
                if city:
                    record = {
                        "city": city,
                        "metric_type": "avg_price",
                        "value_numeric": price,
                        "value_text": f"Average secondary price USD/m2",
                    }
                    self.add_meta(record, filename, confidence=0.85)
                    metrics.append(record)

        return metrics

    def _extract_segments(
        self, text: str, filename: str
    ) -> list[dict[str, Any]]:
        """Extract market segment (grade) distribution summaries.

        The source format has percentages on separate lines followed by segment
        names with price ranges, like:
            37%
            29%
            24%
            10%
            ...
            Affordable
            Mid-end
            High-end
            Luxury
            (~  999 USD/m2)
            (1,000 ~ 1,999 USD/m2)
            (2,000 ~ 3,999 USD/m2)
            (4,000 USD/m2 ~)
        Then per-city breakdowns follow with city names and their percentages.
        """
        summaries: list[dict[str, Any]] = []

        grade_map = {
            "affordable": "A-I",
            "mid-end": "M-I",
            "high-end": "H-I",
            "luxury": "L",
            "super-luxury": "SL",
        }

        # Segment order and price ranges (from source)
        segment_order = ["affordable", "mid-end", "high-end", "luxury"]
        price_ranges = {
            "affordable": "~ 999 USD/m2",
            "mid-end": "1,000 ~ 1,999 USD/m2",
            "high-end": "2,000 ~ 3,999 USD/m2",
            "luxury": "4,000 USD/m2 ~",
        }

        # Find "Project Proportion by grade" section
        proportion_match = re.search(
            r"Project\s+Proportion\s+by\s+grade",
            text,
            re.IGNORECASE,
        )
        if not proportion_match:
            return summaries

        section_start = proportion_match.end()
        # Get text until next major section (01.xx header or page break)
        next_section = re.search(
            r"01\.\d{2}\s+|---\s*Page\s+\d+\s*---",
            text[section_start:],
        )
        section_end = section_start + (next_section.start() if next_section else 2000)
        section_text = text[section_start:section_end]

        # Parse city blocks: city name followed by 4 percentages
        # City names appear as: BINH DUONG, HAI PHONG, HA LONG, HCMC, DA NANG
        city_names_map = {
            "HCMC": "Ho Chi Minh City",
            "HO CHI MINH": "Ho Chi Minh City",
            "BINH DUONG": "Binh Duong",
            "HA LONG": "Ha Long",
            "HAI PHONG": "Hai Phong",
            "DA NANG": "Da Nang",
            "HANOI": "Hanoi",
        }

        lines = [l.strip() for l in section_text.split("\n") if l.strip()]

        # Also extract the overall (national) proportions that appear BEFORE
        # the "Project Proportion by grade" header
        pre_section = text[max(0, proportion_match.start() - 500):proportion_match.start()]
        pre_lines = [l.strip() for l in pre_section.split("\n") if l.strip()]

        # Look for the 4 percentages before segment names
        national_pcts: list[float] = []
        for line in pre_lines:
            pct_match = re.match(r"^(\d+)\s*%$", line)
            if pct_match:
                national_pcts.append(float(pct_match.group(1)))
            elif national_pcts and not pct_match:
                # Reset if we hit non-percentage line and haven't collected 4 yet
                if len(national_pcts) < 4:
                    national_pcts = []

        # Take first 4 percentages as national
        if len(national_pcts) >= 4:
            for i, segment in enumerate(segment_order):
                record = {
                    "city": "National",
                    "grade_code": grade_map[segment],
                    "segment": segment,
                    "proportion_pct": national_pcts[i],
                    "price_range": price_ranges.get(segment),
                }
                self.add_meta(record, filename, confidence=0.85)
                summaries.append(record)

        # Parse per-city data from the section after the header.
        # The PDF chart extraction produces city names on separate lines,
        # then percentage groups. City names appear in chart column order
        # (left to right), and percentage groups follow in the same order.
        # Collect all city names first, then assign percentage groups.
        city_order: list[str] = []
        all_pcts: list[float | None] = []  # None represents "-"
        past_cities = False

        for line in lines:
            line_upper = line.upper().strip()
            if not line_upper:
                continue

            # Check for city name
            matched_city = None
            for key, city_name in city_names_map.items():
                if key == line_upper or (key in line_upper and len(line_upper) < len(key) + 5):
                    matched_city = city_name
                    break

            if matched_city and not past_cities:
                city_order.append(matched_city)
                continue

            # Check for percentage or dash
            pct_match = re.match(r"^(\d+)\s*%$", line)
            if pct_match:
                past_cities = True
                all_pcts.append(float(pct_match.group(1)))
                continue
            if line.strip() == "-":
                past_cities = True
                all_pcts.append(None)
                continue

            # Stop at commentary lines
            if past_cities and re.match(r"^(In |HCMC|Source|01\.)", line):
                break

        # Assign percentage groups to cities (4 values each)
        if city_order and all_pcts:
            idx = 0
            for city_name in city_order:
                if idx + 3 > len(all_pcts):
                    break
                city_pcts: list[float | None] = []
                # Take up to 4 values
                for j in range(4):
                    if idx < len(all_pcts):
                        city_pcts.append(all_pcts[idx])
                        idx += 1
                    else:
                        city_pcts.append(None)

                for i, segment in enumerate(segment_order[:len(city_pcts)]):
                    pct = city_pcts[i]
                    if pct is None:
                        pct = 0.0
                    record = {
                        "city": city_name,
                        "grade_code": grade_map[segment],
                        "segment": segment,
                        "proportion_pct": pct,
                        "price_range": price_ranges.get(segment),
                    }
                    self.add_meta(record, filename, confidence=0.75)
                    summaries.append(record)

        return summaries

    def _extract_multi_period_district_metrics(
        self, text: str, filename: str
    ) -> list[dict[str, Any]]:
        """Extract multi-period district price data from pass3 tables.

        Looks for 'Avg. Secondary Price (USD/m2)' tables with columns
        for multiple half-years (e.g., 2021-H1 through 2024-H1).
        """
        metrics: list[dict[str, Any]] = []

        # Pattern for multi-period price tables
        table_header = re.search(
            r"Avg\.?\s*Secondary\s+Price\s*\(USD/[Mm]2\)",
            text,
            re.IGNORECASE,
        )
        if not table_header:
            return metrics

        start = table_header.end()
        chunk = text[start:start + 5000]

        # Detect city context
        city = self._detect_city_context(text[:start])
        if not city:
            return metrics

        # Look for period headers like "2021-H1", "2021H1", "H1 2021"
        period_pattern = re.compile(r"(20\d{2})\s*[-]?\s*(H[12])", re.IGNORECASE)
        period_matches = list(period_pattern.finditer(chunk[:500]))

        if not period_matches:
            return metrics

        periods = [(int(m.group(1)), m.group(2).upper()) for m in period_matches]

        # Parse district rows: district name followed by numeric values
        lines = chunk.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match district name at start, followed by numbers
            district_row = re.match(
                r"(?P<district>[A-Za-z\s]+(?:\d+)?)\s+"
                r"(?P<values>[\d,.\s-]+)$",
                line,
            )
            if not district_row:
                continue

            district_name = district_row.group("district").strip()
            values_str = district_row.group("values").strip()

            # Parse numeric values
            values = re.findall(r"[\d,]+\.?\d*", values_str)
            if not values:
                continue

            for i, (year, half) in enumerate(periods):
                if i >= len(values):
                    break
                price = extract_number(values[i])
                if price and price > 0:
                    record = {
                        "city": city,
                        "district_name": district_name,
                        "period_year": year,
                        "period_half": half,
                        "metric_type": "avg_secondary_price",
                        "value_numeric": price,
                        "value_text": f"Avg secondary price USD/m2 {year}-{half}",
                    }
                    self.add_meta(record, filename, confidence=0.85)
                    metrics.append(record)

        return metrics

    @staticmethod
    def _detect_city_context(text_before: str) -> Optional[str]:
        """Detect which city section we're in based on preceding text."""
        # Find the last city section header
        city_matches = list(CITY_SECTION.finditer(text_before))
        if city_matches:
            last = city_matches[-1].group(1).upper()
            if "HO CHI MINH" in last or "HCMC" in last:
                return "Ho Chi Minh City"
            if "BINH DUONG" in last:
                return "Binh Duong"
            if "HA LONG" in last:
                return "Ha Long"
            if "HAI PHONG" in last:
                return "Hai Phong"
            if "DA NANG" in last:
                return "Da Nang"

        # Fallback: check for city mentions in recent text
        recent = text_before[-2000:]
        if "HCMC" in recent or "Ho Chi Minh" in recent:
            return "Ho Chi Minh City"
        if "Binh Duong" in recent:
            return "Binh Duong"
        if "Hanoi" in recent or "Ha Noi" in recent:
            return "Hanoi"

        return None
