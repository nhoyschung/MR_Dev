"""Price reconciliation and anomaly detection for the scraping pipeline.

Compares BDS-scraped prices against NHO-PD database prices and flags:
  - Conflicts  : BDS vs NHO divergence exceeds CONFLICT_THRESHOLD (default 15 %)
  - Anomalies  : Price is more than ANOMALY_SIGMA (default 2.5σ) from the batch mean

These checks run inside promote_job() so that suspicious listings are held
for human review instead of silently overwriting source-report data.

Reconcile statuses written to scraped_listings.reconcile_status:
  'ok'               – passed both checks
  'conflict'         – BDS vs NHO divergence > threshold
  'anomaly'          – price is a statistical outlier in the batch
  'conflict_anomaly' – both flags triggered
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import PriceRecord, ReportPeriod


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

CONFLICT_THRESHOLD: float = 0.15    # 15 % divergence between BDS and NHO prices
ANOMALY_SIGMA: float = 2.5          # standard deviations from batch mean


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ReconcileOutcome:
    """Result of reconciling a single scraped listing."""
    status: str                          # 'ok' | 'conflict' | 'anomaly' | 'conflict_anomaly'
    conflict: bool = False
    anomaly: bool = False
    # Conflict details
    existing_price_vnd: Optional[float] = None
    scraped_price_vnd: Optional[float] = None
    divergence_pct: Optional[float] = None
    # Anomaly details
    batch_mean_vnd: Optional[float] = None
    batch_std_vnd: Optional[float] = None
    sigma_distance: Optional[float] = None

    def to_json(self) -> str:
        """Serialize to compact JSON for storage in reconcile_detail column."""
        return json.dumps({
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in self.__dict__.items()
            if v is not None and k != "status"
        })


@dataclass
class ReconciliationReport:
    """Summary returned by promote_job() after reconciliation."""
    job_id: int
    period_id: int
    promoted: int = 0
    conflicted: int = 0
    anomalous: int = 0
    skipped_no_price: int = 0
    skipped_no_match: int = 0
    details: list[dict] = field(default_factory=list)

    @property
    def total_flagged(self) -> int:
        return self.conflicted + self.anomalous

    def summary(self) -> str:
        lines = [
            f"Reconciliation Report — Job #{self.job_id}, Period #{self.period_id}",
            f"  Promoted   : {self.promoted}",
            f"  Conflicted : {self.conflicted}  (held for review)",
            f"  Anomalous  : {self.anomalous}  (promoted with flag)",
            f"  Skipped    : {self.skipped_no_price + self.skipped_no_match}  "
            f"(no price: {self.skipped_no_price}, no match: {self.skipped_no_match})",
        ]
        if self.details:
            lines.append("  Flagged listings:")
            for d in self.details:
                lines.append(
                    f"    [{d['status']}] project_id={d['project_id']}  "
                    f"listing_id={d['listing_id']}  {d.get('reason','')}"
                )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core reconciler
# ---------------------------------------------------------------------------

class PriceReconciler:
    """Checks scraped prices against database prices and batch statistics.

    Usage inside promote_job():
        reconciler = PriceReconciler(session)
        reconciler.build_batch_stats(price_list_vnd)     # call once with all eligible prices
        outcome = reconciler.reconcile(project_id, period_id, scraped_price_vnd)
    """

    def __init__(
        self,
        session: Session,
        conflict_threshold: float = CONFLICT_THRESHOLD,
        anomaly_sigma: float = ANOMALY_SIGMA,
    ) -> None:
        self.session = session
        self.conflict_threshold = conflict_threshold
        self.anomaly_sigma = anomaly_sigma
        self._batch_mean: Optional[float] = None
        self._batch_std: Optional[float] = None

    # ------------------------------------------------------------------
    # Batch statistics (anomaly baseline)
    # ------------------------------------------------------------------

    def build_batch_stats(self, prices_vnd: list[float]) -> None:
        """Pre-compute mean and std from all eligible prices in the current batch.

        Call this once before reconciling individual listings.
        Prices with value <= 0 are ignored.
        """
        clean = [p for p in prices_vnd if p and p > 0]
        if len(clean) < 2:
            self._batch_mean = None
            self._batch_std = None
            return
        n = len(clean)
        mean = sum(clean) / n
        variance = sum((p - mean) ** 2 for p in clean) / n
        self._batch_mean = mean
        self._batch_std = math.sqrt(variance)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _get_existing_price_vnd(
        self, project_id: int, period_id: int
    ) -> Optional[float]:
        """Return the most recently stored VND price for a (project, period) pair."""
        stmt = (
            select(PriceRecord.price_vnd_per_m2)
            .where(
                PriceRecord.project_id == project_id,
                PriceRecord.period_id == period_id,
                PriceRecord.price_vnd_per_m2.isnot(None),
            )
            .order_by(PriceRecord.id.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def check_conflict(
        self,
        project_id: int,
        period_id: int,
        scraped_price_vnd: float,
    ) -> tuple[bool, Optional[float], Optional[float], Optional[float]]:
        """Compare scraped price against stored NHO price.

        Returns:
            (is_conflict, existing_price, scraped_price, divergence_pct)
        """
        existing = self._get_existing_price_vnd(project_id, period_id)
        if existing is None or existing <= 0:
            return False, None, scraped_price_vnd, None

        divergence = abs(scraped_price_vnd - existing) / existing
        is_conflict = divergence > self.conflict_threshold
        return is_conflict, existing, scraped_price_vnd, round(divergence * 100, 2)

    def check_anomaly(
        self, scraped_price_vnd: float
    ) -> tuple[bool, Optional[float], Optional[float], Optional[float]]:
        """Check if a price is a statistical outlier relative to the batch.

        Returns:
            (is_anomaly, batch_mean, batch_std, sigma_distance)
        """
        if self._batch_mean is None or self._batch_std is None or self._batch_std == 0:
            return False, self._batch_mean, self._batch_std, None

        sigma_dist = abs(scraped_price_vnd - self._batch_mean) / self._batch_std
        is_anomaly = sigma_dist > self.anomaly_sigma
        return is_anomaly, self._batch_mean, self._batch_std, round(sigma_dist, 2)

    def reconcile(
        self,
        project_id: int,
        period_id: int,
        scraped_price_vnd: float,
    ) -> ReconcileOutcome:
        """Run both conflict and anomaly checks for a single listing.

        Returns a ReconcileOutcome with status and detailed breakdown.
        """
        is_conflict, existing, scraped, div_pct = self.check_conflict(
            project_id, period_id, scraped_price_vnd
        )
        is_anomaly, b_mean, b_std, sigma = self.check_anomaly(scraped_price_vnd)

        if is_conflict and is_anomaly:
            status = "conflict_anomaly"
        elif is_conflict:
            status = "conflict"
        elif is_anomaly:
            status = "anomaly"
        else:
            status = "ok"

        return ReconcileOutcome(
            status=status,
            conflict=is_conflict,
            anomaly=is_anomaly,
            existing_price_vnd=existing,
            scraped_price_vnd=scraped,
            divergence_pct=div_pct,
            batch_mean_vnd=round(b_mean, 0) if b_mean else None,
            batch_std_vnd=round(b_std, 0) if b_std else None,
            sigma_distance=sigma,
        )
