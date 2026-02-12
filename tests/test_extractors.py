"""Tests for the data extraction pipeline."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.extractors.base_extractor import BaseExtractor
from src.utils.text_parser import (
    PAGE_PATTERN,
    BLOCK_PATTERN,
    FLOOR_FUNCTION_PATTERN,
    UNIT_TYPE_AREA_PATTERN,
    ABSORPTION_PATTERN,
    extract_blocks,
    extract_unit_types,
    extract_absorption,
    extract_facilities,
    extract_access_control,
)


# ---------------------------------------------------------------------------
# Text fixtures (real snippets from source files)
# ---------------------------------------------------------------------------

CASESTUDY_SNIPPET = """--- Page 4 ---
BLOCK B – 6F:
1-6F: Commercial
and community
01 AVA CENTER
1
No. of Units
845
Launching
/Handover
2025-Q4 / 2027-Q1
Primary Price (USD)
Access control
-
Open type
-
Checking at lobby,
parking
Nam Tu Liem, Ha Noi
1
BLOCK A – 40F:
1F: Shophouse
2F: Shophouse + Officetel
3F: Offictel + Facilities
4-40F: Officetel + Apt

--- Page 5 ---
02 VISTA VERDE
Total No. of Units
1,152
Launching /
Handover
Q3-2014 / Q4-2017
Primary Price (USD)
1,502
Access control
- Site gated
- 3 check-point: Main gate,
sub-gate, lobby
"""

MARKET_UNIT_SNIPPET = """Unit Sizes (m2):
  1BR: 51.9-54.8m2
  2BR: 77.5-80.5m2
  2.5BR: 76.8m2
  3BR: 98.4-110m2
  4BR: 128.5-153.3m2
  Duplex: 75.9-128.9m2
"""

SALES_STATUS_SNIPPET = """Sale status: Sold 97% (809/836 units) in 3 weeks"""

BLOCK_SNIPPET = """BLOCK A:
1-3F: Mall
4: Hotel + Facilities
5-7: Hotel
9-27F: Apt
BLOCK B:
1-3F: Mall
4: Hotel + Facilities
5-7: Hotel
9-27F: Apt
"""

FACILITY_SNIPPET = """[Rooftop] Infinity pool, sky bar,
gym (serviced apt), salon/spa
[2F] Gym (Apt), library, restaurant,
meeting room, event room
[13F] Community room (library +
game), lounge, kids room, meeting
room, café, garden
Kindergarten
"""

LANCASTER_SNIPPET = """04 LANCASTER LUMINAIRE
– TOWER 1
1-4F: Mall
5-12F: Service Apt.
13F: Facilities
14-25F: Apt.
26-27F: Penthouse
RF: Facilities
– TOWER 2
1-4F: Mall
5-27F: Office
No. of Units
252
(126 service apt.; 126 apt.)
Primary Price (USD)
2,772
Access control
- Building gated
- Checking points: parking,
lobby
Tower 1
Tower 2
"""


class TestPageSplitting:
    def test_split_pages(self):
        text = "before\n--- Page 1 ---\nPage one content\n--- Page 2 ---\nPage two content"
        pages = {}
        splits = PAGE_PATTERN.split(text)
        for i in range(1, len(splits), 2):
            pages[int(splits[i])] = splits[i + 1].strip()
        assert 1 in pages
        assert 2 in pages
        assert "Page one content" in pages[1]
        assert "Page two content" in pages[2]

    def test_casestudy_pages(self):
        splits = PAGE_PATTERN.split(CASESTUDY_SNIPPET)
        page_nums = [int(splits[i]) for i in range(1, len(splits), 2)]
        assert 4 in page_nums
        assert 5 in page_nums


class TestBlockExtraction:
    def test_block_pattern_basic(self):
        match = BLOCK_PATTERN.search("BLOCK A – 40F:")
        assert match is not None
        assert match.group(1).strip() == "A"
        assert match.group(2) == "40"

    def test_block_pattern_no_floors(self):
        match = BLOCK_PATTERN.search("BLOCK B:")
        assert match is not None
        assert match.group(1).strip() == "B"
        assert match.group(2) is None

    def test_tower_pattern(self):
        match = BLOCK_PATTERN.search("Tower 1\n")
        assert match is not None
        assert match.group(1).strip() == "1"

    def test_extract_blocks_multiple(self):
        blocks = extract_blocks(BLOCK_SNIPPET)
        names = [b["block_name"] for b in blocks]
        assert "A" in names
        assert "B" in names

    def test_extract_blocks_with_floors(self):
        blocks = extract_blocks("BLOCK A – 40F:\n1F: Shophouse\n2-4F: Mall")
        assert len(blocks) >= 1
        assert blocks[0]["floors"] == 40


class TestFloorFunctionExtraction:
    def test_single_floor(self):
        match = FLOOR_FUNCTION_PATTERN.search("1F: Shophouse")
        assert match is not None
        assert match.group(1) == "1"
        assert "Shophouse" in match.group(5)

    def test_floor_range(self):
        match = FLOOR_FUNCTION_PATTERN.search("5-12F: Service Apt.")
        assert match is not None
        assert match.group(1) == "5"
        assert match.group(2) == "12"
        assert "Service Apt" in match.group(5)

    def test_floor_with_ampersand(self):
        match = FLOOR_FUNCTION_PATTERN.search("5-19F & 21-39: Apt")
        assert match is not None
        assert match.group(1) == "5"
        assert match.group(2) == "19"


class TestUnitTypeExtraction:
    def test_unit_type_pattern(self):
        match = UNIT_TYPE_AREA_PATTERN.search("1BR: 51.9-54.8m2")
        assert match is not None
        assert match.group(1).strip() == "1BR"
        assert match.group(2) == "51.9"
        assert match.group(3) == "54.8"

    def test_extract_unit_types(self):
        types = extract_unit_types(MARKET_UNIT_SNIPPET)
        type_names = [t["type_name"] for t in types]
        assert "1BR" in type_names or "1 BR" in type_names
        assert "2BR" in type_names or "2 BR" in type_names
        assert "3BR" in type_names or "3 BR" in type_names

    def test_area_midpoint(self):
        types = extract_unit_types("1BR: 50-60m2")
        assert len(types) >= 1
        assert types[0]["area_mid"] == 55.0

    def test_single_area(self):
        types = extract_unit_types("Studio: 49.14m2")
        assert len(types) >= 1
        assert types[0]["area_min"] == 49.14
        assert types[0]["area_max"] == 49.14


class TestAbsorptionExtraction:
    def test_sold_percentage(self):
        result = extract_absorption(SALES_STATUS_SNIPPET)
        assert result is not None
        assert result["rate_pct"] == 97.0
        assert result["sold_units"] == 809
        assert result["total_units"] == 836

    def test_sold_out(self):
        result = extract_absorption("Absorption: Sold out")
        assert result is not None
        assert result["rate_pct"] == 100.0

    def test_no_match(self):
        result = extract_absorption("No sales data available")
        assert result is None


class TestFacilityExtraction:
    def test_extract_facilities(self):
        facilities = extract_facilities(FACILITY_SNIPPET)
        types = [f["facility_type"] for f in facilities]
        assert "pool" in types
        assert "gym" in types
        assert "clubhouse" in types  # community room -> clubhouse
        assert "school" in types  # kindergarten -> school

    def test_facility_dedup(self):
        text = "Swimming pool\nInfinity pool\nSky pool"
        facilities = extract_facilities(text)
        pool_count = sum(1 for f in facilities if f["facility_type"] == "pool")
        assert pool_count == 1  # Deduplicated


class TestAccessControlExtraction:
    def test_building_gated(self):
        result = extract_access_control("Building gated\nChecking points: parking, lobby")
        assert result is not None
        assert result["control_type"] == "building_gated"

    def test_open_type(self):
        result = extract_access_control("Open type\nCheck-point: Elevator")
        assert result is not None
        assert result["control_type"] == "open"

    def test_site_gated(self):
        result = extract_access_control("Site gated\n3 check-point")
        assert result is not None
        assert result["control_type"] == "site_gated"

    def test_no_match(self):
        result = extract_access_control("No access info here")
        assert result is None


class TestBaseExtractor:
    def test_split_by_pages(self):
        with TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source"
            out = Path(tmpdir) / "output"
            src.mkdir()
            out.mkdir()

            # Create a concrete extractor for testing
            class TestExt(BaseExtractor):
                def extract(self):
                    return {}

            ext = TestExt(src, out)
            pages = ext.split_by_pages(CASESTUDY_SNIPPET)
            assert len(pages) == 2
            assert 4 in pages
            assert 5 in pages

    def test_write_json(self):
        with TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source"
            out = Path(tmpdir) / "output"
            src.mkdir()
            out.mkdir()

            class TestExt(BaseExtractor):
                def extract(self):
                    return {}

            ext = TestExt(src, out)
            data = [{"name": "test", "value": 42}]
            path = ext.write_json("test.json", data)
            assert path.exists()

            with open(path) as f:
                loaded = json.load(f)
            assert loaded == data

    def test_add_meta(self):
        class TestExt(BaseExtractor):
            def extract(self):
                return {}

        with TemporaryDirectory() as tmpdir:
            ext = TestExt(Path(tmpdir), Path(tmpdir))
            record = {"name": "test"}
            result = ext.add_meta(record, "source.txt", page=5, confidence=0.9)
            assert "_meta" in result
            assert result["_meta"]["source_file"] == "source.txt"
            assert result["_meta"]["page"] == 5
            assert result["_meta"]["confidence"] == 0.9
