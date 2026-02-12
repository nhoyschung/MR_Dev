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
    ]
    session.add_all(projects)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def matcher(session_with_projects):
    return ProjectMatcher(session_with_projects)


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
