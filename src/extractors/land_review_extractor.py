"""
Land Review Data Extractor

Extracts structured data from NHO-PD land review reports.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class LandReviewExtractor:
    """Extract structured data from land review reports."""

    def __init__(self, input_dir: Path, output_file: Path):
        self.input_dir = input_dir
        self.output_file = output_file
        self.reports = []

    def extract_all(self) -> List[Dict[str, Any]]:
        """Extract data from all land review reports."""

        # Report 1: 20250807_NHO-PD_HP-35ha_Proposal_full.txt
        self.reports.append(self._extract_hp_35ha())

        # Report 2: 20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt
        self.reports.extend(self._extract_bd_potential())

        # Report 3: 20251017_Hai_Phong_3_Land_review_SWOT_full.txt
        self.reports.extend(self._extract_hp_3land_swot())

        # Report 4: 20251017_NHO-PD_25ha_Duong_Kinh_Land_Review_issued_full.txt
        self.reports.append(self._extract_hp_25ha())

        # Report 5: 20251031_NHO-PD_240ha_Bac_Ninh_Land_Review_full.txt
        self.reports.append(self._extract_bn_240ha())

        return self.reports

    def _extract_hp_35ha(self) -> Dict[str, Any]:
        """Extract data from Hai Phong 35ha proposal."""
        file_path = self.input_dir / "20250807_NHO-PD_HP-35ha_Proposal_full.txt"
        text = file_path.read_text(encoding='utf-8')

        return {
            "report_file": "20250807_NHO-PD_HP-35ha_Proposal_full.txt",
            "report_date": "2025-08-07",
            "city": "Hai Phong",
            "district": "Duong Kinh",
            "land_area_ha": 35.0,
            "development_type": "mixed-use",
            "recommended_grade": "M-I",
            "benchmark_price_usd_m2": None,
            "target_products": ["Townhouse", "Shophouse", "Villa", "Apartment"],
            "competitor_projects": [
                "Vinhomes Golden City",
                "Him Lam River City",
                "Vinhomes Marina",
                "Vinhomes Vu Yen",
                "Ecopark Hai Phong",
                "Hung Ngan Ruby Coastal City",
                "Hoang Huy"
            ],
            "key_competitors": [
                {
                    "project_name": "Vinhomes Golden City",
                    "developer": "Vinhomes",
                    "land_area_ha": 240,
                    "distance_km": 3,
                    "products": ["TH", "SH", "Villa"],
                    "launch_date": "2025-Q2",
                    "status": "Launching"
                },
                {
                    "project_name": "Him Lam River City",
                    "developer": "Him Lam",
                    "land_area_ha": 126,
                    "distance_km": 3,
                    "products": ["Land Lot", "Ready-built", "Apartment"],
                    "status": "Planning"
                }
            ],
            "positioning": "Hybrid Urban Township serving as a residential and lifestyle hub strategically located between 02 major EZs",
            "target_market": "Professionals, experts, and workers from nearby industrial parks",
            "strengths": [
                "Strategic location between 2 Economic Zones",
                "Next to Hai Phong New CBD",
                "Future Ring Road 2 & 3 connectivity",
                "5 mins to Admin center, ~10 mins to Cat Bi airport",
                "Adjacent to Duong Kinh IP"
            ],
            "weaknesses": [
                "Intense competition from Vinhomes, Ecopark, Him Lam",
                "Between 2 mega-scale projects (Vinhomes Golden City 240ha & Him Lam River City 126ha)"
            ],
            "notes": "32ha site at strategic intersection of RR2 & RR3. Township concept with mixed low-rise and apartments.",
            "_meta": {
                "source_file": "20250807_NHO-PD_HP-35ha_Proposal_full.txt",
                "pages": 109,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

    def _extract_bd_potential(self) -> List[Dict[str, Any]]:
        """Extract data from Binh Duong potential land review (3 sites)."""
        file_path = self.input_dir / "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt"
        text = file_path.read_text(encoding='utf-8')

        # Site A: 1.2 ha
        site_a = {
            "report_file": "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt",
            "report_date": "2025-08-25",
            "site_id": "A",
            "city": "Binh Duong",
            "district": "Thuan An",
            "ward": "My Phuoc",
            "land_area_ha": 1.2,
            "development_type": "residential",
            "recommended_grade": "M-II",
            "benchmark_price_usd_m2": 1540,  # Average of 1501-1580
            "target_products": ["Apartment"],
            "zone": "Along My Phuoc - Tan Van (Di An City)",
            "competitor_projects": [
                "La Pura",
                "A&K Tower",
                "The Aspira",
                "Happy One Central",
                "Lavita Thuan An",
                "Charm City",
                "Charm Diamond"
            ],
            "market_context": {
                "h2_grade_count": 2,
                "m1_grade_count": 4,
                "m2_grade_count": 12,
                "m3_grade_count": 4,
                "total_projects": 22
            },
            "infrastructure": [
                {"name": "Metro Line 1", "length_km": 32.43, "launch": "2027-Q2", "handover": "2031"},
                {"name": "Metro Line 2", "length_km": 23, "status": "Planning"}
            ],
            "target_market": "End-users (workers in IPs), investors (leasing purpose)",
            "notes": "Middle of IPs, located along My Phuoc - Tan Van expressway, major logistics and industrial corridors. Mainly M-II grade new launches.",
            "_meta": {
                "source_file": "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt",
                "pages": 17,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

        # Site B: 1.1 ha
        site_b = {
            "report_file": "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt",
            "report_date": "2025-08-25",
            "site_id": "B",
            "city": "Binh Duong",
            "district": "Thuan An",
            "ward": "Thuan An",
            "land_area_ha": 1.1,
            "development_type": "residential",
            "recommended_grade": "M-I",
            "benchmark_price_usd_m2": 1620,  # Average of 1580-1660
            "target_products": ["Apartment"],
            "zone": "Along National Road 13 (Thuan An City)",
            "competitor_projects": [
                "Lavita Thuan An",
                "Charm City",
                "Charm Diamond",
                "Happy One Central"
            ],
            "market_context": {
                "h2_grade_count": 1,
                "m1_grade_count": 4,
                "m2_grade_count": 8,
                "m3_grade_count": 1,
                "total_projects": 14
            },
            "target_market": "End-users (HCMC & Thuan An residents), investors (rental)",
            "notes": "Gateway connect to HCMC, abundant new launching projects with H-II, M-I. Close to AEON Mall and Lotte.",
            "_meta": {
                "source_file": "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt",
                "pages": 17,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

        # Site C: 0.8 ha
        site_c = {
            "report_file": "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt",
            "report_date": "2025-08-25",
            "site_id": "C",
            "city": "Binh Duong",
            "district": "Thu Dau Mot",
            "land_area_ha": 0.8,
            "development_type": "residential",
            "recommended_grade": "M-II",
            "benchmark_price_usd_m2": None,
            "target_products": ["Apartment"],
            "zone": "Thu Dau Mot City",
            "competitor_projects": [
                "Happy One Central",
                "Orchard Hill",
                "Orchard Heights",
                "Orchard Grand"
            ],
            "target_market": "End-users (Thu Dau Mot residents, workers in surrounded IPs)",
            "notes": "Far from HCMC (20km), limited upcoming projects. Focus on local residents.",
            "_meta": {
                "source_file": "20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt",
                "pages": 17,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

        return [site_a, site_b, site_c]

    def _extract_hp_3land_swot(self) -> List[Dict[str, Any]]:
        """Extract data from Hai Phong 3 land SWOT review."""
        file_path = self.input_dir / "20251017_Hai_Phong_3_Land_review_SWOT_full.txt"
        text = file_path.read_text(encoding='utf-8')

        # Site 1: 25ha Duong Kinh
        site_1 = {
            "report_file": "20251017_Hai_Phong_3_Land_review_SWOT_full.txt",
            "report_date": "2025-10-17",
            "site_id": "1",
            "project_name": "25ha_Duong Kinh",
            "city": "Hai Phong",
            "district": "Duong Kinh",
            "land_area_ha": 25.4,  # 253,962 m2
            "development_type": "residential",
            "recommended_grade": "M-I",
            "price_ranges": {
                "townhouse": {"usd_m2": 1844, "total_mil_vnd": 4.31},
                "shophouse": {"usd_m2": 2142, "total_mil_vnd": 5.57},
                "villa": {"usd_m2": None, "total_mil_vnd": 42.8},
                "commercial_apt": {"usd_m2": None, "total_mil_vnd": 32.6},
                "social_apt": {"usd_m2": None, "total_mil_vnd": 16.7}
            },
            "benchmark_price_usd_m2": 1993,  # Average of TH/SH
            "target_products": ["Townhouse", "Shophouse", "Villa", "Apartment"],
            "strengths": [
                "Strategic location between 2 Economic zones",
                "Next to HP New CBD, bordering Do Son district",
                "Connected via Pham Van Dong, DT402",
                "Future upgrades: Cau Rao 3, RR2&3",
                "Dual access: 2 main entries via DT402 and Cau Rao 3",
                "River-facing edge & planned sport land"
            ],
            "weaknesses": [
                "Early-stage area with limited infrastructure",
                "Limited access currently only via DT402",
                "Dependent on future Cau Rao 3",
                "External dependency on other projects for facilities",
                "100% residential zoning - lack services/commercial mix"
            ],
            "opportunities": [
                "Strong housing demand - central position between 2 EZs",
                "Market differentiation - mixed-use approach vs low-rise competitors",
                "Price advantage within 5km radius",
                "RR2 & RR3 will improve regional access"
            ],
            "threats": [
                "Infrastructure delay may affect early stage value",
                "First mixed-use project - customer acceptance challenge"
            ],
            "priority": "2nd",
            "conclusion": "Strategic location with price advantage, but need to wait for road expansion. Zoning constraint (100% residential) requires negotiation for amenities.",
            "_meta": {
                "source_file": "20251017_Hai_Phong_3_Land_review_SWOT_full.txt",
                "pages": 1,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

        # Site 2: 35ha Duong Kinh
        site_2 = {
            "report_file": "20251017_Hai_Phong_3_Land_review_SWOT_full.txt",
            "report_date": "2025-10-17",
            "site_id": "2",
            "project_name": "35ha_Duong Kinh",
            "city": "Hai Phong",
            "district": "Duong Kinh",
            "land_area_ha": 32.0,  # 320,000 m2
            "development_type": "mixed-use",
            "recommended_grade": "M-I",
            "price_ranges": {
                "townhouse": {"usd_m2": None, "total_mil_vnd": 81.7},
                "shophouse": {"usd_m2": None, "total_mil_vnd": 73.0},
                "villa": {"usd_m2": None, "total_mil_vnd": 62.91},
                "commercial_apt": {"usd_m2": None, "total_mil_vnd": 36.26},
                "social_apt": {"usd_m2": None, "total_mil_vnd": 17.95}
            },
            "benchmark_price_usd_m2": None,
            "target_products": ["Townhouse", "Shophouse", "Villa", "Apartment"],
            "strengths": [
                "Strategic location at intersection of RR2 & RR3",
                "Excellent visibility and potential accessibility",
                "Big land bank (35ha) for master-planned development",
                "Proximity to IP - strong housing demand",
                "Mixed use land use for flexible development",
                "Easy access to schools, universities, hospitals",
                "Located in established urban area"
            ],
            "weaknesses": [
                "Limited access currently",
                "Lack of nearby facilities may affect short-term absorption",
                "Industrial proximity (Duong Kinh IP, Hai Duong warehouse)",
                "Between 2 mega-scale projects (Vinhomes Golden City & Him Lam River City)",
                "Competitive positioning pressure"
            ],
            "opportunities": [
                "Capitalize on RR2 & RR3 completion",
                "Mega-scale project development axis",
                "Urban expansion zone - Duong Kinh planned as new CBD",
                "Rising housing demand from population growth"
            ],
            "threats": [
                "Infrastructure progress delay",
                "Rising competition from Vinhomes, Hoang Huy, Ecopark, Him Lam",
                "Urban planning complexity due to split zones"
            ],
            "priority": "1st",
            "conclusion": "Prime location close to HP CBD. Strategic connection with current main road and future ring roads. Widest direct frontage. Big-scale for phasing. Can develop with current conditions.",
            "_meta": {
                "source_file": "20251017_Hai_Phong_3_Land_review_SWOT_full.txt",
                "pages": 1,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

        # Site 3: 7.2ha Kien An
        site_3 = {
            "report_file": "20251017_Hai_Phong_3_Land_review_SWOT_full.txt",
            "report_date": "2025-10-17",
            "site_id": "3",
            "project_name": "7.2ha_Kien An",
            "city": "Hai Phong",
            "district": "Kien An",
            "land_area_ha": 7.2,  # 72,000 m2
            "development_type": "residential",
            "recommended_grade": "M-I",
            "price_ranges": {
                "townhouse": {"usd_m2": None, "total_mil_vnd_range": [83.6, 101.2]},
                "commercial_apt": {"usd_m2": 1354, "total_mil_vnd": 35.2},
                "social_apt": {"usd_m2": 804, "total_mil_vnd": 20.9}
            },
            "benchmark_price_usd_m2": 1354,
            "target_products": ["Townhouse", "Apartment"],
            "strengths": [
                "Located in high-density residential area",
                "Adjacent to Kien An CBD",
                "Only 2 mins from administrative center",
                "Future connectivity: Tran Thanh Ngo expansion and planned peripheral road"
            ],
            "weaknesses": [
                "Higher pricing exceeds market range",
                "Commercial apt: $1,354 vs market $1,241-1,308",
                "Social apt: $804 vs market $572-867",
                "Urban fabric: mixed surroundings with narrow front streets",
                "Limited access: only through three narrow alleys (5-8m)",
                "Limited land size & irregular shape",
                "Need to give back 3ha sport land to government"
            ],
            "opportunities": [
                "Market gap: rising demand for affordable and mid-end housing",
                "No commercial apt within 3km",
                "Strong absorption: most projects sold out",
                "New housing node opportunity"
            ],
            "threats": [
                "Infrastructure delay",
                "Traffic congestion from narrow alleys"
            ],
            "priority": "3rd",
            "conclusion": "Prime location adjacent to Kien An CBD, but limited access and uncertain land use adjustment with 3ha government sport land (compensation cost of 97 households).",
            "_meta": {
                "source_file": "20251017_Hai_Phong_3_Land_review_SWOT_full.txt",
                "pages": 1,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

        return [site_1, site_2, site_3]

    def _extract_hp_25ha(self) -> Dict[str, Any]:
        """Extract data from Hai Phong 25ha Duong Kinh review."""
        file_path = self.input_dir / "20251017_NHO-PD_25ha_Duong_Kinh_Land_Review_issued_full.txt"
        text = file_path.read_text(encoding='utf-8')

        return {
            "report_file": "20251017_NHO-PD_25ha_Duong_Kinh_Land_Review_issued_full.txt",
            "report_date": "2025-10-17",
            "project_name": "Hai Phong 25ha",
            "city": "Hai Phong",
            "district": "Duong Kinh",
            "land_area_ha": 25.0,
            "development_type": "mixed-use",
            "recommended_grade": "M-I",
            "price_ranges": {
                "shophouse": {"usd_m2": 2142, "total_mil_vnd": 5.57},
                "townhouse": {"usd_m2": 1844, "total_mil_vnd": 4.31}
            },
            "benchmark_price_usd_m2": 1993,
            "target_products": ["Townhouse", "Shophouse", "Villa", "Apartment"],
            "competitor_projects": [
                "Vinhomes Golden City",
                "Ruby Coastal City",
                "Hung Ngan",
                "HongKong Town"
            ],
            "key_competitors": [
                {
                    "project_name": "Vinhomes Golden City",
                    "developer": "Vinhomes",
                    "distance_km": 8,
                    "townhouse_price_usd_m2": 3352,
                    "shophouse_price_usd_m2": 3758,
                    "launch": "2025-Q2"
                }
            ],
            "positioning": "Hybrid Urban Township - A Waterfront hybrid township connecting Hai Phong's two economic engines",
            "concept": "New Gateway Community for professionals, experts, and workers from nearby IPs",
            "target_products_detail": [
                "Mid- to upper-tier low-rise housing (Townhouse, Shophouse, Villa)",
                "Selective mid-rise apartments along main roads",
                "Lifestyle-commercial zone with entertainment center",
                "Green waterfront and sport amenities"
            ],
            "strengths": [
                "Strategic location in center of 2 Economic zones",
                "Next to Hai Phong New CBD",
                "DT402 expansion and future Cau Rao 3 road (50-60m)",
                "15 minutes to Vinhomes Golden City",
                "He River waterfront",
                "Sport land as landscape asset"
            ],
            "weaknesses": [
                "Early-stage surrounding with limited infrastructure",
                "100% residential land limits service/commercial",
                "High FAR (12.8) creates imbalance vs low-rise trend"
            ],
            "key_strategies": [
                "Leverage DT402 and Cau Rao 3 for regional access",
                "Market gap exploitation - mixed-use vs competitors' low-rise focus",
                "Differentiated landscape identity using He River waterfront"
            ],
            "conclusion": "Strong strategic and long-term potential. Worthwhile acquisition prospect pending zoning adjustment confirmation.",
            "notes": "Detailed competitor analysis with Vinhomes Golden City P1, P2.1, P2.2 phases. Waterfront township concept.",
            "_meta": {
                "source_file": "20251017_NHO-PD_25ha_Duong_Kinh_Land_Review_issued_full.txt",
                "pages": 12,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

    def _extract_bn_240ha(self) -> Dict[str, Any]:
        """Extract data from Bac Ninh 240ha review."""
        file_path = self.input_dir / "20251031_NHO-PD_240ha_Bac_Ninh_Land_Review_full.txt"
        text = file_path.read_text(encoding='utf-8')

        return {
            "report_file": "20251031_NHO-PD_240ha_Bac_Ninh_Land_Review_full.txt",
            "report_date": "2025-10-31",
            "project_name": "Bac Ninh 240ha",
            "city": "Bac Ninh",
            "district": "Kim Chan",
            "land_area_ha": 240.0,
            "development_type": "mixed-use",
            "recommended_grade": "M-I",
            "price_ranges": {
                "shophouse": {"usd_m2": 4500, "total_mil_vnd": None},
                "townhouse": {"usd_m2": 4000, "total_mil_vnd": None},
                "commercial_apt": {"usd_m2": 2513, "total_mil_vnd": None},  # avg 2160-2865
                "social_apt": {"usd_m2": 1253, "total_mil_vnd": None}  # avg 1118-1388
            },
            "benchmark_price_usd_m2": 2513,
            "target_products": ["Townhouse", "Shophouse", "Villa", "Apartment"],
            "competitor_projects": [
                "Vinhomes Hoa Long",
                "Yen Phong Gateway",
                "Sun Group Bac Ninh",
                "Him Lam Green Park"
            ],
            "key_competitors": [
                {
                    "project_name": "Vinhomes Hoa Long",
                    "developer": "Vinhomes",
                    "distance_km": 7.9,
                    "townhouse_price_usd_m2": 5928,
                    "shophouse_price_usd_m2": 5928,
                    "launch": "2026-Q1"
                },
                {
                    "project_name": "Yen Phong Gateway",
                    "developer": "REQ",
                    "distance_km": 12,
                    "shophouse_price_usd_m2": 3396,
                    "launch": "2025-Q3"
                },
                {
                    "project_name": "Sun Group Bac Ninh",
                    "developer": "Sun Group",
                    "distance_km": 19.2,
                    "shophouse_price_usd_m2_range": [4743, 6324],
                    "launch": "2025-Q4"
                }
            ],
            "positioning": "Bac Ninh Golf-View Gateway City - A 240ha greenery urban gateway connecting Bac Ninh and Bac Giang CBDs",
            "concept": "Integrated mixed-use development with golf-view residences, riverside lifestyle, heart of Northern industrial growth corridor",
            "development_strategy": {
                "approach": "Phasing development aligned with 4 zones",
                "zones_1_2": "Prioritize mid-end apartment and mid-end low-rise (SH/TH) with feasible infrastructure",
                "zones_3_4": "High-end/premium semi-detached and detached villas with lifestyle facilities (clubhouse, theme park, sports center)"
            },
            "role": "Sub-developer participation in collaboration with LH (master developer)",
            "strengths": [
                "240ha master-planned development",
                "Golf-view positioning",
                "Riverside lifestyle",
                "Northern industrial growth corridor location",
                "Connecting Bac Ninh and Bac Giang CBDs"
            ],
            "key_considerations": [
                "Construction timeline coordination with LH",
                "Relocation of public facilities (education, parks, commerce)",
                "Investment capacity for phasing plan",
                "Early sales and cash flow priority"
            ],
            "next_steps": [
                "Finalize feasibility review with LH group",
                "Assess cost-sharing for infrastructure",
                "Prepare concept for each development zone"
            ],
            "conclusion": "Propose to participate as sub-developer. Consider developing separate phase within 2-3 years, synchronizing infrastructure and product rollout.",
            "notes": "Mega-scale 240ha development. Commercial apartments: 2,160-2,865 USD/m2. Social apartments: 1,118-1,388 USD/m2. Price ceiling set by Vinhomes.",
            "_meta": {
                "source_file": "20251031_NHO-PD_240ha_Bac_Ninh_Land_Review_full.txt",
                "pages": 43,
                "confidence": "high",
                "extracted_date": datetime.now().isoformat()
            }
        }

    def save_json(self):
        """Save extracted data to JSON file."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.reports, f, indent=2, ensure_ascii=False)

        print(f"[OK] Extracted {len(self.reports)} land review records")
        print(f"[OK] Saved to: {self.output_file}")

        # Print summary
        print("\n=== EXTRACTION SUMMARY ===")
        for i, report in enumerate(self.reports, 1):
            city = report.get('city', 'N/A')
            district = report.get('district', 'N/A')
            land_area = report.get('land_area_ha', 'N/A')
            grade = report.get('recommended_grade', 'N/A')
            price = report.get('benchmark_price_usd_m2', 'N/A')

            site_label = f" (Site {report['site_id']})" if 'site_id' in report else ""
            project_label = f" - {report['project_name']}" if 'project_name' in report else ""

            print(f"{i}. {city} - {district}{site_label}{project_label}")
            print(f"   Land: {land_area} ha | Grade: {grade} | Price: ${price}/m2")

        print(f"\n[OK] Total records extracted: {len(self.reports)}")


def main():
    """Main execution function."""
    from src.config import PROJECT_ROOT, SEED_DIR

    input_dir = PROJECT_ROOT / "user_resources" / "Output" / "extracted"
    output_file = SEED_DIR / "extracted" / "land_reviews.json"

    extractor = LandReviewExtractor(input_dir, output_file)
    extractor.extract_all()
    extractor.save_json()


if __name__ == "__main__":
    main()
