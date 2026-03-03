"""Seed NHO-PD data from user_resources/Output reports into the database.

Sources:
 - 20250825 BD Potential Land Review (Revised)   → BD competitor projects
 - 20251017 Hai Phong 3 Land Review SWOT          → HP site comparison
 - 20251017 NHO-PD 25ha Duong Kinh Land Review    → HP market + NHO site pricing
 - 20250807 NHO-PD HP-35ha Proposal               → HP 35ha NHO site
 - 20251031 NHO-PD 240ha Bac Ninh Land Review     → BN competitor projects

New data added:
 - Cities: Hai Phong, Bac Ninh
 - Districts: 3 (HP), 7 (BN)
 - Grade definitions for HP and BN
 - Developers: 19 new
 - Projects: 30 new competitor + NHO sites
 - Price records: 2025-H2 (source=nho_pdf)
 - Grade updates for existing scraped BD projects

Exchange rate: 1 USD = 25,500 VND (from NHO-PD planning assumptions)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.connection import get_session
from src.db.models import (
    City, District, GradeDefinition, Developer, Project, PriceRecord, ReportPeriod,
)


VND_PER_USD = 25_500


def _usd_to_vnd(usd: float) -> float:
    return round(usd * VND_PER_USD)


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def seed_output_reports():
    with get_session() as session:
        print("=" * 60)
        print("Seeding Output-report data (Hai Phong + Bac Ninh + BD)")
        print("=" * 60)

        # ── Period ──────────────────────────────────────────────────
        period = session.query(ReportPeriod).filter_by(year=2025, half="H2").first()
        if not period:
            raise ValueError("Period 2025-H2 not found. Run GradeSeeder first.")
        period_id = period.id
        source = "NHO-PD Land Review 2025-H2"

        # ── 1. New Cities ────────────────────────────────────────────
        hp, hp_new = get_or_create(
            session, City,
            name_en="Hai Phong",
            defaults={"name_vi": "Hải Phòng", "name_ko": "하이퐁", "region": "North"},
        )
        bn, bn_new = get_or_create(
            session, City,
            name_en="Bac Ninh",
            defaults={"name_vi": "Bắc Ninh", "name_ko": "박닌", "region": "North"},
        )
        print(f"[Cities] Hai Phong id={hp.id} ({'NEW' if hp_new else 'exists'}),  "
              f"Bac Ninh id={bn.id} ({'NEW' if bn_new else 'exists'})")

        # ── 2. New Districts ─────────────────────────────────────────
        hp_districts = [
            ("Duong Kinh", "Dương Kinh", "urban"),
            ("Kien An",    "Kiến An",    "urban"),
            ("Do Son",     "Đồ Sơn",     "urban"),
        ]
        bn_districts = [
            ("Kim Chan",  "Kim Chân",  "urban"),
            ("Dai Phuc",  "Đại Phúc",  "urban"),
            ("Ninh Xa",   "Ninh Xá",   "urban"),
            ("Vo Cuong",  "Võ Cường",  "urban"),
            ("Yen Phong", "Yên Phong", "suburban"),
            ("Tien Du",   "Tiên Du",   "suburban"),
            ("Hoa Long",  "Hòa Long",  "suburban"),
        ]

        hp_dist: dict[str, District] = {}
        for name_en, name_vi, dtype in hp_districts:
            d, created = get_or_create(
                session, District,
                name_en=name_en, city_id=hp.id,
                defaults={"name_vi": name_vi, "district_type": dtype},
            )
            hp_dist[name_en] = d
            print(f"  District HP/{name_en} id={d.id} ({'NEW' if created else 'exists'})")

        bn_dist: dict[str, District] = {}
        for name_en, name_vi, dtype in bn_districts:
            d, created = get_or_create(
                session, District,
                name_en=name_en, city_id=bn.id,
                defaults={"name_vi": name_vi, "district_type": dtype},
            )
            bn_dist[name_en] = d
            print(f"  District BN/{name_en} id={d.id} ({'NEW' if created else 'exists'})")

        # ── 3. Grade definitions ─────────────────────────────────────
        # Hai Phong: low-rise focus, same tier structure as BD
        hp_grades = [
            ("H-I",   3_000, 999_999, "high-end"),
            ("H-II",  2_000, 3_000,   "high-end"),
            ("M-I",   1_600, 2_000,   "mid-end"),
            ("M-II",  1_200, 1_600,   "mid-end"),
            ("M-III", 1_000, 1_200,   "mid-end"),
            ("A",         0, 1_000,   "affordable"),
        ]
        # Bac Ninh: higher price range (low-rise $3k-6k; apt $2.2k-2.9k)
        bn_grades = [
            ("L",    5_000, 999_999, "luxury"),
            ("H-I",  3_500, 5_000,   "high-end"),
            ("H-II", 2_500, 3_500,   "high-end"),
            ("M-I",  1_800, 2_500,   "mid-end"),
            ("M-II", 1_200, 1_800,   "mid-end"),
            ("A",        0, 1_200,   "affordable"),
        ]

        def seed_grades(city_id, grade_list):
            count = 0
            for code, mn, mx, seg in grade_list:
                _, created = get_or_create(
                    session, GradeDefinition,
                    city_id=city_id, grade_code=code,
                    defaults={
                        "min_price_usd": mn, "max_price_usd": mx,
                        "segment": seg, "period_id": period_id,
                    },
                )
                if created:
                    count += 1
            return count

        g_hp = seed_grades(hp.id, hp_grades)
        g_bn = seed_grades(bn.id, bn_grades)
        print(f"[Grades] HP: {g_hp} new,  BN: {g_bn} new")

        # ── 4. New Developers ────────────────────────────────────────
        devs_to_add = [
            # BD
            ("Phu Dong Group",    "Phú Đông Group",    hp.id,  None,  "Developer of Phu Dong Sky One in Binh Duong."),
            ("C-Holding",         "C-Holding",          None,   None,  "Developer of The Felix and The Maison (C-River View) in Binh Duong."),
            ("TT Capital",        "TT Capital",         None,   None,  "Developer of TT AVIO (Orion) in Di An, Binh Duong."),
            ("Charm Group",       "Charm Group",        None,   None,  "Developer of Charm City and Charm Diamond in Thuan An, Binh Duong."),
            ("Bcons Group",       "Bcons Group",        None,   None,  "Developer of Bcons Solary, Bcons City series in Binh Duong."),
            ("A&T Group",         "A&T Group",          None,   None,  "Developer of A&T Sky Garden and A&T Saigon Riverside in Binh Duong."),
            ("OBC Tower",         "OBC Tower Corp",     None,   None,  "Developer of A&K Tower in Thuan An, Binh Duong."),
            ("Tyson An Phu",      "Tyson An Phú",       None,   None,  "Developer of Ava Center in Thuan An, Binh Duong."),
            ("Phuc An Gia",       "Phúc An Gia",        None,   None,  "Developer of The Aspira in Di An, Binh Duong."),
            ("SP Setia Berhad",   "SP Setia Berhad",    None,   None,  "Malaysian developer. Setia Garden Residence in Binh Duong."),
            # HP
            ("BRG Group",         "BRG Group",          2,      None,  "Hanoi-based conglomerate. Ruby Coastal City in Do Son, Hai Phong."),
            ("Ramond Group",      "Ramond Group",       hp.id,  None,  "Developer of Ramond Urbaniz Hai Phong in Duong Kinh."),
            ("Phuong Dong Group", "Phương Đông Group",  hp.id,  None,  "Developer of HongKong Town in Do Son, Hai Phong."),
            ("Hung Ngan Group",   "Hưng Ngân Group",    hp.id,  None,  "Developer of Hung Ngan Riverside township in Duong Kinh."),
            # BN
            ("Him Lam Land",      "Him Lam Land",       2,      None,  "Hanoi-based developer of Him Lam Green Park in Bac Ninh."),
            ("Bac Ninh Lotus",    "Bắc Ninh Lotus",     bn.id,  None,  "Developer of Phoenix Tower in Dai Phuc, Bac Ninh."),
            ("Dabaco Group",      "Dabaco Group",       bn.id,  None,  "Bac Ninh-based developer of Lotus Central and Parkview City."),
            ("Hop Phu Land",      "Hợp Phú Land",       bn.id,  None,  "Developer of Hop Phu Complex in Vo Cuong, Bac Ninh."),
            ("Nhan Dat Tien",     "Nhân Đất Tiên",      bn.id,  None,  "Developer of Green Pearl in Vo Cuong, Bac Ninh."),
        ]

        dev_map: dict[str, Developer] = {}
        dev_new_count = 0
        for name_en, name_vi, hq_city_id, stock, desc in devs_to_add:
            d, created = get_or_create(
                session, Developer,
                name_en=name_en,
                defaults={
                    "name_vi": name_vi,
                    "hq_city_id": hq_city_id,
                    "stock_code": stock,
                    "description": desc,
                },
            )
            dev_map[name_en] = d
            if created:
                dev_new_count += 1
        print(f"[Developers] {dev_new_count} new")

        # Helper: get existing developer by name
        def dev(name_en: str) -> Developer | None:
            if name_en in dev_map:
                return dev_map[name_en]
            d = session.query(Developer).filter_by(name_en=name_en).first()
            return d

        # ── 5. Update existing scraped BD projects (grades) ──────────
        updates = [
            (99,  "The Maison",      "M-III", "completed"),
            (101, "Happy One Central", "M-II", "completed"),
            (115, "Phu Dong SkyOne", "M-II",  "selling"),
        ]
        upd_count = 0
        for pid, name, grade, status in updates:
            p = session.get(Project, pid)
            if p and p.grade_primary is None:
                p.grade_primary = grade
                p.status = status
                upd_count += 1
                print(f"  Updated [{pid}] {name}: grade={grade}, status={status}")
        session.flush()
        print(f"[Existing projects updated] {upd_count}")

        # ── 6. New projects ──────────────────────────────────────────
        # Lookup existing developers by name
        hung_thinh    = dev("Hung Thinh Corp")
        phat_dat      = dev("Phat Dat")
        capitaland    = dev("Capitaland")
        vinhomes      = dev("Vinhomes")
        sun_group     = dev("Sun Group")
        brg_group     = dev("BRG Group")

        new_projects = [
            # ── Binh Duong ───────────────────────────────────────────
            {
                "name": "Lavita Thuan An",
                "developer_id": hung_thinh.id if hung_thinh else None,
                "district_id": 39,  # Thuan An, Binh Duong
                "project_type": "apartment",
                "status": "selling",
                "total_units": 2477,
                "launch_date": "2021-Q1",
                "completion_date": "2027",
                "grade_primary": "M-II",
                "price_usd": 1373,
            },
            {
                "name": "La Pura Binh Duong",
                "developer_id": phat_dat.id if phat_dat else None,
                "district_id": 39,  # Thuan An, Binh Duong
                "project_type": "apartment",
                "status": "selling",
                "total_units": 4982,
                "launch_date": "2025-Q2",
                "completion_date": "2028",
                "grade_primary": "H-II",
                "price_usd": 2031,
            },
            {
                "name": "TT AVIO - Orion",
                "developer_id": dev("TT Capital").id if dev("TT Capital") else None,
                "district_id": 38,  # Di An
                "project_type": "apartment",
                "status": "selling",
                "total_units": 843,
                "launch_date": "2025-Q3",
                "completion_date": "2026",
                "grade_primary": "M-I",
                "price_usd": 1670,
            },
            {
                "name": "Charm City - Charm Diamond",
                "developer_id": dev("Charm Group").id if dev("Charm Group") else None,
                "district_id": 39,  # Thuan An
                "project_type": "apartment",
                "status": "selling",
                "total_units": 547,
                "launch_date": "2025-Q2",
                "completion_date": None,
                "grade_primary": "M-I",
                "price_usd": 1720,
            },
            {
                "name": "Bcons Solary",
                "developer_id": dev("Bcons Group").id if dev("Bcons Group") else None,
                "district_id": 38,  # Di An
                "project_type": "apartment",
                "status": "selling",
                "total_units": 2650,
                "launch_date": "2025-Q3",
                "completion_date": "2027-Q3",
                "grade_primary": "M-II",
                "price_usd": 1428,
            },
            {
                "name": "A&T Sky Garden",
                "developer_id": dev("A&T Group").id if dev("A&T Group") else None,
                "district_id": 39,  # Thuan An
                "project_type": "apartment",
                "status": "completed",
                "total_units": 963,
                "launch_date": "2024-Q1",
                "completion_date": "2026-Q2",
                "grade_primary": "M-III",
                "price_usd": 1176,
            },
            {
                "name": "Orchard Hill",
                "developer_id": capitaland.id if capitaland else None,
                "district_id": 37,  # Thu Dau Mot
                "project_type": "apartment",
                "status": "completed",
                "total_units": 774,
                "launch_date": "2024-Q3",
                "completion_date": "2026-Q4",
                "grade_primary": "M-I",
                "price_usd": 1803,
            },
            {
                "name": "Orchard Heights",
                "developer_id": capitaland.id if capitaland else None,
                "district_id": 37,  # Thu Dau Mot
                "project_type": "apartment",
                "status": "completed",
                "total_units": 346,
                "launch_date": "2025-Q2",
                "completion_date": "2027-Q2",
                "grade_primary": "H-II",
                "price_usd": 2026,
            },
            {
                "name": "A&K Tower BD",
                "developer_id": dev("OBC Tower").id if dev("OBC Tower") else None,
                "district_id": 39,  # Thuan An
                "project_type": "apartment",
                "status": "selling",
                "total_units": 1155,
                "launch_date": "2025-Q3",
                "completion_date": "2027",
                "grade_primary": "M-II",
                "price_usd": 1385,
            },
            {
                "name": "Setia Garden Residence",
                "developer_id": dev("SP Setia Berhad").id if dev("SP Setia Berhad") else None,
                "district_id": 39,  # Thuan An
                "project_type": "apartment",
                "status": "selling",
                "total_units": 865,
                "launch_date": None,
                "completion_date": "2027",
                "grade_primary": "M-I",
                "price_usd": 1600,
            },
            {
                "name": "The Aspira",
                "developer_id": dev("Phuc An Gia").id if dev("Phuc An Gia") else None,
                "district_id": 38,  # Di An
                "project_type": "apartment",
                "status": "selling",
                "total_units": 1212,
                "launch_date": "2025-Q3",
                "completion_date": "2027-Q1",
                "grade_primary": "M-II",
                "price_usd": 1305,
            },
            {
                "name": "Orchard Grand",
                "developer_id": capitaland.id if capitaland else None,
                "district_id": 37,  # Thu Dau Mot
                "project_type": "apartment",
                "status": "selling",
                "total_units": 517,
                "launch_date": "2025-Q4",
                "completion_date": "2027-Q4",
                "grade_primary": "H-II",
                "price_usd": 2292,
            },
            # ── Hai Phong ────────────────────────────────────────────
            {
                "name": "Vinhomes Golden City",
                "developer_id": vinhomes.id if vinhomes else None,
                "district_id": hp_dist["Duong Kinh"].id,
                "project_type": "township",
                "status": "selling",
                "total_units": 4937,
                "launch_date": "2025-Q2",
                "completion_date": "2027",
                "grade_primary": "H-I",
                "price_usd": 3785,  # avg TH $3,352-4,219
            },
            {
                "name": "Ramond Urbaniz Hai Phong",
                "developer_id": dev("Ramond Group").id if dev("Ramond Group") else None,
                "district_id": hp_dist["Duong Kinh"].id,
                "project_type": "township",
                "status": "selling",
                "total_units": 438,
                "launch_date": "2025-Q4",
                "completion_date": "2026-Q3",
                "grade_primary": "H-II",
                "price_usd": 2606,  # avg TH $2,553-2,658
            },
            {
                "name": "HongKong Town Hai Phong",
                "developer_id": dev("Phuong Dong Group").id if dev("Phuong Dong Group") else None,
                "district_id": hp_dist["Do Son"].id,
                "project_type": "township",
                "status": "completed",
                "total_units": 79,
                "launch_date": "2023-Q3",
                "completion_date": "2025-Q3",
                "grade_primary": "H-II",
                "price_usd": 2585,
            },
            {
                "name": "Ruby Coastal City",
                "developer_id": brg_group.id if brg_group else None,
                "district_id": hp_dist["Do Son"].id,
                "project_type": "township",
                "status": "selling",
                "total_units": 682,
                "launch_date": "2017-Q3",
                "completion_date": None,
                "grade_primary": "M-I",
                "price_usd": 1724,  # avg villa $1,612-1,836
            },
            {
                "name": "Hung Ngan Riverside",
                "developer_id": dev("Hung Ngan Group").id if dev("Hung Ngan Group") else None,
                "district_id": hp_dist["Duong Kinh"].id,
                "project_type": "township",
                "status": "planning",
                "total_units": 2967,
                "launch_date": "2014-Q4",
                "completion_date": None,
                "grade_primary": None,
                "price_usd": 0,  # N/A - plan to resell
            },
            {
                "name": "NHO 25ha Duong Kinh - Hai Phong",
                "developer_id": None,
                "district_id": hp_dist["Duong Kinh"].id,
                "project_type": "township",
                "status": "planning",
                "total_units": None,
                "total_area_m2": 250000,  # 25ha = 250,000 m²
                "launch_date": "2027",
                "completion_date": None,
                "grade_primary": "M-I",
                "price_usd": 1844,  # TH asking price — most representative
            },
            {
                "name": "NHO 35ha Duong Kinh - Hai Phong",
                "developer_id": None,
                "district_id": hp_dist["Duong Kinh"].id,
                "project_type": "township",
                "status": "planning",
                "total_units": None,
                "total_area_m2": 350000,  # 35ha
                "launch_date": None,
                "completion_date": None,
                "grade_primary": "H-II",
                "price_usd": 2467,  # TH low range from 35ha proposal
            },
            {
                "name": "NHO 7.2ha Kien An - Hai Phong",
                "developer_id": None,
                "district_id": hp_dist["Kien An"].id,
                "project_type": "township",
                "status": "planning",
                "total_units": None,
                "total_area_m2": 72000,  # 7.2ha
                "launch_date": None,
                "completion_date": None,
                "grade_primary": "H-I",
                "price_usd": 3275,  # TH range $2,200-4,350 mid (from SWOT)
            },
            # ── Bac Ninh ─────────────────────────────────────────────
            {
                "name": "SC Vinhomes Bac Ninh",
                "developer_id": vinhomes.id if vinhomes else None,
                "district_id": bn_dist["Dai Phuc"].id,
                "project_type": "apartment",
                "status": "completed",
                "total_units": 568,
                "launch_date": "2015",
                "completion_date": "2018-Q3",
                "grade_primary": "H-II",
                "price_usd": 2864,
            },
            {
                "name": "Phoenix Tower Bac Ninh",
                "developer_id": dev("Bac Ninh Lotus").id if dev("Bac Ninh Lotus") else None,
                "district_id": bn_dist["Dai Phuc"].id,
                "project_type": "apartment",
                "status": "completed",
                "total_units": 381,
                "launch_date": "2017-Q3",
                "completion_date": "2019-Q3",
                "grade_primary": "M-I",
                "price_usd": 2623,
            },
            {
                "name": "Lotus Central Bac Ninh",
                "developer_id": dev("Dabaco Group").id if dev("Dabaco Group") else None,
                "district_id": bn_dist["Ninh Xa"].id,
                "project_type": "apartment",
                "status": "completed",
                "total_units": 288,
                "launch_date": "2020-Q2",
                "completion_date": "2021-Q1",
                "grade_primary": "M-I",
                "price_usd": 2817,
            },
            {
                "name": "Parkview City Bac Ninh",
                "developer_id": dev("Dabaco Group").id if dev("Dabaco Group") else None,
                "district_id": bn_dist["Ninh Xa"].id,
                "project_type": "apartment",
                "status": "completed",
                "total_units": 458,
                "launch_date": "2020-Q3",
                "completion_date": "2022-Q1",
                "grade_primary": "M-I",
                "price_usd": 2625,
            },
            {
                "name": "Hop Phu Complex",
                "developer_id": dev("Hop Phu Land").id if dev("Hop Phu Land") else None,
                "district_id": bn_dist["Vo Cuong"].id,
                "project_type": "apartment",
                "status": "completed",
                "total_units": 188,
                "launch_date": "2017",
                "completion_date": "2018-Q4",
                "grade_primary": "M-I",
                "price_usd": 2160,
            },
            {
                "name": "Green Pearl Bac Ninh",
                "developer_id": dev("Nhan Dat Tien").id if dev("Nhan Dat Tien") else None,
                "district_id": bn_dist["Vo Cuong"].id,
                "project_type": "apartment",
                "status": "completed",
                "total_units": 457,
                "launch_date": "2018-Q4",
                "completion_date": "2023-Q1",
                "grade_primary": "M-I",
                "price_usd": 2255,
            },
            {
                "name": "Him Lam Green Park",
                "developer_id": dev("Him Lam Land").id if dev("Him Lam Land") else None,
                "district_id": bn_dist["Dai Phuc"].id,
                "project_type": "township",
                "status": "completed",
                "total_units": 688,
                "launch_date": "2019-Q1",
                "completion_date": "2019-Q4",
                "grade_primary": "H-I",
                "price_usd": 4581,  # TH avg $4,581/m²
            },
            {
                "name": "Sun Group Bac Ninh P1",
                "developer_id": sun_group.id if sun_group else None,
                "district_id": bn_dist["Tien Du"].id,
                "project_type": "township",
                "status": "selling",
                "total_units": 3349,
                "launch_date": "2025-Q4",
                "completion_date": "2027-Q4",
                "grade_primary": "H-I",
                "price_usd": 4743,  # TH/SH min $4,743/m²
            },
            {
                "name": "Yen Phong Gateway",
                "developer_id": None,
                "district_id": bn_dist["Yen Phong"].id,
                "project_type": "township",
                "status": "completed",
                "total_units": 82,
                "launch_date": "2025-Q3",
                "completion_date": "2025-Q4",
                "grade_primary": "H-II",
                "price_usd": 3396,
            },
            {
                "name": "Vinhomes Hoa Long",
                "developer_id": vinhomes.id if vinhomes else None,
                "district_id": bn_dist["Hoa Long"].id,
                "project_type": "township",
                "status": "selling",
                "total_units": 3478,
                "launch_date": "2026-Q1",
                "completion_date": None,
                "grade_primary": "L",
                "price_usd": 5928,  # secondary price used as reference
            },
            {
                "name": "NHO 240ha Kim Chan - Bac Ninh",
                "developer_id": None,
                "district_id": bn_dist["Kim Chan"].id,
                "project_type": "township",
                "status": "planning",
                "total_units": None,
                "total_area_m2": 2_400_000,  # 240ha
                "launch_date": None,
                "completion_date": None,
                "grade_primary": "M-I",
                "price_usd": 2200,  # apt asking price
            },
        ]

        proj_count = 0
        price_count = 0
        for p_data in new_projects:
            price_usd = p_data.pop("price_usd")
            area = p_data.pop("total_area_m2", None)

            defaults = {k: v for k, v in p_data.items() if k != "name"}
            if area is not None:
                defaults["total_area_m2"] = area

            proj, created = get_or_create(
                session, Project,
                name=p_data["name"],
                defaults=defaults,
            )
            if created:
                proj_count += 1

            # Add price record if we have a price
            if price_usd > 0:
                _, pr_created = get_or_create(
                    session, PriceRecord,
                    project_id=proj.id, period_id=period_id,
                    defaults={
                        "price_usd_per_m2": price_usd,
                        "price_vnd_per_m2": _usd_to_vnd(price_usd),
                        "price_incl_vat": False,
                        "source_report": source,
                        "data_source": "nho_pdf",
                    },
                )
                if pr_created:
                    price_count += 1

        print(f"[New projects] {proj_count} created (of {len(new_projects)} processed)")
        print(f"[New price records] {price_count} created")

        # ── 7. Price records for existing scraped BD projects ────────
        existing_prices = [
            (99,  1266, 37, "The Maison (BD) primary price"),
            (101, 1600, 39, "Happy One Central primary price"),
            (115, 1206, 38, "Phu Dong SkyOne primary price"),
        ]
        ex_price_count = 0
        for pid, usd, _dist_id, note in existing_prices:
            p = session.get(Project, pid)
            if p is None:
                print(f"  WARNING: project id={pid} not found, skipping price")
                continue
            _, created = get_or_create(
                session, PriceRecord,
                project_id=pid, period_id=period_id,
                defaults={
                    "price_usd_per_m2": float(usd),
                    "price_vnd_per_m2": float(_usd_to_vnd(usd)),
                    "price_incl_vat": False,
                    "source_report": source,
                    "data_source": "nho_pdf",
                },
            )
            if created:
                ex_price_count += 1
                print(f"  Added price for [{pid}] {p.name}: ${usd}/m²")

        print(f"[Existing project prices] {ex_price_count} created")

        session.commit()
        print("\n✓ Seeding complete.")

        # ── Summary ──────────────────────────────────────────────────
        print("\n── Summary ────────────────────────────────────────────────")
        for city_obj in [hp, bn]:
            projs = (
                session.query(Project)
                .join(District, Project.district_id == District.id)
                .filter(District.city_id == city_obj.id)
                .all()
            )
            print(f"  {city_obj.name_en}: {len(projs)} projects in DB")
        bd = session.query(City).filter_by(name_en="Binh Duong").first()
        if bd:
            bd_ids = [d.id for d in session.query(District).filter_by(city_id=bd.id).all()]
            bd_projs = session.query(Project).filter(Project.district_id.in_(bd_ids)).count()
            print(f"  Binh Duong: {bd_projs} projects in DB")


if __name__ == "__main__":
    seed_output_reports()
