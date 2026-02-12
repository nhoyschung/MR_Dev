"""Seeder for market_segment_summaries from extracted JSON."""

from typing import Any

from src.db.models import City, MarketSegmentSummary, ReportPeriod
from src.seeders.base_seeder import LineageAwareSeeder


class MarketSegmentSeeder(LineageAwareSeeder):
    """Seeds market_segment_summaries from price pass extraction."""

    def validate(self) -> bool:
        try:
            data = self.load_json("extracted/segment_summaries.json")
            return len(data) > 0
        except FileNotFoundError:
            return False

    def seed(self) -> int:
        count = 0

        try:
            data = self.load_json("extracted/segment_summaries.json")
        except FileNotFoundError:
            return 0

        # Default period: 2024-H1
        period = (
            self.session.query(ReportPeriod)
            .filter_by(year=2024, half="H1")
            .first()
        )
        if not period:
            return 0

        for record in data:
            city_name = record.get("city")
            if not city_name or city_name == "National":
                continue

            # Try exact match first, then partial match for names like "Da Nang"
            city = (
                self.session.query(City)
                .filter_by(name_en=city_name)
                .first()
            )
            if not city:
                city = (
                    self.session.query(City)
                    .filter(City.name_en.ilike(f"%{city_name}%"))
                    .first()
                )
            if not city:
                continue

            meta = record.get("_meta", {})
            source_report = self._get_source_report(meta.get("source_file", ""))
            source_report_id = source_report.id if source_report else None

            grade_code = record.get("grade_code")
            segment = record.get("segment")

            defaults = {
                "segment": segment,
                "total_supply": None,
                "total_sold": None,
                "absorption_rate": None,
                "new_launches": None,
            }

            if source_report_id:
                _, created = self._get_or_create_with_lineage(
                    MarketSegmentSummary,
                    table_name="market_segment_summaries",
                    source_report_id=source_report_id,
                    page_number=meta.get("page"),
                    confidence=meta.get("confidence", 0.8),
                    city_id=city.id,
                    period_id=period.id,
                    grade_code=grade_code,
                    defaults=defaults,
                )
            else:
                _, created = self._get_or_create(
                    MarketSegmentSummary,
                    city_id=city.id,
                    period_id=period.id,
                    grade_code=grade_code,
                    defaults=defaults,
                )

            if created:
                count += 1

        self.session.commit()
        return count
