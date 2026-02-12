"""Seeder for project_sales_points from extracted JSON."""

from typing import Any

from src.db.models import Project, ProjectSalesPoint
from src.seeders.base_seeder import LineageAwareSeeder


class SalesPointSeeder(LineageAwareSeeder):
    """Seeds project_sales_points from casestudy extraction."""

    def validate(self) -> bool:
        try:
            data = self.load_json("extracted/casestudy_sales_points.json")
            return len(data) > 0
        except FileNotFoundError:
            return False

    def seed(self) -> int:
        count = 0

        try:
            data = self.load_json("extracted/casestudy_sales_points.json")
        except FileNotFoundError:
            return 0

        for i, record in enumerate(data):
            project = self._find_project(record["project_name"])
            if not project:
                continue

            meta = record.get("_meta", {})
            source_report = self._get_source_report(meta.get("source_file", ""))
            source_report_id = source_report.id if source_report else None

            category = record["category"]
            description = record["description"]

            if source_report_id:
                _, created = self._get_or_create_with_lineage(
                    ProjectSalesPoint,
                    table_name="project_sales_points",
                    source_report_id=source_report_id,
                    page_number=meta.get("page"),
                    confidence=meta.get("confidence", 0.8),
                    project_id=project.id,
                    category=category,
                    description=description,
                    defaults={"ranking": i + 1},
                )
            else:
                _, created = self._get_or_create(
                    ProjectSalesPoint,
                    project_id=project.id,
                    category=category,
                    description=description,
                    defaults={"ranking": i + 1},
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
