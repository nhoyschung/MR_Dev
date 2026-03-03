"""Tests for office and hotel market models, seeders, and query helpers."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.config import SEED_DIR
from src.db.models import (
    Base, OfficeProject, OfficeLeasingRecord, OfficeMarketSummary,
    HotelProject, HotelRoomType, HotelPerformanceRecord,
    ReportPeriod,
)
from src.db.queries import (
    get_office_projects,
    get_office_project_by_name,
    get_office_leasing_history,
    get_office_market_summary,
    get_office_rent_comparison,
    get_hotel_projects,
    get_hotel_room_breakdown,
    get_hotel_market_performance,
    get_hotel_kpi_trend,
)
from src.seeders.city_seeder import CitySeeder
from src.seeders.grade_seeder import GradeSeeder
from src.seeders.office_project_seeder import OfficeProjectSeeder
from src.seeders.office_leasing_seeder import OfficeLeasingSeeder
from src.seeders.office_market_summary_seeder import OfficeMarketSummarySeeder
from src.seeders.hotel_project_seeder import HotelProjectSeeder
from src.seeders.hotel_room_type_seeder import HotelRoomTypeSeeder
from src.seeders.hotel_performance_seeder import HotelPerformanceSeeder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    """In-memory session with cities + grade periods pre-seeded."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close(),
    )
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    CitySeeder(s, SEED_DIR).seed()
    GradeSeeder(s, SEED_DIR).seed()
    yield s
    s.close()


@pytest.fixture
def office_session(session):
    """Session with all office data seeded."""
    OfficeProjectSeeder(session, SEED_DIR).seed()
    OfficeLeasingSeeder(session, SEED_DIR).seed()
    OfficeMarketSummarySeeder(session, SEED_DIR).seed()
    return session


@pytest.fixture
def hotel_session(session):
    """Session with all hotel data seeded."""
    HotelProjectSeeder(session, SEED_DIR).seed()
    HotelRoomTypeSeeder(session, SEED_DIR).seed()
    HotelPerformanceSeeder(session, SEED_DIR).seed()
    return session


@pytest.fixture
def full_session(office_session):
    """Session with both office and hotel data."""
    HotelProjectSeeder(office_session, SEED_DIR).seed()
    HotelRoomTypeSeeder(office_session, SEED_DIR).seed()
    HotelPerformanceSeeder(office_session, SEED_DIR).seed()
    return office_session


# ---------------------------------------------------------------------------
# OfficeProjectSeeder tests
# ---------------------------------------------------------------------------

class TestOfficeProjectSeeder:
    def test_validate_passes(self, session):
        seeder = OfficeProjectSeeder(session, SEED_DIR)
        assert seeder.validate() is True

    def test_seed_returns_positive_count(self, session):
        count = OfficeProjectSeeder(session, SEED_DIR).seed()
        assert count > 0

    def test_seed_idempotent(self, session):
        first = OfficeProjectSeeder(session, SEED_DIR).seed()
        second = OfficeProjectSeeder(session, SEED_DIR).seed()
        assert first > 0
        assert second == 0

    def test_expected_project_count(self, office_session):
        """JSON file has 11 office projects."""
        total = office_session.query(OfficeProject).count()
        assert total == 11

    def test_grade_a_projects_exist(self, office_session):
        grade_a = (
            office_session.query(OfficeProject)
            .filter_by(office_grade="A")
            .count()
        )
        assert grade_a >= 5

    def test_deutsches_haus_has_dual_certification(self, office_session):
        proj = (
            office_session.query(OfficeProject)
            .filter_by(name="Deutsches Haus")
            .one()
        )
        assert "LEED Platinum" in proj.green_certificate
        assert "DGNB" in proj.green_certificate

    def test_the_hallmark_is_grade_a(self, office_session):
        proj = (
            office_session.query(OfficeProject)
            .filter_by(name="The Hallmark")
            .one()
        )
        assert proj.office_grade == "A"
        assert proj.total_leasing_area_m2 == 68000

    def test_worc_q2_is_grade_b_plus(self, office_session):
        proj = (
            office_session.query(OfficeProject)
            .filter_by(name="Worc@Q2")
            .one()
        )
        assert proj.office_grade == "B+"

    def test_all_projects_have_names(self, office_session):
        records = office_session.query(OfficeProject).all()
        for r in records:
            assert r.name is not None and len(r.name) > 0


# ---------------------------------------------------------------------------
# OfficeLeasingSeeder tests
# ---------------------------------------------------------------------------

class TestOfficeLeasingSeeder:
    def test_seed_returns_positive_count(self, office_session):
        total = office_session.query(OfficeLeasingRecord).count()
        assert total > 0

    def test_idempotent(self, office_session):
        second = OfficeLeasingSeeder(office_session, SEED_DIR).seed()
        assert second == 0

    def test_deutsches_haus_has_premium_rent(self, office_session):
        proj = (
            office_session.query(OfficeProject)
            .filter_by(name="Deutsches Haus")
            .one()
        )
        record = (
            office_session.query(OfficeLeasingRecord)
            .filter_by(office_project_id=proj.id)
            .first()
        )
        assert record is not None
        assert record.rent_min_usd >= 65

    def test_worc_q2_rent_range(self, office_session):
        proj = (
            office_session.query(OfficeProject)
            .filter_by(name="Worc@Q2")
            .one()
        )
        record = (
            office_session.query(OfficeLeasingRecord)
            .filter_by(office_project_id=proj.id)
            .first()
        )
        assert record is not None
        assert record.rent_min_usd == pytest.approx(23.5)
        assert record.rent_max_usd == pytest.approx(30.0)

    def test_all_records_have_rent_range(self, office_session):
        records = office_session.query(OfficeLeasingRecord).all()
        for r in records:
            assert r.rent_min_usd is not None
            assert r.rent_max_usd is not None
            assert r.rent_min_usd <= r.rent_max_usd


# ---------------------------------------------------------------------------
# OfficeMarketSummarySeeder tests
# ---------------------------------------------------------------------------

class TestOfficeMarketSummarySeeder:
    def test_seed_returns_positive_count(self, office_session):
        total = office_session.query(OfficeMarketSummary).count()
        assert total > 0

    def test_hcmc_2024_h2_total_stock(self, office_session):
        """HCMC 2024-H2 citywide stock = 2.8M m² NLA per Mozac data."""
        period = (
            office_session.query(ReportPeriod)
            .filter_by(year=2024, half="H2")
            .one()
        )
        summary = (
            office_session.query(OfficeMarketSummary)
            .filter(
                OfficeMarketSummary.period_id == period.id,
                OfficeMarketSummary.district_id.is_(None),
            )
            .first()
        )
        assert summary is not None
        assert summary.total_stock_nla_m2 == pytest.approx(2_800_000)

    def test_hcmc_2024_h2_has_394_projects(self, office_session):
        period = (
            office_session.query(ReportPeriod)
            .filter_by(year=2024, half="H2")
            .one()
        )
        summary = (
            office_session.query(OfficeMarketSummary)
            .filter(
                OfficeMarketSummary.period_id == period.id,
                OfficeMarketSummary.district_id.is_(None),
            )
            .first()
        )
        assert summary is not None
        assert summary.num_projects_total == 394

    def test_grade_a_rent_highest(self, office_session):
        """Grade A rent must be > Grade B > Grade C."""
        period = (
            office_session.query(ReportPeriod)
            .filter_by(year=2024, half="H2")
            .one()
        )
        summary = (
            office_session.query(OfficeMarketSummary)
            .filter(
                OfficeMarketSummary.period_id == period.id,
                OfficeMarketSummary.district_id.is_(None),
            )
            .first()
        )
        assert summary is not None
        assert summary.avg_rent_usd_grade_a > summary.avg_rent_usd_grade_b
        assert summary.avg_rent_usd_grade_b > summary.avg_rent_usd_grade_c


# ---------------------------------------------------------------------------
# HotelProjectSeeder tests
# ---------------------------------------------------------------------------

class TestHotelProjectSeeder:
    def test_seed_returns_positive_count(self, session):
        count = HotelProjectSeeder(session, SEED_DIR).seed()
        assert count > 0

    def test_idempotent(self, hotel_session):
        second = HotelProjectSeeder(hotel_session, SEED_DIR).seed()
        assert second == 0

    def test_mozac_hotel_is_148_rooms(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(name="Mozac Hotel (Plan B)")
            .one()
        )
        assert hotel.total_rooms == 148
        assert hotel.star_rating == 4

    def test_riverbank_is_5_star(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(name="Riverbank Place")
            .one()
        )
        assert hotel.star_rating == 5

    def test_m_village_brand_present(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(brand="M Village")
            .first()
        )
        assert hotel is not None

    def test_all_hotels_have_names(self, hotel_session):
        records = hotel_session.query(HotelProject).all()
        for r in records:
            assert r.name is not None and len(r.name) > 0


# ---------------------------------------------------------------------------
# HotelRoomTypeSeeder tests
# ---------------------------------------------------------------------------

class TestHotelRoomTypeSeeder:
    def test_mozac_has_5_room_types(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(name="Mozac Hotel (Plan B)")
            .one()
        )
        count = (
            hotel_session.query(HotelRoomType)
            .filter_by(hotel_project_id=hotel.id)
            .count()
        )
        assert count == 5

    def test_mozac_total_rooms_sum_to_148(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(name="Mozac Hotel (Plan B)")
            .one()
        )
        room_types = (
            hotel_session.query(HotelRoomType)
            .filter_by(hotel_project_id=hotel.id)
            .all()
        )
        total = sum(rt.room_count or 0 for rt in room_types)
        assert total == 148

    def test_suite_is_largest_room(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(name="Mozac Hotel (Plan B)")
            .one()
        )
        suite = (
            hotel_session.query(HotelRoomType)
            .filter_by(hotel_project_id=hotel.id, room_type="suite")
            .one()
        )
        assert suite.area_m2 == pytest.approx(70)

    def test_standard_room_is_smallest(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(name="Mozac Hotel (Plan B)")
            .one()
        )
        standard = (
            hotel_session.query(HotelRoomType)
            .filter_by(hotel_project_id=hotel.id, room_type="standard")
            .one()
        )
        assert standard.area_m2 == pytest.approx(30)


# ---------------------------------------------------------------------------
# HotelPerformanceSeeder tests
# ---------------------------------------------------------------------------

class TestHotelPerformanceSeeder:
    def test_seed_returns_positive_count(self, session):
        count = HotelPerformanceSeeder(session, SEED_DIR).seed()
        assert count > 0

    def test_hcmc_2024_h2_occupancy(self, hotel_session):
        """HCMC Q1 2025 occupancy = 68% per Mozac data (stored as 2024-H2)."""
        period = (
            hotel_session.query(ReportPeriod)
            .filter_by(year=2024, half="H2")
            .one()
        )
        record = (
            hotel_session.query(HotelPerformanceRecord)
            .filter(
                HotelPerformanceRecord.period_id == period.id,
                HotelPerformanceRecord.hotel_project_id.is_(None),
                HotelPerformanceRecord.district_id.is_(None),
            )
            .first()
        )
        assert record is not None
        assert record.occupancy_rate_pct == pytest.approx(68)

    def test_hcmc_adr_is_reasonable(self, hotel_session):
        """ADR should be in range 1M–5M VND/night for HCMC market."""
        records = (
            hotel_session.query(HotelPerformanceRecord)
            .filter(HotelPerformanceRecord.hotel_project_id.is_(None))
            .all()
        )
        for r in records:
            if r.adr_vnd is not None:
                assert 1_000_000 <= r.adr_vnd <= 5_000_000, (
                    f"ADR out of range: {r.adr_vnd} for period_id={r.period_id}"
                )

    def test_revpar_is_occ_times_adr(self, hotel_session):
        """RevPAR should approximately equal occupancy_rate * ADR."""
        records = (
            hotel_session.query(HotelPerformanceRecord)
            .filter(HotelPerformanceRecord.hotel_project_id.is_(None))
            .all()
        )
        for r in records:
            if r.revpar_vnd and r.adr_vnd and r.occupancy_rate_pct:
                expected = r.adr_vnd * (r.occupancy_rate_pct / 100)
                assert r.revpar_vnd == pytest.approx(expected, rel=0.05)


# ---------------------------------------------------------------------------
# Query helper tests
# ---------------------------------------------------------------------------

class TestGetOfficeProjects:
    def test_returns_list(self, office_session):
        result = get_office_projects(office_session)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_filter_by_grade_a(self, office_session):
        result = get_office_projects(office_session, grade="A")
        assert all(p.office_grade == "A" for p in result)
        assert len(result) >= 5

    def test_filter_by_city(self, office_session):
        result = get_office_projects(office_session, city_name="hcmc")
        assert len(result) > 0

    def test_get_by_name_found(self, office_session):
        proj = get_office_project_by_name(office_session, "The Hallmark")
        assert proj is not None
        assert proj.office_grade == "A"

    def test_get_by_name_not_found(self, office_session):
        proj = get_office_project_by_name(office_session, "Nonexistent Tower")
        assert proj is None


class TestGetOfficeLeasingHistory:
    def test_returns_records_for_valid_project(self, office_session):
        proj = get_office_project_by_name(office_session, "The Hallmark")
        records = get_office_leasing_history(office_session, proj.id)
        assert len(records) >= 1

    def test_records_ordered_chronologically(self, office_session):
        proj = get_office_project_by_name(office_session, "Deutsches Haus")
        records = get_office_leasing_history(office_session, proj.id)
        if len(records) >= 2:
            for i in range(1, len(records)):
                assert (
                    records[i].period.year > records[i - 1].period.year
                    or (
                        records[i].period.year == records[i - 1].period.year
                        and records[i].period.half >= records[i - 1].period.half
                    )
                )

    def test_empty_for_unknown_project_id(self, office_session):
        records = get_office_leasing_history(office_session, 99999)
        assert records == []


class TestGetOfficeMarketSummary:
    def test_returns_summary_for_hcmc(self, office_session):
        result = get_office_market_summary(office_session, "hcmc", 2024, "H2")
        assert result is not None

    def test_none_for_unknown_period(self, office_session):
        result = get_office_market_summary(office_session, "hcmc", 2099, "H1")
        assert result is None

    def test_394_projects_in_hcmc_2024_h2(self, office_session):
        result = get_office_market_summary(office_session, "hcmc", 2024, "H2")
        assert result.num_projects_total == 394


class TestGetOfficeRentComparison:
    def test_returns_list(self, office_session):
        result = get_office_rent_comparison(office_session, "hcmc", 2023, "H1")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_has_required_keys(self, office_session):
        result = get_office_rent_comparison(office_session, "hcmc", 2023, "H1")
        for row in result:
            assert "name" in row
            assert "office_grade" in row
            assert "rent_min_usd" in row
            assert "rent_max_usd" in row
            assert "rent_midpoint_usd" in row

    def test_ordered_by_rent_descending(self, office_session):
        result = get_office_rent_comparison(office_session, "hcmc", 2023, "H1")
        rents = [r["rent_max_usd"] for r in result if r["rent_max_usd"] is not None]
        assert rents == sorted(rents, reverse=True)


class TestGetHotelProjects:
    def test_returns_list(self, hotel_session):
        result = get_hotel_projects(hotel_session)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_filter_by_min_stars(self, hotel_session):
        result = get_hotel_projects(hotel_session, min_stars=5)
        assert all(h.star_rating >= 5 for h in result)

    def test_get_hotel_room_breakdown(self, hotel_session):
        hotel = (
            hotel_session.query(HotelProject)
            .filter_by(name="Mozac Hotel (Plan B)")
            .one()
        )
        rooms = get_hotel_room_breakdown(hotel_session, hotel.id)
        assert len(rooms) == 5
        # Ordered by area ascending
        areas = [r.area_m2 for r in rooms if r.area_m2]
        assert areas == sorted(areas)


class TestGetHotelMarketPerformance:
    def test_returns_record_for_hcmc(self, hotel_session):
        result = get_hotel_market_performance(hotel_session, "hcmc", 2024, "H2")
        assert result is not None

    def test_none_for_unknown_period(self, hotel_session):
        result = get_hotel_market_performance(hotel_session, "hcmc", 2099, "H1")
        assert result is None

    def test_hcmc_2024_h2_occupancy_68pct(self, hotel_session):
        result = get_hotel_market_performance(hotel_session, "hcmc", 2024, "H2")
        assert result.occupancy_rate_pct == pytest.approx(68)


class TestGetHotelKpiTrend:
    def test_returns_list(self, hotel_session):
        result = get_hotel_kpi_trend(hotel_session, "hcmc")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_ordered_chronologically(self, hotel_session):
        result = get_hotel_kpi_trend(hotel_session, "hcmc")
        periods = [r["period"] for r in result]
        assert periods == sorted(periods)

    def test_has_required_keys(self, hotel_session):
        result = get_hotel_kpi_trend(hotel_session, "hcmc")
        for row in result:
            assert "period" in row
            assert "year" in row
            assert "half" in row
            assert "occupancy_rate_pct" in row
            assert "adr_vnd" in row
            assert "revpar_vnd" in row

    def test_occupancy_values_in_range(self, hotel_session):
        result = get_hotel_kpi_trend(hotel_session, "hcmc")
        for row in result:
            if row["occupancy_rate_pct"] is not None:
                assert 0 <= row["occupancy_rate_pct"] <= 100
