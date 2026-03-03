"""Show remaining unmatched listings."""
from src.db.connection import get_session
from src.db.models import ScrapedListing

session = get_session()
unmatched = session.query(ScrapedListing).filter(
    ScrapedListing.matched_project_id.is_(None)
).all()

print(f"Remaining unmatched: {len(unmatched)}\n")
for l in unmatched:
    price = f"{l.price_vnd/1e9:.1f}ty" if l.price_vnd else l.price_raw or "N/A"
    url_slug = ""
    if l.listing_url:
        parts = l.listing_url.split("/")
        if len(parts) >= 4:
            url_slug = parts[3].replace("ban-can-ho-chung-cu-", "")[:50]
    print(f"  [{l.bds_listing_id}] {l.project_name[:60]}")
    print(f"    {price} | {l.district_name}, {l.city_name} | slug: {url_slug}")
    print()
session.close()
