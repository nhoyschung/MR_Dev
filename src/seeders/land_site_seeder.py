"""Unified land site seeder: LandSite + child tables (zones, competitors, etc.)."""

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import (
    LandSite, SiteZone, SitePlanningIndicator, SiteSpecification,
    SiteNearbyFacility, SiteSwotItem, SiteCompetitor, SitePriceTarget,
    SiteTargetCustomer, SiteDevelopmentPhase, SiteView,
    SiteRecommendedProject, CaseStudyProject, CaseStudyPhase,
    CaseStudyUnitType, DesignGuideline, DesignProductSpec,
    DesignCaseStudy, SportParkFacility,
)
from src.seeders.base_seeder import BaseSeeder


class LandSiteSeeder(BaseSeeder):
    """Seeds land_sites and all child tables from JSON files."""

    # Map of (filename, model_class, site_name_key) for child tables
    CHILD_TABLES = [
        ("site_zones.json", SiteZone, "site_name"),
        ("site_competitors.json", SiteCompetitor, "site_name"),
        ("site_price_targets.json", SitePriceTarget, "site_name"),
        ("site_target_customers.json", SiteTargetCustomer, "site_name"),
        ("site_specifications.json", SiteSpecification, "site_name"),
        ("site_views.json", SiteView, "site_name"),
        ("site_recommended_projects.json", SiteRecommendedProject, "site_name"),
        ("sport_park_facilities.json", SportParkFacility, None),
    ]

    def validate(self) -> bool:
        path = self.seed_dir / "land_sites.json"
        if not path.exists():
            raise FileNotFoundError(f"Seed file not found: {path}")
        return True

    def seed(self) -> int:
        count = 0
        count += self._seed_land_sites()
        for filename, model_class, site_key in self.CHILD_TABLES:
            count += self._seed_child_table(filename, model_class, site_key)
        count += self._seed_case_studies()
        count += self._seed_design_guidelines()
        self.session.commit()
        return count

    def _seed_land_sites(self) -> int:
        data = self.load_json("land_sites.json")
        count = 0
        for row in data:
            name = row["name"]
            if self._exists(LandSite, name=name):
                continue
            site = LandSite(**row)
            self.session.add(site)
            self.session.flush()
            count += 1
        return count

    def _resolve_site(self, name: str) -> LandSite | None:
        return self.session.query(LandSite).filter_by(name=name).first()

    def _seed_child_table(
        self, filename: str, model_class: type, site_key: str | None,
    ) -> int:
        path = self.seed_dir / filename
        if not path.exists():
            return 0
        data = self.load_json(filename)
        count = 0
        for row in data:
            row = dict(row)  # copy
            if site_key:
                site_name = row.pop(site_key)
                site = self._resolve_site(site_name)
                if not site:
                    continue
                row["land_site_id"] = site.id

            # SportParkFacility: no site_key, uses case_study_name
            obj = model_class(**row)
            self.session.add(obj)
            count += 1
        self.session.flush()
        return count

    def _seed_case_studies(self) -> int:
        path = self.seed_dir / "case_study_projects.json"
        if not path.exists():
            return 0
        data = self.load_json("case_study_projects.json")
        count = 0
        for row in data:
            row = dict(row)
            phases_data = row.pop("phases", [])
            project_name = row["project_name"]

            if self._exists(CaseStudyProject, project_name=project_name):
                continue

            proj = CaseStudyProject(**row)
            self.session.add(proj)
            self.session.flush()
            count += 1

            for phase_row in phases_data:
                phase_row = dict(phase_row)
                unit_types_data = phase_row.pop("unit_types", [])

                phase = CaseStudyPhase(
                    case_study_project_id=proj.id, **phase_row,
                )
                self.session.add(phase)
                self.session.flush()
                count += 1

                for ut_row in unit_types_data:
                    ut = CaseStudyUnitType(
                        case_study_phase_id=phase.id, **ut_row,
                    )
                    self.session.add(ut)
                    count += 1

        self.session.flush()
        return count

    def _seed_design_guidelines(self) -> int:
        path = self.seed_dir / "design_guidelines.json"
        if not path.exists():
            return 0
        data = self.load_json("design_guidelines.json")
        count = 0
        for row in data:
            row = dict(row)
            site_name = row.pop("site_name")
            product_specs_data = row.pop("product_specs", [])
            case_studies_data = row.pop("design_case_studies", [])

            site = self._resolve_site(site_name)
            if not site:
                continue

            if self._exists(DesignGuideline, land_site_id=site.id):
                continue

            dg = DesignGuideline(land_site_id=site.id, **row)
            self.session.add(dg)
            self.session.flush()
            count += 1

            for spec_row in product_specs_data:
                spec = DesignProductSpec(
                    design_guideline_id=dg.id, **spec_row,
                )
                self.session.add(spec)
                count += 1

            for cs_row in case_studies_data:
                cs = DesignCaseStudy(
                    design_guideline_id=dg.id, **cs_row,
                )
                self.session.add(cs)
                count += 1

        self.session.flush()
        return count
