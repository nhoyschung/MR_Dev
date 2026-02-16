"""Seeder for price_change_factors from extracted JSON."""

from src.db.models import PriceChangeFactor, PriceRecord
from src.seeders.base_seeder import LineageAwareSeeder


class PriceFactorSeeder(LineageAwareSeeder):
    """Seeds price_change_factors linking to existing price_records."""

    def validate(self) -> bool:
        try:
            data = self.load_json("extracted/price_factors.json")
            return len(data) > 0
        except FileNotFoundError:
            return False

    def seed(self) -> int:
        count = 0

        try:
            data = self.load_json("extracted/price_factors.json")
        except FileNotFoundError:
            return 0

        for record in data:
            # Find the project
            project = self._find_project(record["project_name"])
            if not project:
                continue

            # Find associated price record for this project
            price_record = (
                self.session.query(PriceRecord)
                .filter_by(project_id=project.id)
                .first()
            )
            if not price_record:
                continue

            meta = record.get("_meta", {})
            source_report = self._get_source_report(meta.get("source_file", ""))
            source_report_id = source_report.id if source_report else None

            factor_type = record["factor_type"]
            factor_category = record["factor_category"]
            description = record.get("description")

            if source_report_id:
                _, created = self._get_or_create_with_lineage(
                    PriceChangeFactor,
                    table_name="price_change_factors",
                    source_report_id=source_report_id,
                    page_number=meta.get("page"),
                    confidence=meta.get("confidence", 0.8),
                    price_record_id=price_record.id,
                    factor_type=factor_type,
                    factor_category=factor_category,
                    defaults={"description": description},
                )
            else:
                _, created = self._get_or_create(
                    PriceChangeFactor,
                    price_record_id=price_record.id,
                    factor_type=factor_type,
                    factor_category=factor_category,
                    defaults={"description": description},
                )

            if created:
                count += 1

        self.session.commit()
        return count
