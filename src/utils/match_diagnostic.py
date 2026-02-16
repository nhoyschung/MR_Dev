"""Diagnostic script: measure project name matching rate across extracted data."""

import json
from pathlib import Path

from src.config import SEED_DIR
from src.db.connection import engine, get_session
from src.db.models import Base
from src.seeders.city_seeder import CitySeeder
from src.seeders.developer_seeder import DeveloperSeeder
from src.seeders.grade_seeder import GradeSeeder
from src.seeders.project_seeder import ProjectSeeder
from src.utils.project_matcher import ProjectMatcher

EXTRACTED_DIR = SEED_DIR / "extracted"

# JSON files that contain a "project_name" field
EXTRACTED_FILES = [
    "casestudy_blocks.json",
    "casestudy_facilities.json",
    "casestudy_sales_points.json",
    "casestudy_unit_types.json",
    "market_sales_statuses.json",
    "market_unit_types.json",
    "market_facilities.json",
    "price_factors.json",
]


def run_diagnostic() -> None:
    """Load extracted data, run matcher, and print results."""
    # Ensure DB is seeded with reference data + projects
    Base.metadata.create_all(engine)
    session = get_session()

    # Seed prerequisite data
    CitySeeder(session, SEED_DIR).seed()
    GradeSeeder(session, SEED_DIR).seed()
    DeveloperSeeder(session, SEED_DIR).seed()
    ProjectSeeder(session, SEED_DIR).seed()

    # Load aliases
    alias_path = SEED_DIR / "project_aliases.json"
    aliases: dict[str, str] = {}
    if alias_path.exists():
        aliases = json.loads(alias_path.read_text(encoding="utf-8"))

    matcher = ProjectMatcher(session, aliases=aliases)

    # Collect all unique project names from extracted files
    all_names: set[str] = set()
    for filename in EXTRACTED_FILES:
        filepath = EXTRACTED_DIR / filename
        if not filepath.exists():
            continue
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        for record in data:
            name = record.get("project_name", "")
            if name:
                all_names.add(name)

    # Run matching
    matched: list[tuple[str, int, float]] = []
    unmatched: list[str] = []
    junk_filtered: list[str] = []

    for name in sorted(all_names):
        if matcher.is_junk_name(name):
            junk_filtered.append(name)
            continue
        pid, confidence = matcher.match(name)
        if pid is not None and confidence >= 0.5:
            matched.append((name, pid, confidence))
        else:
            unmatched.append(name)

    total = len(all_names)
    junk_count = len(junk_filtered)
    real_names = total - junk_count
    match_count = len(matched)
    match_rate = (match_count / real_names * 100) if real_names > 0 else 0

    print(f"\n{'='*60}")
    print(f"  Project Name Matching Diagnostic")
    print(f"{'='*60}")
    print(f"  Total unique names:     {total}")
    print(f"  Junk names filtered:    {junk_count}")
    print(f"  Real project names:     {real_names}")
    print(f"  Matched:                {match_count}")
    print(f"  Unmatched:              {len(unmatched)}")
    print(f"  Match rate:             {match_rate:.1f}%")
    print(f"{'='*60}")

    if matched:
        print(f"\n  Matched ({match_count}):")
        for name, pid, conf in matched:
            print(f"    [{conf:.2f}] {name} -> project_id={pid}")

    if unmatched:
        print(f"\n  Unmatched ({len(unmatched)}):")
        for name in unmatched:
            print(f"    - {name}")

    if junk_filtered:
        print(f"\n  Junk filtered ({junk_count}):")
        for name in junk_filtered:
            print(f"    x {name}")

    # Save results to JSON for further processing
    output = {
        "summary": {
            "total": total,
            "junk_count": junk_count,
            "real_names": real_names,
            "matched": match_count,
            "unmatched": len(unmatched),
            "match_rate": match_rate,
        },
        "matched": [{"name": n, "project_id": pid, "confidence": c} for n, pid, c in matched],
        "unmatched": unmatched,
        "junk_filtered": junk_filtered,
    }
    output_path = SEED_DIR / "match_diagnostic_results.json"
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults saved to: {output_path}")

    session.close()


if __name__ == "__main__":
    run_diagnostic()
