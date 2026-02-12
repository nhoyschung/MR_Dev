"""Seeder for sales_statuses from extracted JSON."""

from typing import Any

from src.db.models import Project, ReportPeriod, SalesStatus
from src.seeders.base_seeder import LineageAwareSeeder


class SalesStatusSeeder(LineageAwareSeeder):
    """Seeds sales_statuses from market pass extraction."""

    def validate(self) -> bool:
        try:
            data = self.load_json("extracted/market_sales_statuses.json")
            return len(data) > 0
        except FileNotFoundError:
            return False

    def seed(self) -> int:
        count = 0

        try:
            data = self.load_json("extracted/market_sales_statuses.json")
        except FileNotFoundError:
            return 0

        # Default period: 2024-H1 (matches the main analysis period)
        period = (
            self.session.query(ReportPeriod)
            .filter_by(year=2024, half="H1")
            .first()
        )
        if not period:
            return 0

        for record in data:
            project = self._find_project(record["project_name"])
            if not project:
                continue

            meta = record.get("_meta", {})
            source_report = self._get_source_report(meta.get("source_file", ""))
            source_report_id = source_report.id if source_report else None

            defaults = {
                "launched_units": record.get("launched_units"),
                "sold_units": record.get("sold_units"),
                "available_units": record.get("available_units"),
                "sales_rate_pct": record.get("sales_rate_pct"),
            }

            if source_report_id:
                _, created = self._get_or_create_with_lineage(
                    SalesStatus,
                    table_name="sales_statuses",
                    source_report_id=source_report_id,
                    page_number=meta.get("page"),
                    confidence=meta.get("confidence", 0.8),
                    project_id=project.id,
                    period_id=period.id,
                    defaults=defaults,
                )
            else:
                _, created = self._get_or_create(
                    SalesStatus,
                    project_id=project.id,
                    period_id=period.id,
                    defaults=defaults,
                )

            if created:
                count += 1

        self.session.commit()
        return count

    def _find_project(self, name: str) -> Any:
        return (
            self.session.query(Project)
            .filter(Project.name.ilike(f"%{name}%"))
            .first()
        )
