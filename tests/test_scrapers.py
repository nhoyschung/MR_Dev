"""Tests for the BDS web scraping system: parsers, rate limiter, pipeline."""

import asyncio

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import (
    Base, City, District, Developer, Project, ReportPeriod,
    ScrapeJob, ScrapedListing, PriceRecord, SourceReport, DataLineage,
)
from src.scrapers.parsers import (
    clean_project_name,
    extract_slug_from_url,
    parse_area_sqm,
    parse_int_from_text,
    parse_price_per_sqm,
    parse_price_vnd,
)
from src.scrapers.rate_limiter import RateLimiter
from src.scrapers.models import ScrapedListingData, ScrapedProjectData, ScrapeJobResult
from src.scrapers.pipeline import ScrapePipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """In-memory SQLite session with all tables."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close(),
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def seeded_session(db_session: Session):
    """Session with basic reference data for pipeline tests."""
    city = City(name_en="HCMC", name_vi="TP. Ho Chi Minh", region="South")
    db_session.add(city)
    db_session.flush()

    district = District(city_id=city.id, name_en="District 9", name_vi="Quan 9")
    db_session.add(district)
    db_session.flush()

    developer = Developer(name_en="Vinhomes")
    db_session.add(developer)
    db_session.flush()

    project = Project(
        name="Vinhomes Grand Park",
        developer_id=developer.id,
        district_id=district.id,
    )
    db_session.add(project)
    db_session.flush()

    period = ReportPeriod(year=2025, half="H2")
    db_session.add(period)
    db_session.flush()

    db_session.commit()
    return db_session


# ---------------------------------------------------------------------------
# Parser Tests
# ---------------------------------------------------------------------------

class TestPriceParser:
    def test_parse_ty(self):
        assert parse_price_vnd("2.5 tỷ") == 2_500_000_000

    def test_parse_ty_ascii(self):
        assert parse_price_vnd("3 ty") == 3_000_000_000

    def test_parse_trieu(self):
        assert parse_price_vnd("800 triệu") == 800_000_000

    def test_parse_trieu_ascii(self):
        assert parse_price_vnd("500 trieu") == 500_000_000

    def test_parse_ty_with_trieu(self):
        """2 tỷ 500 triệu = 2.5 billion"""
        assert parse_price_vnd("2 tỷ 500 triệu") == 2_500_000_000

    def test_parse_comma_decimal(self):
        assert parse_price_vnd("2,5 tỷ") == 2_500_000_000

    def test_parse_none(self):
        assert parse_price_vnd("") is None
        assert parse_price_vnd("Thỏa thuận") is None

    def test_parse_price_per_sqm(self):
        assert parse_price_per_sqm("45 triệu/m²") == 45_000_000

    def test_parse_price_per_sqm_ascii(self):
        assert parse_price_per_sqm("120 tr/m2") == 120_000_000

    def test_parse_price_per_sqm_none(self):
        assert parse_price_per_sqm("2.5 tỷ") is None


class TestAreaParser:
    def test_basic(self):
        assert parse_area_sqm("65 m²") == 65.0

    def test_decimal(self):
        assert parse_area_sqm("85.5 m2") == 85.5

    def test_no_space(self):
        assert parse_area_sqm("120m²") == 120.0

    def test_none(self):
        assert parse_area_sqm("") is None

    def test_unreasonable_value(self):
        """Values outside 5-10000 should be rejected."""
        assert parse_area_sqm("2 m²") is None


class TestNameParser:
    def test_strip_du_an(self):
        assert clean_project_name("Dự án Vinhomes Grand Park") == "Vinhomes Grand Park"

    def test_strip_can_ho(self):
        assert clean_project_name("Căn hộ The Infiniti") == "The Infiniti"

    def test_strip_chung_cu(self):
        assert clean_project_name("Chung cư Masteri Thao Dien") == "Masteri Thao Dien"

    def test_no_prefix(self):
        assert clean_project_name("Vinhomes Central Park") == "Vinhomes Central Park"

    def test_empty(self):
        assert clean_project_name("") == ""


class TestSlugExtractor:
    def test_basic(self):
        assert extract_slug_from_url(
            "https://batdongsan.com.vn/du-an/vinhomes-grand-park"
        ) == "vinhomes-grand-park"

    def test_no_match(self):
        assert extract_slug_from_url("https://example.com") is None

    def test_none(self):
        assert extract_slug_from_url("") is None


class TestIntParser:
    def test_basic(self):
        assert parse_int_from_text("3 phòng ngủ") == 3

    def test_no_number(self):
        assert parse_int_from_text("abc") is None


# ---------------------------------------------------------------------------
# Pydantic Schema Tests
# ---------------------------------------------------------------------------

class TestScrapedListingData:
    def test_valid(self):
        data = ScrapedListingData(
            bds_listing_id="123",
            project_name="  Vinhomes Grand Park  ",
            price_vnd=2_500_000_000,
            area_sqm=65.0,
        )
        assert data.project_name == "Vinhomes Grand Park"
        assert data.price_vnd == 2_500_000_000

    def test_negative_price_rejected(self):
        with pytest.raises(Exception):
            ScrapedListingData(price_vnd=-100)

    def test_direction_normalized(self):
        data = ScrapedListingData(direction="  đông nam  ")
        assert data.direction == "Đông Nam"


class TestScrapedProjectData:
    def test_name_required(self):
        with pytest.raises(Exception):
            ScrapedProjectData(name="")

    def test_valid(self):
        data = ScrapedProjectData(
            name="Vinhomes Grand Park",
            slug="vinhomes-grand-park",
            total_units=10000,
        )
        assert data.name == "Vinhomes Grand Park"


class TestScrapeJobResult:
    def test_duration(self):
        from datetime import datetime, timezone
        r = ScrapeJobResult(
            job_type="test",
            status="completed",
            started_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2025, 1, 1, 10, 5, 30, tzinfo=timezone.utc),
        )
        assert r.duration_sec == 330.0


# ---------------------------------------------------------------------------
# Rate Limiter Tests
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def test_request_count(self):
        limiter = RateLimiter(min_delay=0, max_delay=0, rpm=120, capacity=10)
        asyncio.get_event_loop().run_until_complete(limiter.acquire())
        assert limiter.request_count == 1

    def test_reset(self):
        limiter = RateLimiter(min_delay=0, max_delay=0, rpm=120, capacity=10)
        asyncio.get_event_loop().run_until_complete(limiter.acquire())
        limiter.reset()
        assert limiter.request_count == 0


# ---------------------------------------------------------------------------
# DB Model Tests
# ---------------------------------------------------------------------------

class TestScrapeJobModel:
    def test_create_job(self, db_session: Session):
        job = ScrapeJob(job_type="project_list", status="pending")
        db_session.add(job)
        db_session.commit()
        assert job.id is not None
        assert job.status == "pending"

    def test_job_listing_relationship(self, db_session: Session):
        job = ScrapeJob(job_type="test", status="running")
        db_session.add(job)
        db_session.flush()

        listing = ScrapedListing(
            scrape_job_id=job.id,
            bds_listing_id="test-123",
            project_name="Test Project",
        )
        db_session.add(listing)
        db_session.commit()

        assert len(job.listings) == 1
        assert job.listings[0].bds_listing_id == "test-123"

    def test_unique_bds_listing_id(self, db_session: Session):
        job = ScrapeJob(job_type="test", status="running")
        db_session.add(job)
        db_session.flush()

        l1 = ScrapedListing(scrape_job_id=job.id, bds_listing_id="dup-1")
        db_session.add(l1)
        db_session.commit()

        l2 = ScrapedListing(scrape_job_id=job.id, bds_listing_id="dup-1")
        db_session.add(l2)
        with pytest.raises(Exception):
            db_session.commit()


class TestProjectBdsColumns:
    def test_bds_slug_column(self, db_session: Session):
        project = Project(name="Test", bds_slug="test-slug", bds_url="https://bds.com/test")
        db_session.add(project)
        db_session.commit()
        assert project.bds_slug == "test-slug"


# ---------------------------------------------------------------------------
# Pipeline Tests
# ---------------------------------------------------------------------------

class TestScrapePipeline:
    def test_create_and_complete_job(self, db_session: Session):
        pipeline = ScrapePipeline(db_session)
        job = pipeline.create_job("test", "https://example.com")
        assert job.status == "running"

        result = pipeline.complete_job(job, 10, 8)
        assert result.status == "completed"
        assert result.items_found == 10
        assert result.items_saved == 8

    def test_process_listings(self, seeded_session: Session):
        pipeline = ScrapePipeline(seeded_session)
        job = pipeline.create_job("test")

        raw = [
            {
                "bds_listing_id": "bds-001",
                "project_name": "Vinhomes Grand Park",
                "price_vnd": 2_500_000_000,
                "price_per_sqm": 45_000_000,
                "area_sqm": 55.0,
            },
            {
                "bds_listing_id": "bds-002",
                "project_name": "Unknown Project XYZ",
                "price_vnd": 1_000_000_000,
                "area_sqm": 40.0,
            },
        ]

        valid, saved = pipeline.process_listings(raw, job)
        assert valid == 2
        assert saved == 2

        # First listing should be matched
        l1 = seeded_session.query(ScrapedListing).filter_by(bds_listing_id="bds-001").one()
        assert l1.matched_project_id is not None

        # Second listing should not be matched
        l2 = seeded_session.query(ScrapedListing).filter_by(bds_listing_id="bds-002").one()
        assert l2.matched_project_id is None

    def test_duplicate_prevention(self, seeded_session: Session):
        pipeline = ScrapePipeline(seeded_session)
        job = pipeline.create_job("test")

        raw = [{"bds_listing_id": "dup-001", "project_name": "Test"}]
        _, saved1 = pipeline.process_listings(raw, job)
        seeded_session.commit()

        _, saved2 = pipeline.process_listings(raw, job)
        assert saved1 == 1
        assert saved2 == 0  # Duplicate rejected

    def test_promote_job(self, seeded_session: Session):
        pipeline = ScrapePipeline(seeded_session)
        job = pipeline.create_job("test")

        # Get the project and period IDs
        project = seeded_session.query(Project).filter_by(name="Vinhomes Grand Park").one()
        period = seeded_session.query(ReportPeriod).first()

        raw = [{
            "bds_listing_id": "promo-001",
            "project_name": "Vinhomes Grand Park",
            "price_vnd": 2_500_000_000,
            "price_per_sqm": 45_000_000,
            "area_sqm": 55.0,
        }]
        pipeline.process_listings(raw, job)
        pipeline.complete_job(job, 1, 1)

        report = pipeline.promote_job(job.id, period.id)
        promoted = report.promoted

        # Check price_record was created
        pr = seeded_session.query(PriceRecord).filter_by(project_id=project.id).first()
        assert pr is not None
        assert pr.price_vnd_per_m2 == 45_000_000

        # Check data lineage
        lineage = seeded_session.query(DataLineage).filter_by(
            table_name="price_records", record_id=pr.id
        ).first()
        assert lineage is not None

        # Check listing marked as promoted
        listing = seeded_session.query(ScrapedListing).filter_by(bds_listing_id="promo-001").one()
        assert listing.promoted is True


# ---------------------------------------------------------------------------
# Table Count Test (updated for new tables)
# ---------------------------------------------------------------------------

class TestUpdatedTableCount:
    def test_table_count_with_scraper_tables(self, db_session: Session):
        """Should have at least 30 tables (core + scraper + office/hotel + land site)."""
        assert len(Base.metadata.tables) >= 30
        assert "scrape_jobs" in Base.metadata.tables
        assert "scraped_listings" in Base.metadata.tables
        assert "scraped_office_listings" in Base.metadata.tables
