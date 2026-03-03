"""Enrich DB with new projects discovered from BDS scraped data.

1. Extract project names from BDS URL slugs
2. Add new projects with proper city/district FK linkage
3. Update project aliases for better matching
4. Re-match all unmatched scraped listings
"""

import json
import re
from pathlib import Path

from src.config import SEED_DIR
from src.db.connection import get_session
from src.db.models import City, District, Developer, Project, ScrapedListing
from src.utils.project_matcher import ProjectMatcher

# ──────────────────────────────────────────────────────────────
# Project definitions extracted from BDS URL slugs + listing context
# Format: (project_name, bds_slug, district_id, project_type)
# ──────────────────────────────────────────────────────────────

NEW_PROJECTS = [
    # HCMC
    ("Empire City Thu Thiem", "empire-city-thu-thiem", 2, "apartment"),
    ("Saigon Royal Residence", "saigon-royal-residence", 4, "apartment"),
    ("Paris Hoang Kim", "paris-hoang-kim", 2, "apartment"),
    ("eHome 3", "khu-can-ho-ehome-3", 12, "apartment"),  # Binh Chanh → District 12 area
    ("Eco Green Saigon", "eco-green-sai-gon", 5, "apartment"),  # Q7
    ("The Galleria Residence", "the-galleria-residence", 2, "apartment"),
    ("The Opera Residence", "the-opera-residence", 2, "apartment"),
    ("D-Aqua", "can-ho-d-aqua", 19, "apartment"),  # Q8
    ("The Pegasuite", "the-pegasuite", 19, "apartment"),  # Q8
    ("Celadon City", "the-glen-celadon-city", 16, "mixed-use"),  # Tan Phu
    # Hanoi
    ("An Binh Homeland", "an-binh-homeland", 33, "apartment"),  # Ha Dong
    ("Rivea Residences", "rivea-residences", 34, "apartment"),  # Hoang Mai
    ("The Queen 360 Giai Phong", "the-queen", 29, "apartment"),  # Thanh Xuan
    # Binh Duong
    ("Bcons Center City", "bcons-center-city", 38, "apartment"),  # Di An
    ("The Maison", "the-maison", 37, "apartment"),  # Thu Dau Mot
    ("The Gio Riverside", "the-gio-riverside", 38, "apartment"),  # Di An
    ("Happy One Central", "happy-one-central", 37, "apartment"),  # Thu Dau Mot
    ("Compass One", "compass-one", 37, "apartment"),  # Thu Dau Mot
    ("Legacy Central", "legacy-prime", 39, "apartment"),  # Thuan An (Legacy Prime/Central same complex)
    ("The Emerald Garden View", "the-emerald-garden-view", 39, "apartment"),  # Thuan An
]

# Aliases: scraped name variants → canonical DB project name
# These improve matching for listings whose titles don't contain the project name directly
NEW_ALIASES = {
    # Vinhomes Grand Park sub-projects
    "The Origami": "Vinhomes Grand Park",
    "The Origami Vinhomes Grand Park": "Vinhomes Grand Park",
    "Origami": "Vinhomes Grand Park",
    "The Beverly Solari": "Vinhomes Grand Park",
    "Beverly Solari": "Vinhomes Grand Park",
    "The Beverly Solari Vinhomes Grand Park": "Vinhomes Grand Park",
    # The Global City sub-projects
    "Masteri Park Place": "The Global City - Masteri Grand View",
    "Masteri Cosmo Central": "The Global City - Masteri Grand View",
    "Global City": "The Global City - Masteri Grand View",
    # Vinhomes Ocean Park sub-zones
    "Vinhomes Ocean Park Gia Lam": "Vinhomes Ocean Park",
    # Empire City
    "Empire City": "Empire City Thu Thiem",
    # Celadon
    "The Glen Celadon City": "Celadon City",
    "The Glen": "Celadon City",
    # Eco Green
    "Eco Green Sài Gòn": "Eco Green Saigon",
    # eHome
    "eHome 3": "eHome 3",
    "Ehome 3": "eHome 3",
    # Legacy
    "Legacy Prime": "Legacy Central",
    "Legacy Central": "Legacy Central",
    # Bcons
    "Bcons Center City": "Bcons Center City",
    # The Gio
    "The Gio Riverside": "The Gio Riverside",
    # Noble Crystal
    "Noble Crystal Tay Ho": "Noble Crystal Tay Ho",
    "Noble Crystal": "Noble Crystal Tay Ho",
}


def add_new_projects(session) -> int:
    """Add new projects to the database."""
    added = 0
    for name, bds_slug, district_id, project_type in NEW_PROJECTS:
        existing = session.query(Project).filter_by(name=name).first()
        if existing:
            # Update bds_slug if missing
            if not existing.bds_slug:
                existing.bds_slug = bds_slug
                existing.bds_url = f"https://batdongsan.com.vn/du-an/{bds_slug}"
                print(f"  Updated slug: {name} → {bds_slug}")
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
    for alias, canonical in NEW_ALIASES.items():
        # Only add if the canonical project exists in DB
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


def update_existing_bds_slugs(session) -> int:
    """Update bds_slug for existing projects found in scraped URLs."""
    # Map from URL slug fragment → existing project name
    SLUG_UPDATES = {
        "masteri-thao-dien": "Masteri Thao Dien",
        "masteri-an-phu": "Masteri An Phu",
        "lumiere-riverside": "Lumiere Riverside",
        "vinhomes-grand-park": "Vinhomes Grand Park",
        "vinhomes-central-park": "Vinhomes Central Park",
        "eaton-park": "Eaton Park",
        "westgate": "Westgate",
        "the-river": "The River",
        "picity-sky-park": "Picity Sky Park",
        "vinhomes-ocean-park": "Vinhomes Ocean Park",
        "vinhomes-smart-city": "Vinhomes Smart City",
        "noble-crystal-tay-ho": "Noble Crystal Tay Ho",
    }
    updated = 0
    for slug, pname in SLUG_UPDATES.items():
        project = session.query(Project).filter_by(name=pname).first()
        if project and not project.bds_slug:
            project.bds_slug = slug
            project.bds_url = f"https://batdongsan.com.vn/du-an/{slug}"
            updated += 1
            print(f"  Slug: {pname} → {slug}")
    return updated


def rematch_listings(session) -> tuple[int, int]:
    """Re-run project matching on all unmatched listings."""
    alias_path = SEED_DIR / "project_aliases.json"
    aliases = {}
    if alias_path.exists():
        aliases = json.loads(alias_path.read_text(encoding="utf-8"))

    matcher = ProjectMatcher(session, aliases=aliases)

    unmatched = session.query(ScrapedListing).filter(
        ScrapedListing.matched_project_id.is_(None)
    ).all()

    matched_count = 0
    for listing in unmatched:
        # Try matching listing title
        pid, conf = matcher.match(listing.project_name or "")
        if pid and conf >= 0.5:
            listing.matched_project_id = pid
            matched_count += 1
            project = session.get(Project, pid)
            print(f"  Matched: '{listing.project_name[:50]}' → {project.name} (conf={conf:.2f})")
            continue

        # Try extracting project name from URL slug
        if listing.listing_url:
            url_parts = listing.listing_url.split("/")
            if len(url_parts) >= 4:
                url_segment = url_parts[3]
                # Remove category prefix
                slug_part = re.sub(r'^ban-can-ho-chung-cu-', '', url_segment)
                # Try matching the slug against project bds_slugs
                for project in session.query(Project).filter(Project.bds_slug.isnot(None)).all():
                    if project.bds_slug and project.bds_slug in slug_part:
                        listing.matched_project_id = project.id
                        matched_count += 1
                        print(f"  Slug match: '{listing.project_name[:40]}' → {project.name} (via URL)")
                        break

    return len(unmatched), matched_count


def main():
    session = get_session()

    total_before = session.query(ScrapedListing).count()
    matched_before = session.query(ScrapedListing).filter(
        ScrapedListing.matched_project_id.isnot(None)
    ).count()
    projects_before = session.query(Project).count()

    print("=" * 70)
    print("  ENRICH DB FROM SCRAPED DATA")
    print("=" * 70)
    print(f"  Before: {projects_before} projects, {matched_before}/{total_before} matched")

    # Step 1: Add new projects
    print(f"\n--- Step 1: Add New Projects ---")
    added = add_new_projects(session)
    session.commit()

    # Step 2: Update existing project slugs
    print(f"\n--- Step 2: Update BDS Slugs ---")
    slug_updated = update_existing_bds_slugs(session)
    session.commit()

    # Step 3: Update aliases
    print(f"\n--- Step 3: Update Aliases ---")
    alias_count = update_aliases(session)
    session.commit()

    # Step 4: Re-match listings
    print(f"\n--- Step 4: Re-match Listings ---")
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
    print(f"  Projects: {projects_before} → {projects_after} (+{added} new)")
    print(f"  Slugs updated: {slug_updated}")
    print(f"  Aliases added: {alias_count}")
    print(f"  Matching: {matched_before}/{total_before} → {matched_after}/{total_before}")
    print(f"  Newly matched: {newly_matched}")
    print(f"  Still unmatched: {total_before - matched_after}")
    print(f"{'=' * 70}")

    session.close()


if __name__ == "__main__":
    main()
