"""Seeder for competitor_comparisons from DB project pairings."""

from itertools import combinations
from typing import Any

from src.db.models import CompetitorComparison, Project, ReportPeriod
from src.config import COMPARISON_DIMENSIONS
from src.seeders.base_seeder import BaseSeeder


class CompetitorSeeder(BaseSeeder):
    """Seeds competitor_comparisons by pairing projects in the same district/grade."""

    def validate(self) -> bool:
        return True

    def seed(self) -> int:
        count = 0

        period = (
            self.session.query(ReportPeriod)
            .filter_by(year=2024, half="H1")
            .first()
        )
        if not period:
            return 0

        # Group projects by (district_id, grade_primary)
        projects = (
            self.session.query(Project)
            .filter(
                Project.district_id.isnot(None),
                Project.grade_primary.isnot(None),
            )
            .all()
        )

        groups: dict[tuple[int, str], list[Project]] = {}
        for p in projects:
            key = (p.district_id, p.grade_primary)
            groups.setdefault(key, []).append(p)

        for (district_id, grade), group in groups.items():
            if len(group) < 2:
                continue

            # Create pairings (limit to avoid combinatorial explosion)
            pairs = list(combinations(group, 2))[:10]

            for p1, p2 in pairs:
                # Create one comparison per pair with "location" dimension
                _, created = self._get_or_create(
                    CompetitorComparison,
                    subject_project_id=p1.id,
                    competitor_project_id=p2.id,
                    period_id=period.id,
                    dimension="location",
                    defaults={
                        "analysis_notes": f"Same district ({district_id}) and grade ({grade})",
                    },
                )
                if created:
                    count += 1

        self.session.commit()
        return count
