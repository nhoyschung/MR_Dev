"""Aggregate scraped office listings into district-level rent summaries.

BDS office listings are small/medium offices (Grade B/C market), not Grade A towers.
This script groups scraped data by district and upserts into office_market_summaries.

Usage:
    python -m scripts.aggregate_office_scraped [--dry-run] [--period-id N]
"""

import argparse
import statistics
from collections import defaultdict
from datetime import datetime, timezone

from src.db.connection import get_session
from src.db.models import City, District, OfficeMarketSummary, ScrapedOfficeListing

# Map ward-level names that appear in BDS to their parent district
WARD_TO_DISTRICT: dict[str, str] = {
    "Nguyễn Cư Trinh": "Quận 3",
    "Võ Thị Sáu": "Quận 3",
    "Phường 2": "Quận 3",
    "Phường 3": "Quận 3",
    "Phường 6": "Quận 3",
    "Bến Thành": "Quận 1",
    "Phường 25": "Bình Thạnh",
    "Tây Thạnh": "Tân Bình",
    "Tân Hưng": "Quận 7",
}

# Normalize scraped city_name values → canonical DB name
CITY_NORMALIZE: dict[str, str] = {
    "TP. Hồ Chí Minh": "Hồ Chí Minh",
    "Tp. Hồ Chí Minh": "Hồ Chí Minh",
    "TP HCM": "Hồ Chí Minh",
    "TPHCM": "Hồ Chí Minh",
    "Hồ Chí Minh": "Hồ Chí Minh",
    "Ho Chi Minh": "Hồ Chí Minh",
    "Hà Nội": "Hà Nội",
    "Hanoi": "Hà Nội",
}

# Grade classification by rent (VND/m²/month)
# Based on HCMC office market benchmarks
def classify_grade(rent_vnd: float) -> str:
    if rent_vnd >= 500_000:
        return "A"
    elif rent_vnd >= 250_000:
        return "B"
    else:
        return "C"


def normalize_district(raw: str) -> str | None:
    """Map ward names to district, pass through district names."""
    if raw in WARD_TO_DISTRICT:
        return WARD_TO_DISTRICT[raw]
    # Drop generic "Phường X" entries that can't be mapped
    if raw.startswith("Phường ") and raw[7:].isdigit():
        return None
    return raw


def main(dry_run: bool = False, period_id: int | None = None) -> None:
    session = get_session()

    try:
        # ── 1. Gather all staged office listings with rent data ────────────────
        listings = (
            session.query(ScrapedOfficeListing)
            .filter(ScrapedOfficeListing.rent_vnd_per_m2_month.isnot(None))
            .all()
        )
        print(f"Loaded {len(listings)} office listings with rent data")

        # ── 2. Group by district (all scraped data is HCMC) ───────────────────
        # Structure: {district: {"A": [...], "B": [...], "C": [...]}}
        by_district: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: {"A": [], "B": [], "C": []}
        )
        # Track which city each district belongs to (for DB lookup)
        district_city: dict[str, str] = {}

        skipped = 0
        for l in listings:
            raw_city = l.city_name or "Hồ Chí Minh"
            city = CITY_NORMALIZE.get(raw_city, "Hồ Chí Minh")
            if not l.district_name:
                skipped += 1
                continue
            district = normalize_district(l.district_name)
            if not district:
                skipped += 1
                continue
            grade = classify_grade(l.rent_vnd_per_m2_month)
            by_district[district][grade].append(l.rent_vnd_per_m2_month)
            district_city[district] = city

        print(f"Skipped {skipped} listings (no district info)")
        print(f"Districts found: {len(by_district)}")
        print()

        # ── 3. Print summary table ─────────────────────────────────────────────
        _EXCHANGE = 25_300  # VND/USD reference

        print(f"{'District':30s} {'n':>4} {'Avg VND/m2/mo':>15} {'Avg USD/m2/mo':>14} {'Grade mix':>20}")
        print("-" * 90)

        results = []
        for district, grades in sorted(by_district.items(), key=lambda x: -sum(len(v) for v in x[1].values())):
            all_rents = grades["A"] + grades["B"] + grades["C"]
            n = len(all_rents)
            avg_vnd = statistics.mean(all_rents)
            avg_usd = avg_vnd / _EXCHANGE
            grade_mix = f"A:{len(grades['A'])} B:{len(grades['B'])} C:{len(grades['C'])}"
            print(f"{district:30s} {n:4d} {avg_vnd:15,.0f} {avg_usd:14.1f} {grade_mix:>20}")
            results.append({
                "city": district_city.get(district, "Hồ Chí Minh"),
                "district": district,
                "n": n,
                "avg_vnd": avg_vnd,
                "avg_usd": avg_usd,
                "grades": grades,
            })

        print()
        if dry_run:
            print("[DRY RUN] No DB changes made.")
            return

        # ── 4. Look up City/District IDs ──────────────────────────────────────
        city_map: dict[str, int] = {}
        for c in session.query(City).all():
            city_map[c.name_vi] = c.id
            city_map[c.name_en] = c.id

        district_map: dict[str, int] = {}
        for d in session.query(District).all():
            if d.name_vi:
                district_map[d.name_vi] = d.id
            if d.name_en:
                district_map[d.name_en] = d.id

        # ── 5. Upsert into office_market_summaries ────────────────────────────
        if period_id is None:
            # Use most recent period in DB
            from src.db.models import ReportPeriod
            p = session.query(ReportPeriod).order_by(ReportPeriod.id.desc()).first()
            period_id = p.id if p else None

        upserted = 0
        skipped_no_city = 0

        for r in results:
            # Resolve city_id
            city_id = city_map.get(r["city"]) or city_map.get("Hồ Chí Minh") or city_map.get("Ho Chi Minh City") or next(iter(city_map.values()), None)
            if not city_id:
                skipped_no_city += 1
                continue

            district_id = district_map.get(r["district"])

            # Check if summary exists for (city, district, period)
            existing = (
                session.query(OfficeMarketSummary)
                .filter_by(
                    city_id=city_id,
                    district_id=district_id,
                    period_id=period_id,
                )
                .first()
            )

            avg_rent_b = (
                statistics.mean(r["grades"]["B"]) / _EXCHANGE
                if r["grades"]["B"]
                else None
            )
            avg_rent_c = (
                statistics.mean(r["grades"]["C"]) / _EXCHANGE
                if r["grades"]["C"]
                else None
            )
            avg_rent_a = (
                statistics.mean(r["grades"]["A"]) / _EXCHANGE
                if r["grades"]["A"]
                else None
            )

            if existing:
                # Update rent fields if scraped data is newer/additional
                if avg_rent_b and existing.avg_rent_usd_grade_b is None:
                    existing.avg_rent_usd_grade_b = round(avg_rent_b, 2)
                if avg_rent_c and existing.avg_rent_usd_grade_c is None:
                    existing.avg_rent_usd_grade_c = round(avg_rent_c, 2)
                if avg_rent_a and existing.avg_rent_usd_grade_a is None:
                    existing.avg_rent_usd_grade_a = round(avg_rent_a, 2)
                existing.notes = (
                    (existing.notes or "") +
                    f" | BDS scraped {r['n']} listings avg {r['avg_usd']:.1f} USD/m2/mo"
                )
            else:
                summary = OfficeMarketSummary(
                    city_id=city_id,
                    district_id=district_id,
                    period_id=period_id,
                    avg_rent_usd_grade_a=round(avg_rent_a, 2) if avg_rent_a else None,
                    avg_rent_usd_grade_b=round(avg_rent_b, 2) if avg_rent_b else None,
                    avg_rent_usd_grade_c=round(avg_rent_c, 2) if avg_rent_c else None,
                    notes=(
                        f"BDS scraped aggregate: {r['n']} listings, "
                        f"avg {r['avg_usd']:.1f} USD/m2/mo "
                        f"(A:{len(r['grades']['A'])} B:{len(r['grades']['B'])} C:{len(r['grades']['C'])})"
                    ),
                )
                session.add(summary)

            upserted += 1

        session.commit()
        print(f"Upserted {upserted} district summaries into office_market_summaries")
        if skipped_no_city:
            print(f"Skipped {skipped_no_city} entries (city not found in DB)")

    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate scraped office data by district")
    parser.add_argument("--dry-run", action="store_true", help="Print only, no DB writes")
    parser.add_argument("--period-id", type=int, default=None, help="Report period ID (default: latest)")
    args = parser.parse_args()
    main(dry_run=args.dry_run, period_id=args.period_id)
