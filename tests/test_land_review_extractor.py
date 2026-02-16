"""Tests for land review data extractor."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def extracted_data():
    """Load extracted land review data."""
    data_path = Path(__file__).parent.parent / "data" / "seed" / "extracted" / "land_reviews.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_record_count(extracted_data):
    """Test that 9 records were extracted."""
    assert len(extracted_data) == 9, "Should extract 9 land review records"


def test_required_fields(extracted_data):
    """Test that all records have required fields."""
    required_fields = [
        'report_file',
        'city',
        'district',
        'land_area_ha',
        'development_type',
        'recommended_grade',
        '_meta'
    ]

    for i, record in enumerate(extracted_data, 1):
        for field in required_fields:
            assert field in record, f"Record {i} missing required field: {field}"


def test_total_land_area(extracted_data):
    """Test total land area calculation."""
    total_area = sum(r.get('land_area_ha', 0) for r in extracted_data)
    assert 360 <= total_area <= 375, f"Total area {total_area} ha outside expected range"


def test_city_distribution(extracted_data):
    """Test city distribution."""
    cities = {}
    for record in extracted_data:
        city = record.get('city')
        cities[city] = cities.get(city, 0) + 1

    assert cities.get('Hai Phong') == 5, "Should have 5 Hai Phong sites"
    assert cities.get('Binh Duong') == 3, "Should have 3 Binh Duong sites"
    assert cities.get('Bac Ninh') == 1, "Should have 1 Bac Ninh site"


def test_grade_assignments(extracted_data):
    """Test grade assignments are valid."""
    valid_grades = ['SL', 'L', 'H-I', 'H-II', 'M-I', 'M-II', 'M-III', 'A-I', 'A-II']

    for i, record in enumerate(extracted_data, 1):
        grade = record.get('recommended_grade')
        assert grade in valid_grades, f"Record {i} has invalid grade: {grade}"


def test_development_types(extracted_data):
    """Test development types are valid."""
    valid_types = ['mixed-use', 'residential', 'commercial']

    for i, record in enumerate(extracted_data, 1):
        dev_type = record.get('development_type')
        assert dev_type in valid_types, f"Record {i} has invalid development type: {dev_type}"


def test_price_ranges(extracted_data):
    """Test price benchmarks are reasonable."""
    for i, record in enumerate(extracted_data, 1):
        price = record.get('benchmark_price_usd_m2')
        if price is not None:
            assert 1000 <= price <= 6000, f"Record {i} has unreasonable price: ${price}/m2"


def test_metadata_present(extracted_data):
    """Test metadata is present and valid."""
    for i, record in enumerate(extracted_data, 1):
        meta = record.get('_meta', {})
        assert 'source_file' in meta, f"Record {i} missing _meta.source_file"
        assert 'confidence' in meta, f"Record {i} missing _meta.confidence"
        assert 'extracted_date' in meta, f"Record {i} missing _meta.extracted_date"
        assert meta['confidence'] in ['high', 'medium', 'low'], f"Record {i} has invalid confidence"


def test_bac_ninh_mega_project(extracted_data):
    """Test Bac Ninh 240ha project extraction."""
    bac_ninh = [r for r in extracted_data if r.get('city') == 'Bac Ninh']
    assert len(bac_ninh) == 1, "Should have exactly 1 Bac Ninh record"

    project = bac_ninh[0]
    assert project['land_area_ha'] == 240.0, "Bac Ninh should be 240 ha"
    assert project['development_type'] == 'mixed-use', "Should be mixed-use"
    assert 'Vinhomes Hoa Long' in project.get('competitor_projects', []), "Should list Vinhomes as competitor"


def test_binh_duong_sites(extracted_data):
    """Test Binh Duong 3 sites extraction."""
    bd_sites = [r for r in extracted_data if r.get('city') == 'Binh Duong']
    assert len(bd_sites) == 3, "Should have 3 Binh Duong sites"

    # Check site IDs
    site_ids = sorted([r.get('site_id') for r in bd_sites])
    assert site_ids == ['A', 'B', 'C'], "Should have sites A, B, C"

    # Check all are small residential sites
    for site in bd_sites:
        assert site['land_area_ha'] < 2.0, "All BD sites should be < 2 ha"
        assert site['development_type'] == 'residential', "All BD sites should be residential"


def test_hai_phong_sites(extracted_data):
    """Test Hai Phong 5 sites extraction."""
    hp_sites = [r for r in extracted_data if r.get('city') == 'Hai Phong']
    assert len(hp_sites) == 5, "Should have 5 Hai Phong sites"

    # Check most are in Duong Kinh
    duong_kinh = [r for r in hp_sites if r.get('district') == 'Duong Kinh']
    assert len(duong_kinh) == 4, "Should have 4 Duong Kinh sites"

    # Check Kien An site
    kien_an = [r for r in hp_sites if r.get('district') == 'Kien An']
    assert len(kien_an) == 1, "Should have 1 Kien An site"
    assert kien_an[0]['land_area_ha'] == 7.2, "Kien An should be 7.2 ha"


def test_competitor_data_structure(extracted_data):
    """Test competitor data structure is valid."""
    for record in extracted_data:
        competitors = record.get('competitor_projects', [])
        assert isinstance(competitors, list), "competitor_projects should be a list"

        key_competitors = record.get('key_competitors', [])
        if key_competitors:
            assert isinstance(key_competitors, list), "key_competitors should be a list"
            for comp in key_competitors:
                assert 'project_name' in comp, "key_competitors should have project_name"
                assert 'developer' in comp, "key_competitors should have developer"


def test_no_duplicate_records(extracted_data):
    """Test there are no duplicate records."""
    seen = set()
    for record in extracted_data:
        # Create unique key from report file + site info
        key = (
            record.get('report_file'),
            record.get('city'),
            record.get('district'),
            record.get('land_area_ha'),
            record.get('site_id', '')
        )
        assert key not in seen, f"Duplicate record found: {key}"
        seen.add(key)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
