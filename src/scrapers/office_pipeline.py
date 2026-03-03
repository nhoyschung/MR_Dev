"""Validate → match → stage → promote pipeline for office lease listings.

Flow:
    1. Raw dicts from OfficeScraper
    2. Validate via ScrapedOfficeListingData (Pydantic)
    3. Fuzzy-match building name to OfficeProject
    4. Save to scraped_office_listings staging table
    5. promote_job(): write to office_leasing_records
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.db.models import (
    OfficeLeasingRecord,
    OfficeProject,
    ReportPeriod,
    ScrapedOfficeListing,
    ScrapeJob,
    SourceReport,
    DataLineage,
)
from src.scrapers.models import ScrapedOfficeListingData, ScrapeJobResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Office building name matcher
# ---------------------------------------------------------------------------

class OfficeMatcher:
    """Fuzzy name matcher for office building names → OfficeProject.id."""

    def __init__(self, session: Session) -> None:
        self._entries: list[tuple[int, str]] = []  # (id, normalized_name)
        self._load(session)

    def _load(self, session: Session) -> None:
        projects = session.query(OfficeProject).all()
        self._entries = [(p.id, self._normalize(p.name)) for p in projects]

    @staticmethod
    def _normalize(name: str) -> str:
        import re
        name = name.lower().strip()
        # Remove common words that don't help matching
        for word in ("tower", "building", "center", "complex", "plaza", "tòa nhà"):
            name = name.replace(word, "").strip()
        # Remove punctuation
        name = re.sub(r"[^a-z0-9\s]", " ", name)
        return re.sub(r"\s+", " ", name).strip()

    def match(self, name: str) -> tuple[Optional[int], float]:
        """Return (office_project_id, confidence). None if no match found."""
        if not name or not self._entries:
            return None, 0.0

        normalized = self._normalize(name)

        # Tier 1: exact match
        for pid, pnorm in self._entries:
            if pnorm == normalized:
                return pid, 1.0

        # Tier 2: one is a substring of the other
        best_id: Optional[int] = None
        best_ratio = 0.0
        for pid, pnorm in self._entries:
            if pnorm in normalized or normalized in pnorm:
                shorter = min(len(pnorm), len(normalized))
                longer = max(len(pnorm), len(normalized))
                ratio = shorter / longer if longer > 0 else 0.0
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_id = pid

        if best_id and best_ratio >= 0.4:
            return best_id, best_ratio * 0.8  # cap at 0.8 for substring match

        return None, 0.0


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class OfficePipeline:
    """Validate, stage, and promote scraped office listings."""

    MIN_CONFIDENCE = 0.4

    def __init__(self, session: Session) -> None:
        self.session = session
        self._matcher: Optional[OfficeMatcher] = None

    @property
    def matcher(self) -> OfficeMatcher:
        if self._matcher is None:
            self._matcher = OfficeMatcher(self.session)
        return self._matcher

    def create_job(self, target_url: Optional[str] = None) -> ScrapeJob:
        job = ScrapeJob(
            job_type="office_listing",
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
        """Validate and save listings to staging. Returns (valid, saved)."""
        valid_count = 0
        saved_count = 0

        for raw in raw_items:
            # Validate
            try:
                data = ScrapedOfficeListingData(**raw)
            except ValidationError as e:
                logger.warning("Office listing validation failed: %s", e.errors())
                continue
            valid_count += 1

            # Skip if no useful data
            if not data.building_name:
                continue

            # Dedup by listing_id
            if data.listing_id:
                existing = (
                    self.session.query(ScrapedOfficeListing)
                    .filter_by(listing_id=data.listing_id)
                    .first()
                )
                if existing:
                    logger.debug("Duplicate office listing: %s", data.listing_id)
                    continue

            # Match to OfficeProject
            matched_id = None
            if data.building_name:
                pid, confidence = self.matcher.match(data.building_name)
                if pid is not None and confidence >= self.MIN_CONFIDENCE:
                    matched_id = pid

            listing = ScrapedOfficeListing(
                scrape_job_id=job.id,
                listing_id=data.listing_id,
                building_name=data.building_name,
                address=data.address,
                district_name=data.district_name,
                city_name=data.city_name,
                rent_raw=data.rent_raw,
                rent_vnd_per_m2_month=data.rent_vnd_per_m2_month,
                rent_usd_per_m2_month=data.rent_usd_per_m2_month,
                area_m2=data.area_m2,
                floor=data.floor,
                listing_url=data.listing_url,
                scraped_at=datetime.now(timezone.utc),
                matched_office_project_id=matched_id,
                promoted=False,
            )
            self.session.add(listing)
            saved_count += 1

        self.session.flush()
        return valid_count, saved_count

    def promote_job(self, job_id: int, period_id: int) -> dict:
        """Promote staged office listings to office_leasing_records.

        Idempotent per (office_project_id, period_id): if a record already
        exists, the listing is skipped (not duplicated).

        Returns a summary dict with promoted/skipped/conflict counts.
        """
        summary = {
            "job_id": job_id,
            "period_id": period_id,
            "promoted": 0,
            "skipped_no_match": 0,
            "skipped_no_price": 0,
            "skipped_duplicate": 0,
        }

        eligible = (
            self.session.query(ScrapedOfficeListing)
            .filter(
                ScrapedOfficeListing.scrape_job_id == job_id,
                ScrapedOfficeListing.promoted == False,  # noqa: E712
            )
            .all()
        )

        source_report = SourceReport(
            filename=f"office_scrape_job_{job_id}",
            report_type="web_scrape",
            ingested_at=datetime.now(timezone.utc),
            status="completed",
        )
        self.session.add(source_report)
        self.session.flush()

        for listing in eligible:
            # Must be matched
            if listing.matched_office_project_id is None:
                summary["skipped_no_match"] += 1
                listing.reconcile_status = "skipped_no_match"
                continue

            # Must have rent data
            has_rent = (
                listing.rent_vnd_per_m2_month is not None
                or listing.rent_usd_per_m2_month is not None
            )
            if not has_rent:
                summary["skipped_no_price"] += 1
                listing.reconcile_status = "skipped_no_price"
                continue

            # Idempotency: skip if already have a leasing record for this (project, period)
            existing = (
                self.session.query(OfficeLeasingRecord)
                .filter_by(
                    office_project_id=listing.matched_office_project_id,
                    period_id=period_id,
                )
                .first()
            )
            if existing:
                # Update if we have new rent data that's more specific
                if (
                    listing.rent_usd_per_m2_month
                    and existing.rent_min_usd is None
                ):
                    existing.rent_min_usd = listing.rent_usd_per_m2_month
                    existing.rent_max_usd = listing.rent_usd_per_m2_month
                summary["skipped_duplicate"] += 1
                listing.reconcile_status = "duplicate"
                listing.promoted = True
                continue

            # Compute rent values to store
            rent_min = rent_max = None
            if listing.rent_usd_per_m2_month:
                rent_min = rent_max = listing.rent_usd_per_m2_month
            elif listing.rent_vnd_per_m2_month:
                # Rough USD conversion (use 25,300 VND/USD as reference)
                _EXCHANGE = 25_300
                rent_usd = listing.rent_vnd_per_m2_month / _EXCHANGE
                rent_min = rent_max = round(rent_usd, 2)

            record = OfficeLeasingRecord(
                office_project_id=listing.matched_office_project_id,
                period_id=period_id,
                rent_min_usd=rent_min,
                rent_max_usd=rent_max,
                management_fee_usd=None,
                occupancy_rate_pct=None,
                area_basis="NLA",
                notes=(
                    f"Scraped from BDS job #{job_id}. "
                    f"Raw: {listing.rent_raw}"
                ),
            )
            self.session.add(record)
            self.session.flush()

            lineage = DataLineage(
                table_name="office_leasing_records",
                record_id=record.id,
                source_report_id=source_report.id,
                confidence_score=0.6,
                extracted_at=datetime.now(timezone.utc),
            )
            self.session.add(lineage)

            listing.promoted = True
            listing.reconcile_status = "ok"
            summary["promoted"] += 1

        self.session.commit()
        logger.info(
            "Office promote job %d: promoted=%d skipped_no_match=%d "
            "skipped_no_price=%d skipped_dup=%d",
            job_id,
            summary["promoted"],
            summary["skipped_no_match"],
            summary["skipped_no_price"],
            summary["skipped_duplicate"],
        )
        return summary
