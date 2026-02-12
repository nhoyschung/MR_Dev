"""Seeder for district_metrics from extracted JSON + computed aggregates."""

from typing import Any

from sqlalchemy import func

from src.db.models import (
    City,
    District,
    DistrictMetric,
    PriceRecord,
    Project,
    ReportPeriod,
    SupplyRecord,
)
from src.seeders.base_seeder import LineageAwareSeeder


class DistrictMetricSeeder(LineageAwareSeeder):
    """Seeds district_metrics from extraction and computes aggregates."""

    def validate(self) -> bool:
        return True

    def seed(self) -> int:
        count = 0

        # Phase 1: Seed extracted metrics from JSON
        try:
            data = self.load_json("extracted/district_metrics.json")
            count += self._seed_extracted(data)
        except FileNotFoundError:
            pass

        # Phase 2: Compute aggregates from existing DB data
        count += self._compute_aggregates()

        self.session.commit()
        return count

    def _seed_extracted(self, data: list[dict[str, Any]]) -> int:
        count = 0
        period = (
            self.session.query(ReportPeriod)
            .filter_by(year=2024, half="H1")
            .first()
        )
        if not period:
            return 0

        for record in data:
            city_name = record.get("city")
            if not city_name:
                continue

            city = self.session.query(City).filter_by(name_en=city_name).first()
            if not city:
                continue

            # Find the first district in this city as a placeholder
            # (extracted metrics are city-level, stored at district level)
            districts = (
                self.session.query(District)
                .filter_by(city_id=city.id)
                .all()
            )
            if not districts:
                continue

            # Use first district for city-level metrics
            district = districts[0]

            meta = record.get("_meta", {})
            source_report = self._get_source_report(meta.get("source_file", ""))
            source_report_id = source_report.id if source_report else None

            metric_type = record["metric_type"]
            value_numeric = record.get("value_numeric")
            value_text = record.get("value_text")

            if source_report_id:
                _, created = self._get_or_create_with_lineage(
                    DistrictMetric,
                    table_name="district_metrics",
                    source_report_id=source_report_id,
                    page_number=meta.get("page"),
                    confidence=meta.get("confidence", 0.8),
                    district_id=district.id,
                    period_id=period.id,
                    metric_type=metric_type,
                    defaults={
                        "value_numeric": value_numeric,
                        "value_text": value_text,
                    },
                )
            else:
                _, created = self._get_or_create(
                    DistrictMetric,
                    district_id=district.id,
                    period_id=period.id,
                    metric_type=metric_type,
                    defaults={
                        "value_numeric": value_numeric,
                        "value_text": value_text,
                    },
                )

            if created:
                count += 1

        return count

    def _compute_aggregates(self) -> int:
        """Compute district-level metrics from existing price and supply data."""
        count = 0

        period = (
            self.session.query(ReportPeriod)
            .filter_by(year=2024, half="H1")
            .first()
        )
        if not period:
            return 0

        districts = self.session.query(District).all()

        for district in districts:
            # Compute average price for projects in this district
            avg_price_result = (
                self.session.query(func.avg(PriceRecord.price_usd_per_m2))
                .join(Project, PriceRecord.project_id == Project.id)
                .filter(
                    Project.district_id == district.id,
                    PriceRecord.period_id == period.id,
                    PriceRecord.price_usd_per_m2.isnot(None),
                )
                .scalar()
            )

            if avg_price_result:
                _, created = self._get_or_create(
                    DistrictMetric,
                    district_id=district.id,
                    period_id=period.id,
                    metric_type="avg_price",
                    defaults={
                        "value_numeric": round(float(avg_price_result), 2),
                        "value_text": "Computed from price_records",
                    },
                )
                if created:
                    count += 1

            # Compute project count
            project_count = (
                self.session.query(func.count(Project.id))
                .filter(Project.district_id == district.id)
                .scalar()
            )

            if project_count and project_count > 0:
                _, created = self._get_or_create(
                    DistrictMetric,
                    district_id=district.id,
                    period_id=period.id,
                    metric_type="supply_count",
                    defaults={
                        "value_numeric": float(project_count),
                        "value_text": "Computed from projects table",
                    },
                )
                if created:
                    count += 1

        return count
