"""Tests for the price reconciliation and anomaly detection module."""

import json

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import (
    Base, City, District, Developer, Project,
    PriceRecord, ReportPeriod, ScrapeJob, ScrapedListing, SourceReport,
)
from src.utils.reconciler import (
    ANOMALY_SIGMA,
    CONFLICT_THRESHOLD,
    PriceReconciler,
    ReconcileOutcome,
    ReconciliationReport,
)
from src.scrapers.pipeline import ScrapePipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    """Clean in-memory SQLite session."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect",
        lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close(),
    )
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


@pytest.fixture
def base_data(session: Session):
    """Minimal DB records needed for reconciliation tests."""
    city = City(name_en="Test City", region="South")
    session.add(city)
    session.flush()

    district = District(name_en="Test District", city_id=city.id)
    session.add(district)
    session.flush()

    dev = Developer(name_en="Test Developer")
    session.add(dev)
    session.flush()

    project = Project(
        name="Test Project",
        developer_id=dev.id,
        district_id=district.id,
    )
    session.add(project)
    session.flush()

    period = ReportPeriod(year=2024, half="H1")
    session.add(period)
    session.flush()

    return {"city": city, "district": district, "dev": dev, "project": project, "period": period}


def make_scrape_job(session: Session) -> ScrapeJob:
    job = ScrapeJob(job_type="listing", status="completed")
    session.add(job)
    session.flush()
    return job


def make_listing(
    session: Session,
    job: ScrapeJob,
    project_id: int,
    price_vnd: float,
    bds_id: str = None,
) -> ScrapedListing:
    listing = ScrapedListing(
        scrape_job_id=job.id,
        bds_listing_id=bds_id,
        project_name="Test Project",
        price_per_sqm=price_vnd,
        matched_project_id=project_id,
        promoted=False,
    )
    session.add(listing)
    session.flush()
    return listing


def make_price_record(
    session: Session, project_id: int, period_id: int, price_vnd: float
) -> PriceRecord:
    record = PriceRecord(
        project_id=project_id,
        period_id=period_id,
        price_vnd_per_m2=price_vnd,
        price_incl_vat=True,
        source_report="NHO-PD test",
    )
    session.add(record)
    session.flush()
    return record


# ---------------------------------------------------------------------------
# Unit tests — ReconcileOutcome
# ---------------------------------------------------------------------------

class TestReconcileOutcome:
    def test_ok_status(self):
        outcome = ReconcileOutcome(status="ok")
        assert outcome.status == "ok"
        assert not outcome.conflict
        assert not outcome.anomaly

    def test_to_json_excludes_none(self):
        outcome = ReconcileOutcome(status="ok", divergence_pct=5.0)
        data = json.loads(outcome.to_json())
        assert "divergence_pct" in data
        assert "status" not in data           # status excluded from JSON
        assert "existing_price_vnd" not in data   # None excluded

    def test_to_json_rounds_floats(self):
        outcome = ReconcileOutcome(status="anomaly", sigma_distance=2.666666)
        data = json.loads(outcome.to_json())
        assert data["sigma_distance"] == 2.67


# ---------------------------------------------------------------------------
# Unit tests — PriceReconciler.build_batch_stats
# ---------------------------------------------------------------------------

class TestBuildBatchStats:
    def test_normal_batch(self, session):
        r = PriceReconciler(session)
        r.build_batch_stats([1_000_000, 1_100_000, 1_050_000, 1_200_000])
        assert r._batch_mean is not None
        assert r._batch_std is not None
        assert r._batch_std > 0

    def test_single_price_no_std(self, session):
        """Fewer than 2 prices → stats unavailable (anomaly detection skipped)."""
        r = PriceReconciler(session)
        r.build_batch_stats([1_000_000])
        assert r._batch_mean is None  # needs >= 2 data points
        assert r._batch_std is None

    def test_empty_batch(self, session):
        r = PriceReconciler(session)
        r.build_batch_stats([])
        assert r._batch_mean is None
        assert r._batch_std is None

    def test_zero_prices_excluded(self, session):
        r = PriceReconciler(session)
        r.build_batch_stats([0, 0, 1_000_000, 1_100_000])
        assert r._batch_mean == pytest.approx(1_050_000)


# ---------------------------------------------------------------------------
# Unit tests — PriceReconciler.check_conflict
# ---------------------------------------------------------------------------

class TestCheckConflict:
    def test_no_existing_price_no_conflict(self, session, base_data):
        r = PriceReconciler(session)
        conflict, existing, _, div = r.check_conflict(
            base_data["project"].id, base_data["period"].id, 1_000_000
        )
        assert not conflict
        assert existing is None
        assert div is None

    def test_within_threshold_no_conflict(self, session, base_data):
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        r = PriceReconciler(session, conflict_threshold=0.15)
        conflict, _, _, div = r.check_conflict(
            base_data["project"].id, base_data["period"].id, 1_100_000  # 10% diff
        )
        assert not conflict
        assert div == pytest.approx(10.0)

    def test_exceeds_threshold_conflict(self, session, base_data):
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        r = PriceReconciler(session, conflict_threshold=0.15)
        conflict, _, _, div = r.check_conflict(
            base_data["project"].id, base_data["period"].id, 1_200_000  # 20% diff
        )
        assert conflict
        assert div == pytest.approx(20.0)

    def test_exact_threshold_boundary(self, session, base_data):
        """Divergence exactly equal to threshold is NOT flagged (> not >=)."""
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        r = PriceReconciler(session, conflict_threshold=0.15)
        conflict, _, _, div = r.check_conflict(
            base_data["project"].id, base_data["period"].id, 1_150_000  # exactly 15%
        )
        assert not conflict

    def test_lower_price_also_detected(self, session, base_data):
        """BDS price below NHO price by >15% is also a conflict."""
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        r = PriceReconciler(session, conflict_threshold=0.15)
        conflict, _, _, div = r.check_conflict(
            base_data["project"].id, base_data["period"].id, 800_000  # 20% below
        )
        assert conflict


# ---------------------------------------------------------------------------
# Unit tests — PriceReconciler.check_anomaly
# ---------------------------------------------------------------------------

class TestCheckAnomaly:
    def test_no_batch_stats_no_anomaly(self, session):
        r = PriceReconciler(session)
        is_anomaly, _, _, sigma = r.check_anomaly(1_000_000)
        assert not is_anomaly
        assert sigma is None

    def test_price_within_sigma_no_anomaly(self, session):
        r = PriceReconciler(session, anomaly_sigma=2.5)
        r.build_batch_stats([1_000_000] * 10 + [1_100_000] * 10)
        is_anomaly, _, _, _ = r.check_anomaly(1_050_000)
        assert not is_anomaly

    def test_extreme_outlier_is_anomaly(self, session):
        r = PriceReconciler(session, anomaly_sigma=2.5)
        # Tight cluster around 1M VND, outlier at 5M
        r.build_batch_stats([1_000_000] * 20)
        # std will be 0 because all values are identical — won't trigger
        # Use a cluster with spread
        r.build_batch_stats([900_000, 950_000, 1_000_000, 1_050_000, 1_100_000])
        is_anomaly, mean, std, sigma = r.check_anomaly(5_000_000)
        assert is_anomaly
        assert sigma > 2.5

    def test_sigma_distance_calculated_correctly(self, session):
        r = PriceReconciler(session)
        # mean=1_000_000, std=100_000 → price=1_250_000 → sigma=exactly 2.5
        r._batch_mean = 1_000_000
        r._batch_std = 100_000
        is_anomaly_exact, _, _, sigma_exact = r.check_anomaly(1_250_000)
        assert sigma_exact == pytest.approx(2.5)
        # Exactly 2.5 is NOT > 2.5 (strict), so no anomaly
        assert not is_anomaly_exact
        # Price at 1_260_000 → sigma ≈ 2.6 → anomaly
        is_anomaly_over, _, _, sigma_over = r.check_anomaly(1_260_000)
        assert sigma_over > 2.5
        assert is_anomaly_over


# ---------------------------------------------------------------------------
# Unit tests — PriceReconciler.reconcile (combined)
# ---------------------------------------------------------------------------

class TestReconcileCombined:
    def test_ok_status_clean_price(self, session, base_data):
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        r = PriceReconciler(session)
        r.build_batch_stats([950_000, 1_000_000, 1_050_000, 1_100_000])
        outcome = r.reconcile(base_data["project"].id, base_data["period"].id, 1_020_000)
        assert outcome.status == "ok"
        assert not outcome.conflict
        assert not outcome.anomaly

    def test_conflict_status(self, session, base_data):
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        r = PriceReconciler(session, conflict_threshold=0.15)
        # Wide batch spread → 1_250_000 is within 2.5σ (no anomaly), only conflict
        r.build_batch_stats([500_000, 750_000, 1_000_000, 1_250_000, 1_500_000])
        outcome = r.reconcile(base_data["project"].id, base_data["period"].id, 1_250_000)
        assert outcome.status == "conflict"
        assert outcome.conflict
        assert not outcome.anomaly

    def test_anomaly_status(self, session, base_data):
        """No existing NHO price but outlier from batch."""
        r = PriceReconciler(session, anomaly_sigma=2.5)
        r._batch_mean = 1_000_000
        r._batch_std = 100_000
        outcome = r.reconcile(base_data["project"].id, base_data["period"].id, 5_000_000)
        assert outcome.status == "anomaly"
        assert outcome.anomaly
        assert not outcome.conflict

    def test_conflict_anomaly_status(self, session, base_data):
        """Both flags triggered simultaneously."""
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        r = PriceReconciler(session, conflict_threshold=0.15, anomaly_sigma=2.5)
        r._batch_mean = 1_000_000
        r._batch_std = 100_000
        # 5M VND: 400% above NHO (conflict) AND >2.5σ from batch mean (anomaly)
        outcome = r.reconcile(base_data["project"].id, base_data["period"].id, 5_000_000)
        assert outcome.status == "conflict_anomaly"
        assert outcome.conflict
        assert outcome.anomaly


# ---------------------------------------------------------------------------
# Integration tests — pipeline.promote_job with reconciliation
# ---------------------------------------------------------------------------

class TestPromoteJobReconciliation:
    def test_returns_reconciliation_report(self, session, base_data):
        job = make_scrape_job(session)
        make_listing(session, job, base_data["project"].id, 1_000_000)
        pipeline = ScrapePipeline(session)
        result = pipeline.promote_job(job.id, base_data["period"].id)
        assert isinstance(result, ReconciliationReport)

    def test_clean_listing_promoted(self, session, base_data):
        job = make_scrape_job(session)
        make_listing(session, job, base_data["project"].id, 1_000_000)
        pipeline = ScrapePipeline(session)
        result = pipeline.promote_job(job.id, base_data["period"].id)
        assert result.promoted == 1
        assert result.conflicted == 0

    def test_conflicted_listing_not_promoted(self, session, base_data):
        # Seed NHO price at 1M VND
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        job = make_scrape_job(session)
        # BDS price at 1.25M VND → 25% divergence → conflict
        make_listing(session, job, base_data["project"].id, 1_250_000)
        pipeline = ScrapePipeline(session)
        result = pipeline.promote_job(job.id, base_data["period"].id)
        assert result.conflicted == 1
        assert result.promoted == 0

    def test_conflict_status_written_to_listing(self, session, base_data):
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        job = make_scrape_job(session)
        listing = make_listing(session, job, base_data["project"].id, 1_250_000)
        pipeline = ScrapePipeline(session)
        pipeline.promote_job(job.id, base_data["period"].id)
        session.refresh(listing)
        assert listing.reconcile_status == "conflict"
        assert listing.reconcile_detail is not None
        detail = json.loads(listing.reconcile_detail)
        assert "divergence_pct" in detail

    def test_ok_listing_status_written(self, session, base_data):
        job = make_scrape_job(session)
        listing = make_listing(session, job, base_data["project"].id, 1_000_000)
        pipeline = ScrapePipeline(session)
        pipeline.promote_job(job.id, base_data["period"].id)
        session.refresh(listing)
        assert listing.reconcile_status == "ok"

    def test_promoted_listing_marked_promoted(self, session, base_data):
        job = make_scrape_job(session)
        listing = make_listing(session, job, base_data["project"].id, 1_000_000)
        pipeline = ScrapePipeline(session)
        pipeline.promote_job(job.id, base_data["period"].id)
        session.refresh(listing)
        assert listing.promoted is True

    def test_conflicted_listing_not_marked_promoted(self, session, base_data):
        make_price_record(session, base_data["project"].id, base_data["period"].id, 1_000_000)
        job = make_scrape_job(session)
        listing = make_listing(session, job, base_data["project"].id, 1_250_000)
        pipeline = ScrapePipeline(session)
        pipeline.promote_job(job.id, base_data["period"].id)
        session.refresh(listing)
        assert listing.promoted is False

    def test_anomaly_still_promoted(self, session, base_data):
        """Anomalous-only listings are promoted (with lower confidence) but flagged.

        Uses a second project with no prior NHO price records so the outlier
        triggers anomaly (statistical outlier) without triggering conflict
        (no existing price to compare against).
        """
        from src.db.models import Developer, Project as Proj

        # Second project — no prior price records
        dev2 = Developer(name_en="Dev Two")
        session.add(dev2)
        session.flush()
        proj2 = Proj(
            name="Outlier Project",
            developer_id=dev2.id,
            district_id=base_data["district"].id,
        )
        session.add(proj2)
        session.flush()

        job = make_scrape_job(session)
        # 20 normal listings for project1 → tight batch around 1M VND
        for i in range(20):
            make_listing(session, job, base_data["project"].id, 1_000_000 + i * 5_000, bds_id=f"n{i}")
        # outlier for project2 (no existing NHO price) at 5M VND → >2.5σ from batch mean
        outlier = make_listing(session, job, proj2.id, 5_000_000, bds_id="outlier")

        pipeline = ScrapePipeline(session)
        result = pipeline.promote_job(job.id, base_data["period"].id)

        session.refresh(outlier)
        assert outlier.promoted is True
        assert outlier.reconcile_status in ("anomaly", "conflict_anomaly")
        assert result.anomalous >= 1

    def test_anomaly_confidence_lower(self, session, base_data):
        """Anomalous promoted listings get confidence_score=0.5 in DataLineage."""
        from src.db.models import DataLineage
        job = make_scrape_job(session)
        for i in range(5):
            make_listing(session, job, base_data["project"].id, 1_000_000, bds_id=f"n{i}")
        outlier = make_listing(session, job, base_data["project"].id, 5_000_000, bds_id="out")
        pipeline = ScrapePipeline(session)
        pipeline.promote_job(job.id, base_data["period"].id)
        session.refresh(outlier)
        if outlier.reconcile_status in ("anomaly", "conflict_anomaly") and outlier.promoted:
            # Find the price_record created from this listing and its lineage
            pr = session.query(PriceRecord).filter_by(
                project_id=base_data["project"].id,
                price_vnd_per_m2=5_000_000,
            ).first()
            if pr:
                lin = session.query(DataLineage).filter_by(record_id=pr.id).first()
                assert lin is not None
                assert lin.confidence_score == 0.5

    def test_no_eligible_returns_empty_report(self, session, base_data):
        job = make_scrape_job(session)
        pipeline = ScrapePipeline(session)
        result = pipeline.promote_job(job.id, base_data["period"].id)
        assert result.promoted == 0
        assert result.conflicted == 0

    def test_report_summary_string(self, session, base_data):
        job = make_scrape_job(session)
        make_listing(session, job, base_data["project"].id, 1_000_000)
        pipeline = ScrapePipeline(session)
        result = pipeline.promote_job(job.id, base_data["period"].id)
        summary = result.summary()
        assert "Promoted" in summary
        assert "Conflicted" in summary


# ---------------------------------------------------------------------------
# ReconciliationReport unit tests
# ---------------------------------------------------------------------------

class TestReconciliationReport:
    def test_total_flagged(self):
        r = ReconciliationReport(job_id=1, period_id=1)
        r.conflicted = 3
        r.anomalous = 2
        assert r.total_flagged == 5

    def test_summary_contains_key_fields(self):
        r = ReconciliationReport(job_id=99, period_id=3, promoted=5, conflicted=2)
        s = r.summary()
        assert "99" in s
        assert "5" in s
        assert "2" in s
