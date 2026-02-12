"""Seeder for unit_types from extracted JSON (casestudy + market passes)."""

from typing import Any

from src.db.models import Project, UnitType
from src.seeders.base_seeder import LineageAwareSeeder


class UnitTypeSeeder(LineageAwareSeeder):
    """Seeds unit_types merging casestudy and market pass data."""

    JSON_FILES = [
        "extracted/casestudy_unit_types.json",
        "extracted/market_unit_types.json",
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

                type_name = record["type_name"]
                defaults = {
                    "gross_area_m2": record.get("gross_area_m2"),
                    "typical_layout_description": record.get(
                        "typical_layout_description",
                        f"{record.get('area_min', '')}-{record.get('area_max', '')}m2"
                        if record.get("area_min") != record.get("area_max")
                        else f"{record.get('area_min', '')}m2",
                    ),
                }

                if source_report_id:
                    _, created = self._get_or_create_with_lineage(
                        UnitType,
                        table_name="unit_types",
                        source_report_id=source_report_id,
                        page_number=meta.get("page"),
                        confidence=meta.get("confidence", 0.8),
                        project_id=project.id,
                        type_name=type_name,
                        defaults=defaults,
                    )
                else:
                    _, created = self._get_or_create(
                        UnitType,
                        project_id=project.id,
                        type_name=type_name,
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
