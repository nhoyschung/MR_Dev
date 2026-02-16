"""Seeder for project_facilities from extracted JSON."""

from src.db.models import ProjectFacility
from src.seeders.base_seeder import LineageAwareSeeder


class FacilitySeeder(LineageAwareSeeder):
    """Seeds project_facilities from casestudy and market pass extraction."""

    JSON_FILES = [
        "extracted/casestudy_facilities.json",
        "extracted/market_facilities.json",
    ]

    def validate(self) -> bool:
        for filename in self.JSON_FILES:
            try:
                data = self.load_json(filename)
                if len(data) > 0:
                    return True
            except FileNotFoundError:
                continue
        return False

    def seed(self) -> int:
        count = 0

        for filename in self.JSON_FILES:
            try:
                data = self.load_json(filename)
            except FileNotFoundError:
                continue

            for record in data:
                project = self._find_project(record["project_name"])
                if not project:
                    continue

                meta = record.get("_meta", {})
                source_report = self._get_source_report(meta.get("source_file", ""))
                source_report_id = source_report.id if source_report else None

                facility_type = record["facility_type"]
                description = record.get("description", "")

                if source_report_id:
                    _, created = self._get_or_create_with_lineage(
                        ProjectFacility,
                        table_name="project_facilities",
                        source_report_id=source_report_id,
                        page_number=meta.get("page"),
                        confidence=meta.get("confidence", 0.8),
                        project_id=project.id,
                        facility_type=facility_type,
                        defaults={"description": description},
                    )
                else:
                    _, created = self._get_or_create(
                        ProjectFacility,
                        project_id=project.id,
                        facility_type=facility_type,
                        defaults={"description": description},
                    )

                if created:
                    count += 1

        self.session.commit()
        return count
