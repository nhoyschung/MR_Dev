"""Seeder for project_blocks from extracted JSON."""

from src.db.models import ProjectBlock
from src.seeders.base_seeder import LineageAwareSeeder


class BlockSeeder(LineageAwareSeeder):
    """Seeds project_blocks from casestudy extraction."""

    def validate(self) -> bool:
        data = self.load_json("extracted/casestudy_blocks.json")
        return len(data) > 0

    def seed(self) -> int:
        count = 0
        data = self.load_json("extracted/casestudy_blocks.json")

        for record in data:
            project = self._find_project(record["project_name"])
            if not project:
                continue

            meta = record.get("_meta", {})
            source_report = self._get_source_report(meta.get("source_file", ""))
            source_report_id = source_report.id if source_report else None

            # Parse floor count from block data
            floors = record.get("floors")
            total_units = None

            if source_report_id:
                _, created = self._get_or_create_with_lineage(
                    ProjectBlock,
                    table_name="project_blocks",
                    source_report_id=source_report_id,
                    page_number=meta.get("page"),
                    confidence=meta.get("confidence", 0.8),
                    project_id=project.id,
                    block_name=record["block_name"],
                    defaults={"floors": floors, "total_units": total_units},
                )
            else:
                _, created = self._get_or_create(
                    ProjectBlock,
                    project_id=project.id,
                    block_name=record["block_name"],
                    defaults={"floors": floors, "total_units": total_units},
                )

            if created:
                count += 1

        self.session.commit()
        return count
