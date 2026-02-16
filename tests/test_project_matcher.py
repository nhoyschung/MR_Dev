"""Tests for the project name matcher."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, City, District, Project
from src.utils.project_matcher import ProjectMatcher


@pytest.fixture
def session_with_projects():
    """In-memory DB with sample projects."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close(),
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    city = City(name_en="Ho Chi Minh City", region="South")
    session.add(city)
    session.flush()

    district = District(name_en="District 2", city_id=city.id)
    session.add(district)
    session.flush()

    projects = [
        Project(name="Masteri Thao Dien", district_id=district.id),
        Project(name="Vista Verde", district_id=district.id),
        Project(name="The Global City", district_id=district.id),
        Project(name="Eaton Park", district_id=district.id),
        Project(name="Lancaster Luminaire", district_id=district.id),
        Project(name="Happy One Morri", district_id=district.id),
        Project(name="Vinhomes West Point", district_id=district.id),
        Project(name="Noble Crystal Tay Ho", district_id=district.id),
        Project(name="Picity Sky Park", district_id=district.id),
        Project(name="Starlake The Prime K8", district_id=district.id),
        Project(name="The Cosmopolitan Co Loa", district_id=district.id),
        Project(name="Vinhomes Smart City", district_id=district.id),
        Project(name="Masteri Centre Point", district_id=district.id),
        Project(name="Vinhomes Ocean Park", district_id=district.id),
    ]
    session.add_all(projects)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def matcher(session_with_projects):
    return ProjectMatcher(session_with_projects)


@pytest.fixture
def matcher_with_aliases(session_with_projects):
    aliases = {
        "STARLAKE CITY": "Starlake The Prime K8",
        "IMPERIA SMART CITY": "Vinhomes Smart City",
        "VHOP 1 – MASTERISE HOMES –": "Masteri Centre Point",
        "VHOP1 – (P9) THE METROPOLITAN –": "Vinhomes Ocean Park",
    }
    return ProjectMatcher(session_with_projects, aliases=aliases)


class TestExactMatch:
    def test_exact_case_insensitive(self, matcher):
        pid, conf = matcher.match("Masteri Thao Dien")
        assert pid is not None
        assert conf == 1.0

    def test_exact_different_case(self, matcher):
        pid, conf = matcher.match("masteri thao dien")
        assert pid is not None
        assert conf == 1.0

    def test_exact_with_whitespace(self, matcher):
        pid, conf = matcher.match("  Vista Verde  ")
        assert pid is not None
        assert conf == 1.0


class TestNormalizedMatch:
    def test_strip_phase(self, matcher):
        pid, conf = matcher.match("Happy One Morri – (P1) Block Tochi")
        assert pid is not None
        assert conf >= 0.5

    def test_strip_block_suffix(self, matcher):
        pid, conf = matcher.match("Eaton Park – (P3) Tower A4")
        assert pid is not None
        assert conf >= 0.5

    def test_strip_parenthetical(self, matcher):
        pid, conf = matcher.match("The Global City (Phase 2)")
        assert pid is not None
        assert conf >= 0.5


class TestSubstringMatch:
    def test_substring_contained(self, matcher):
        pid, conf = matcher.match("LANCASTER LUMINAIRE")
        assert pid is not None
        assert conf >= 0.5

    def test_substring_partial(self, matcher):
        pid, conf = matcher.match("Noble Crystal")
        assert pid is not None
        assert conf >= 0.5


class TestNoMatch:
    def test_empty_string(self, matcher):
        pid, conf = matcher.match("")
        assert pid is None
        assert conf == 0.0

    def test_nonexistent(self, matcher):
        pid, conf = matcher.match("Completely Unknown Project XYZ123")
        assert pid is None
        assert conf == 0.0


class TestNormalize:
    def test_normalize_phase_suffix(self):
        assert "happy one morri" in ProjectMatcher._normalize("Happy One Morri – (P1) Block Tochi")

    def test_normalize_basic(self):
        result = ProjectMatcher._normalize("  Vista Verde  ")
        assert result == "vista verde"

    def test_normalize_strip_parens(self):
        result = ProjectMatcher._normalize("Project (Phase 2)")
        assert "phase" not in result


class TestUnicodeDashNormalization:
    def test_en_dash_treated_as_hyphen(self):
        result = ProjectMatcher._normalize("Eaton Park \u2013 (P3)")
        assert "eaton park" in result
        assert "p3" not in result

    def test_em_dash_treated_as_hyphen(self):
        result = ProjectMatcher._normalize("Happy One \u2014 Block A")
        assert "happy one" in result
        assert "block" not in result

    def test_trailing_dash_stripped(self):
        result = ProjectMatcher._normalize("THE GLOBAL CITY –")
        assert result == "the global city"

    def test_trailing_em_dash_stripped(self):
        result = ProjectMatcher._normalize("THE MATRIX ONE —")
        assert result == "the matrix one"


class TestPhaseWithNameStripping:
    def test_phase_then_name(self, matcher):
        """PICITY SKY PARK - (P2) SKYZEN should match Picity Sky Park."""
        pid, conf = matcher.match("PICITY SKY PARK - (P2) SKYZEN")
        assert pid is not None
        assert conf >= 0.5

    def test_phase_then_name_normalize(self):
        result = ProjectMatcher._normalize("PICITY SKY PARK - (P2) SKYZEN")
        assert "picity sky park" in result
        assert "skyzen" not in result


class TestPrefixStripping:
    def test_vhop_prefix(self):
        result = ProjectMatcher._normalize("VHOP 1 – MASTERI HOMES –")
        assert "masteri" in result
        assert "vhop" not in result

    def test_vhsc_prefix(self):
        result = ProjectMatcher._normalize("VHSC– IMPERIA SMART CITY –")
        assert "imperia smart city" in result
        assert "vhsc" not in result

    def test_vhgg_prefix(self):
        result = ProjectMatcher._normalize("VHGG – (P5) IMPERIA SIGNATURE -")
        assert "imperia signature" in result
        assert "vhgg" not in result


class TestJunkFilter:
    def test_section_header_rejected(self, matcher):
        pid, conf = matcher.match("II. ON-SALES PROJECTS")
        assert pid is None
        assert conf == 0.0

    def test_column_header_rejected(self, matcher):
        pid, conf = matcher.match("PROJECT NAME")
        assert pid is None
        assert conf == 0.0

    def test_city_name_rejected(self, matcher):
        pid, conf = matcher.match("HO CHI MINH CITY")
        assert pid is None
        assert conf == 0.0

    def test_generic_label_rejected(self, matcher):
        pid, conf = matcher.match("PENTHOUSE")
        assert pid is None
        assert conf == 0.0

    def test_landed_house_rejected(self, matcher):
        pid, conf = matcher.match("LANDED HOUSE")
        assert pid is None
        assert conf == 0.0

    def test_block_label_rejected(self, matcher):
        pid, conf = matcher.match("BLOCK B2")
        assert pid is None
        assert conf == 0.0

    def test_is_junk_name_static(self):
        assert ProjectMatcher.is_junk_name("PROJECT NAME") is True
        assert ProjectMatcher.is_junk_name("PENTHOUSE") is True
        assert ProjectMatcher.is_junk_name("02.01 SECTION") is True
        assert ProjectMatcher.is_junk_name("Masteri Thao Dien") is False


class TestAliasMatch:
    def test_alias_returns_095(self, matcher_with_aliases):
        pid, conf = matcher_with_aliases.match("STARLAKE CITY")
        assert pid is not None
        assert conf == 0.95

    def test_alias_imperia_smart_city(self, matcher_with_aliases):
        pid, conf = matcher_with_aliases.match("IMPERIA SMART CITY")
        assert pid is not None
        assert conf == 0.95

    def test_alias_with_prefix(self, matcher_with_aliases):
        pid, conf = matcher_with_aliases.match("VHOP 1 – MASTERISE HOMES –")
        assert pid is not None
        assert conf == 0.95

    def test_alias_no_match_for_unknown(self, matcher_with_aliases):
        pid, conf = matcher_with_aliases.match("Completely Unknown XYZ")
        assert pid is None
        assert conf == 0.0
