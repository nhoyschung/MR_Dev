"""Seeder for source report records — tracks the 19 source text files."""

from pathlib import Path
from typing import Any

from src.db.models import City, ReportPeriod, SourceReport
from src.seeders.base_seeder import BaseSeeder

# Map source filenames to their metadata
SOURCE_FILES: list[dict[str, Any]] = [
    # D_colect/extracted/
    {"filename": "mixed_use_casestudy_full.txt", "report_type": "case_study", "city_name": None, "year": 2025, "half": "H2"},
    {"filename": "hcmc_pass1.txt", "report_type": "market_analysis", "city_name": "Ho Chi Minh City", "year": 2025, "half": "H2"},
    {"filename": "hcmc_pass2.txt", "report_type": "market_analysis", "city_name": "Ho Chi Minh City", "year": 2025, "half": "H2"},
    {"filename": "hcmc_pass3.txt", "report_type": "market_analysis", "city_name": "Ho Chi Minh City", "year": 2025, "half": "H2"},
    {"filename": "hanoi_pass1.txt", "report_type": "market_analysis", "city_name": "Hanoi", "year": 2025, "half": "H2"},
    {"filename": "hanoi_pass2.txt", "report_type": "market_analysis", "city_name": "Hanoi", "year": 2025, "half": "H2"},
    {"filename": "hanoi_pass3.txt", "report_type": "market_analysis", "city_name": "Hanoi", "year": 2025, "half": "H2"},
    {"filename": "binh_duong_pass1.txt", "report_type": "market_analysis", "city_name": "Binh Duong", "year": 2025, "half": "H2"},
    {"filename": "binh_duong_pass2.txt", "report_type": "market_analysis", "city_name": "Binh Duong", "year": 2025, "half": "H2"},
    {"filename": "binh_duong_pass3.txt", "report_type": "market_analysis", "city_name": "Binh Duong", "year": 2025, "half": "H2"},
    {"filename": "developer_analysis_MIK_full.txt", "report_type": "developer_analysis", "city_name": "Ho Chi Minh City", "year": 2025, "half": "H1"},
    {"filename": "sales_price_pass1.txt", "report_type": "price_analysis", "city_name": None, "year": 2024, "half": "H1"},
    {"filename": "sales_price_pass2.txt", "report_type": "price_analysis", "city_name": None, "year": 2024, "half": "H1"},
    {"filename": "sales_price_pass3.txt", "report_type": "price_analysis", "city_name": None, "year": 2024, "half": "H1"},
    # Output/extracted/
    {"filename": "20250807_NHO-PD_HP-35ha_Proposal_full.txt", "report_type": "development_proposal", "city_name": None, "year": 2025, "half": "H2"},
    {"filename": "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt", "report_type": "land_review", "city_name": "Binh Duong", "year": 2025, "half": "H2"},
    {"filename": "20251017_Hai_Phong_3_Land_review_SWOT_full.txt", "report_type": "land_review", "city_name": None, "year": 2025, "half": "H2"},
    {"filename": "20251017_NHO-PD_25ha_Duong_Kinh_Land_Review_issued_full.txt", "report_type": "land_review", "city_name": None, "year": 2025, "half": "H2"},
    {"filename": "20251031_NHO-PD_240ha_Bac_Ninh_Land_Review_full.txt", "report_type": "land_review", "city_name": None, "year": 2025, "half": "H2"},
]


class SourceReportSeeder(BaseSeeder):
    """Seeds source_reports table to track ingested files."""

    def validate(self) -> bool:
        return True

    def seed(self) -> int:
        count = 0
        for sf in SOURCE_FILES:
            # Look up city
            city_id = None
            if sf["city_name"]:
                city = self.session.query(City).filter_by(name_en=sf["city_name"]).first()
                city_id = city.id if city else None

            # Look up period
            period = (
                self.session.query(ReportPeriod)
                .filter_by(year=sf["year"], half=sf["half"])
                .first()
            )
            period_id = period.id if period else None

            _, created = self._get_or_create(
                SourceReport,
                filename=sf["filename"],
                defaults={
                    "report_type": sf["report_type"],
                    "city_id": city_id,
                    "period_id": period_id,
                    "status": "ingested",
                },
            )
            if created:
                count += 1

        self.session.commit()
        return count
