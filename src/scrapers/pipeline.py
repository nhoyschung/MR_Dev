"""Scrape → parse → validate → match → store pipeline."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.db.models import DataLineage, PriceRecord, ScrapedListing, ScrapeJob, SourceReport
from src.scrapers.models import ScrapedListingData, ScrapeJobResult
from src.utils.project_matcher import ProjectMatcher
from src.utils.reconciler import PriceReconciler, ReconciliationReport

logger = logging.getLogger(__name__)


class ScrapePipeline:
    """Pipeline to validate, match, and store scraped listing data.

    Flow:
        1. Receive raw dicts from scrapers
        2. Validate through Pydantic schemas
        3. Match project names to existing DB projects
        4. Save to scraped_listings staging table
        5. Optionally promote to price_records
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._matcher: Optional[ProjectMatcher] = None

    @property
    def matcher(self) -> ProjectMatcher:
        """Lazy-init project matcher."""
        if self._matcher is None:
            self._matcher = ProjectMatcher(self.session)
        return self._matcher

    def create_job(self, job_type: str, target_url: Optional[str] = None) -> ScrapeJob:
        """Create a new scrape job record."""
        job = ScrapeJob(
            job_type=job_type,
            target_url=target_url,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(job)
        self.session.flush()
        return job

    def complete_job(
        self,
        job: ScrapeJob,
        items_found: int,
        items_saved: int,
        error_message: Optional[str] = None,
    ) -> ScrapeJobResult:
        """Mark a job as completed and return summary."""
        job.status = "failed" if error_message else "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.items_found = items_found
        job.items_saved = items_saved
        job.error_message = error_message
        self.session.commit()

        return ScrapeJobResult(
            job_type=job.job_type,
            target_url=job.target_url,
            status=job.status,
            started_at=job.started_at,
            completed_at=job.completed_at,
            items_found=items_found,
            items_saved=items_saved,
            errors=[error_message] if error_message else [],
        )

    def process_listings(
        self, raw_items: list[dict[str, Any]], job: ScrapeJob
    ) -> tuple[int, int]:
        """Validate and store listing data. Returns (valid_count, saved_count)."""
        valid_count = 0
        saved_count = 0

        for raw in raw_items:
            # Step 1: Validate
            try:
                listing_data = ScrapedListingData(**raw)
            except ValidationError as e:
                logger.warning("Validation failed: %s", e.errors())
                continue
            valid_count += 1

            # Step 2: Check for duplicate by bds_listing_id
            if listing_data.bds_listing_id:
                existing = (
                    self.session.query(ScrapedListing)
                    .filter_by(bds_listing_id=listing_data.bds_listing_id)
                    .first()
                )
                if existing:
                    logger.debug("Duplicate listing: %s", listing_data.bds_listing_id)
                    continue

            # Step 3: Match to existing project
            matched_project_id = None
            if listing_data.project_name:
                pid, confidence = self.matcher.match(listing_data.project_name)
                if pid is not None and confidence >= 0.5:
                    matched_project_id = pid

            # Step 4: Save to staging
            listing = ScrapedListing(
                scrape_job_id=job.id,
                bds_listing_id=listing_data.bds_listing_id,
                project_name=listing_data.project_name,
                district_name=listing_data.district_name,
                city_name=listing_data.city_name,
                price_raw=listing_data.price_raw,
                price_vnd=listing_data.price_vnd,
                price_per_sqm=listing_data.price_per_sqm,
                area_sqm=listing_data.area_sqm,
                bedrooms=listing_data.bedrooms,
                bathrooms=listing_data.bathrooms,
                floor=listing_data.floor,
                direction=listing_data.direction,
                listing_url=listing_data.listing_url,
                scraped_at=datetime.now(timezone.utc),
                matched_project_id=matched_project_id,
                promoted=False,
            )
            self.session.add(listing)
            saved_count += 1

        self.session.flush()
        return valid_count, saved_count

    def promote_job(self, job_id: int, period_id: int) -> ReconciliationReport:
        """Promote staged listings from a job to price_records.

        Runs reconciliation before promoting each listing:
          - Conflict  : BDS vs NHO price diverges > 15 % → listing held, NOT promoted
          - Anomaly   : price is > 2.5 σ from batch mean → promoted but flagged
          - OK        : promoted normally

        Returns a ReconciliationReport with counts and per-listing details.
        """
        report = ReconciliationReport(job_id=job_id, period_id=period_id)

        eligible = (
            self.session.query(ScrapedListing)
            .filter(
                ScrapedListing.scrape_job_id == job_id,
                ScrapedListing.matched_project_id.isnot(None),
                ScrapedListing.price_per_sqm.isnot(None),
                ScrapedListing.promoted == False,  # noqa: E712
            )
            .all()
        )

        # Listings missing a match or price — count but skip
        all_pending = (
            self.session.query(ScrapedListing)
            .filter(
                ScrapedListing.scrape_job_id == job_id,
                ScrapedListing.promoted == False,  # noqa: E712
            )
            .all()
        )
        report.skipped_no_match = sum(
            1 for l in all_pending if l.matched_project_id is None
        )
        report.skipped_no_price = sum(
            1 for l in all_pending
            if l.matched_project_id is not None and l.price_per_sqm is None
        )

        if not eligible:
            self.session.commit()
            return report

        # ── Pass 1: reconcile ALL listings against pre-existing DB prices ────
        # Batch stats are built from the full eligible set BEFORE any promotions.
        # This prevents within-job promotions from affecting the conflict check
        # of subsequent listings in the same batch.
        reconciler = PriceReconciler(self.session)
        reconciler.build_batch_stats([l.price_per_sqm for l in eligible])

        outcomes: list[tuple[ScrapedListing, object]] = []
        for listing in eligible:
            outcome = reconciler.reconcile(
                project_id=listing.matched_project_id,
                period_id=period_id,
                scraped_price_vnd=listing.price_per_sqm,
            )
            listing.reconcile_status = outcome.status
            listing.reconcile_detail = outcome.to_json()
            outcomes.append((listing, outcome))

        # Collect conflict / anomaly details
        for listing, outcome in outcomes:
            if outcome.conflict:
                report.conflicted += 1
                report.details.append({
                    "listing_id": listing.id,
                    "project_id": listing.matched_project_id,
                    "status": outcome.status,
                    "reason": (
                        f"BDS={outcome.scraped_price_vnd:,.0f} VND vs "
                        f"NHO={outcome.existing_price_vnd:,.0f} VND "
                        f"({outcome.divergence_pct:.1f}% divergence)"
                    ),
                })
                logger.warning(
                    "Conflict: listing %d project %d — %.1f%% divergence",
                    listing.id, listing.matched_project_id, outcome.divergence_pct or 0,
                )
            elif outcome.anomaly:
                report.details.append({
                    "listing_id": listing.id,
                    "project_id": listing.matched_project_id,
                    "status": outcome.status,
                    "reason": (
                        f"Price {outcome.scraped_price_vnd:,.0f} VND is "
                        f"{outcome.sigma_distance:.1f}σ from batch mean "
                        f"{outcome.batch_mean_vnd:,.0f} VND"
                    ),
                })

        # ── Pass 2: promote non-conflicted listings ───────────────────────────
        source_report = SourceReport(
            filename=f"scrape_job_{job_id}",
            report_type="web_scrape",
            ingested_at=datetime.now(timezone.utc),
            status="completed",
        )
        self.session.add(source_report)
        self.session.flush()

        for listing, outcome in outcomes:
            if outcome.conflict:
                continue  # held for review

            price_record = PriceRecord(
                project_id=listing.matched_project_id,
                period_id=period_id,
                price_vnd_per_m2=listing.price_per_sqm,
                price_incl_vat=True,
                source_report=f"batdongsan.com.vn scrape job #{job_id}",
                data_source="bds_scrape",
            )
            self.session.add(price_record)
            self.session.flush()

            confidence = 0.5 if outcome.anomaly else 0.7
            lineage = DataLineage(
                table_name="price_records",
                record_id=price_record.id,
                source_report_id=source_report.id,
                confidence_score=confidence,
                extracted_at=datetime.now(timezone.utc),
            )
            self.session.add(lineage)

            listing.promoted = True
            report.promoted += 1
            if outcome.anomaly:
                report.anomalous += 1

        self.session.commit()
        logger.info(
            "Job %d: promoted=%d conflicted=%d anomalous=%d",
            job_id, report.promoted, report.conflicted, report.anomalous,
        )
        return report
