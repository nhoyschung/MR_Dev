"""Enrichment Round 2: Add more projects from remaining unmatched listings.

Handles 20 matchable listings out of 28 remaining:
- 18 identifiable new projects from URL slugs
- 2 Global City sub-project listings (via URL slug aliases)
- 8 are old apartment blocks ("tập thể") or street-level listings — unmatchable
"""

import json
import re
from pathlib import Path

from src.config import SEED_DIR
from src.db.connection import get_session
from src.db.models import City, District, Developer, Project, ScrapedListing
from src.utils.project_matcher import ProjectMatcher

# ──────────────────────────────────────────────────────────────
# New projects extracted from URL slugs of remaining unmatched listings
# Format: (project_name, bds_slug, district_id, project_type)
# ──────────────────────────────────────────────────────────────

NEW_PROJECTS_R2 = [
    # Hanoi
    ("PentStudio", "pentstudio", 27, "apartment"),                     # Tay Ho
    ("Imperial Plaza", "imperial-plaza", 29, "apartment"),             # Thanh Xuan
    ("D'El Dorado", "d-el-dorado", 27, "apartment"),                  # Tay Ho
    ("Heritage West Lake", "heritage-west-lake", 27, "apartment"),     # Tay Ho
    ("The Reflection", "the-reflection", 27, "apartment"),             # Tay Ho (Kusto Westlake)
    ("Sun Feliza", "sun-feliza", 28, "apartment"),                     # Cau Giay
    ("Platinum Long Bien", "platinum-long-bien", 30, "apartment"),     # Long Bien
    ("Sunshine Green Iconic", "sunshine-green-iconic", 30, "apartment"),  # Long Bien
    ("Mulberry Lane", "mulberry-lane", 33, "apartment"),               # Ha Dong
    # Binh Duong
    ("Thanh Binh Residence", "thanh-binh-residen", 39, "apartment"),   # Thuan An
    ("Phu Dong SkyOne", "phu-dong-skyone", 38, "apartment"),           # Di An
    ("Bcons Newsky", "bcons-newsky", 39, "apartment"),                 # Thuan An
    ("The Emerald Golf View", "the-emerald-golf", 39, "apartment"),    # Thuan An
    ("Setia Edenia", "setia-edenia", 39, "apartment"),                 # Thuan An
    ("Happy One Mori", "happy-one-mori", 39, "apartment"),             # Thuan An
    ("C-SkyView", "c-skyview", 37, "apartment"),                       # Thu Dau Mot
    ("Bcons Suoi Tien", "bcons-suoi-tien", 38, "apartment"),           # Di An
    ("The Emerald 68", "the-emerald-68", 39, "apartment"),             # Thuan An
]

# URL slug fragments → canonical project name
# Used for cases where the listing URL contains a sub-project slug
# that differs from the parent project's bds_slug
URL_SLUG_ALIASES = {
    "masteri-park-place": "The Global City - Masteri Grand View",
    "masteri-cosmo-central": "The Global City - Masteri Grand View",
}

# Name aliases for better title-based matching
NEW_ALIASES_R2 = {
    # Hanoi projects
    "PentStudio": "PentStudio",
    "Pent Studio": "PentStudio",
    "PentStudio Tay Ho": "PentStudio",
    "Imperial Plaza 360 Giai Phong": "Imperial Plaza",
    "D'El Dorado": "D'El Dorado",
    "D El Dorado": "D'El Dorado",
    "Del Dorado": "D'El Dorado",
    "Heritage West Lake": "Heritage West Lake",
    "Heritage Westlake": "Heritage West Lake",
    "The Reflection": "The Reflection",
    "The Reflection Kusto": "The Reflection",
    "Kusto Westlake": "The Reflection",
    "Sun Feliza": "Sun Feliza",
    "Platinum Long Bien": "Platinum Long Bien",
    "Sunshine Green Iconic": "Sunshine Green Iconic",
    "Mulberry Lane": "Mulberry Lane",
    # Binh Duong projects
    "Thanh Binh Residence": "Thanh Binh Residence",
    "Phu Dong SkyOne": "Phu Dong SkyOne",
    "Phu Dong Sky One": "Phu Dong SkyOne",
    "Bcons Newsky": "Bcons Newsky",
    "Bcons New Sky": "Bcons Newsky",
    "The Emerald Golf View": "The Emerald Golf View",
    "Emerald Golf View": "The Emerald Golf View",
    "Setia Edenia": "Setia Edenia",
    "Happy One Mori": "Happy One Mori",
    "C-SkyView": "C-SkyView",
    "C Sky View": "C-SkyView",
    "CSkyView": "C-SkyView",
    "Bcons Suoi Tien": "Bcons Suoi Tien",
    "Bcons Suối Tiên": "Bcons Suoi Tien",
    "The Emerald 68": "The Emerald 68",
    "Emerald 68": "The Emerald 68",
}


def add_new_projects(session) -> int:
    """Add new projects to the database."""
    added = 0
    for name, bds_slug, district_id, project_type in NEW_PROJECTS_R2:
        existing = session.query(Project).filter_by(name=name).first()
        if existing:
            if not existing.bds_slug:
                existing.bds_slug = bds_slug
                existing.bds_url = f"https://batdongsan.com.vn/du-an/{bds_slug}"
                print(f"  Updated slug: {name} -> {bds_slug}")
            continue

        district = session.get(District, district_id)
        if not district:
            print(f"  WARNING: District {district_id} not found for {name}")
            continue

        project = Project(
            name=name,
            district_id=district_id,
            project_type=project_type,
            status="selling",
            bds_slug=bds_slug,
            bds_url=f"https://batdongsan.com.vn/du-an/{bds_slug}",
        )
        session.add(project)
        session.flush()
        added += 1
        print(f"  Added: {name} (district={district.name_en}, id={project.id})")

    return added


def update_aliases(session) -> int:
    """Update the project_aliases.json file with new aliases."""
    alias_path = SEED_DIR / "project_aliases.json"

    aliases = {}
    if alias_path.exists():
        aliases = json.loads(alias_path.read_text(encoding="utf-8"))

    new_count = 0
    for alias, canonical in NEW_ALIASES_R2.items():
        project = session.query(Project).filter_by(name=canonical).first()
        if not project:
            print(f"  WARNING: Canonical project '{canonical}' not in DB, skipping alias '{alias}'")
            continue
        if alias not in aliases:
            aliases[alias] = canonical
            new_count += 1

    alias_path.write_text(
        json.dumps(aliases, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Aliases file: {len(aliases)} total ({new_count} new)")
    return new_count


def rematch_listings(session) -> tuple[int, int]:
    """Re-run project matching on all unmatched listings.

    Two-pass matching:
    1. ProjectMatcher (title-based: exact/alias/normalized/substring)
    2. URL slug matching (project bds_slug + URL_SLUG_ALIASES)
    """
    alias_path = SEED_DIR / "project_aliases.json"
    aliases = {}
    if alias_path.exists():
        aliases = json.loads(alias_path.read_text(encoding="utf-8"))

    matcher = ProjectMatcher(session, aliases=aliases)

    # Build slug → project_id map for URL-based matching
    slug_to_pid: dict[str, int] = {}
    for project in session.query(Project).filter(Project.bds_slug.isnot(None)).all():
        if project.bds_slug:
            slug_to_pid[project.bds_slug] = project.id

    # Add URL slug aliases
    for slug_alias, canonical_name in URL_SLUG_ALIASES.items():
        project = session.query(Project).filter_by(name=canonical_name).first()
        if project:
            slug_to_pid[slug_alias] = project.id

    unmatched = session.query(ScrapedListing).filter(
        ScrapedListing.matched_project_id.is_(None)
    ).all()

    matched_count = 0
    for listing in unmatched:
        # Pass 1: Title-based matching via ProjectMatcher
        pid, conf = matcher.match(listing.project_name or "")
        if pid and conf >= 0.5:
            listing.matched_project_id = pid
            matched_count += 1
            project = session.get(Project, pid)
            print(f"  Title match: '{listing.project_name[:50]}' -> {project.name} (conf={conf:.2f})")
            continue

        # Pass 2: URL slug matching
        if listing.listing_url:
            url_parts = listing.listing_url.split("/")
            if len(url_parts) >= 4:
                url_segment = url_parts[3]
                slug_part = re.sub(r'^ban-can-ho-chung-cu-', '', url_segment)

                for slug, project_id in slug_to_pid.items():
                    if slug in slug_part:
                        listing.matched_project_id = project_id
                        matched_count += 1
                        project = session.get(Project, project_id)
                        print(f"  Slug match: '{listing.project_name[:40]}' -> {project.name} (via URL: {slug})")
                        break

    return len(unmatched), matched_count


def main():
    session = get_session()

    total = session.query(ScrapedListing).count()
    matched_before = session.query(ScrapedListing).filter(
        ScrapedListing.matched_project_id.isnot(None)
    ).count()
    projects_before = session.query(Project).count()

    print("=" * 70)
    print("  ENRICHMENT ROUND 2")
    print("=" * 70)
    print(f"  Before: {projects_before} projects, {matched_before}/{total} matched")

    # Step 1: Add new projects
    print(f"\n--- Step 1: Add New Projects ---")
    added = add_new_projects(session)
    session.commit()

    # Step 2: Update aliases
    print(f"\n--- Step 2: Update Aliases ---")
    alias_count = update_aliases(session)
    session.commit()

    # Step 3: Re-match listings
    print(f"\n--- Step 3: Re-match Listings ---")
    total_unmatched, newly_matched = rematch_listings(session)
    session.commit()

    # Summary
    projects_after = session.query(Project).count()
    matched_after = session.query(ScrapedListing).filter(
        ScrapedListing.matched_project_id.isnot(None)
    ).count()

    print(f"\n{'=' * 70}")
    print(f"  RESULTS")
    print(f"{'=' * 70}")
    print(f"  Projects: {projects_before} -> {projects_after} (+{added} new)")
    print(f"  Aliases added: {alias_count}")
    print(f"  Matching: {matched_before}/{total} -> {matched_after}/{total}")
    print(f"  Newly matched: {newly_matched}")
    print(f"  Still unmatched: {total - matched_after}")
    print(f"{'=' * 70}")

    session.close()


if __name__ == "__main__":
    main()
