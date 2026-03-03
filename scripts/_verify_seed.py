"""Quick verification of seeded Output report data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.connection import get_session
from src.db.models import City, District, Project, PriceRecord
from sqlalchemy import func

with get_session() as session:
    cities = session.query(City).all()
    print(f"Total cities: {len(cities)}")
    for c in cities:
        print(f"  [{c.id}] {c.name_en} ({c.region})")

    for city_name in ["Hai Phong", "Bac Ninh"]:
        city = next((c for c in cities if c.name_en == city_name), None)
        if not city:
            print(f"\n{city_name}: NOT FOUND")
            continue
        dists = session.query(District).filter_by(city_id=city.id).all()
        dist_ids = [d.id for d in dists]
        projs = session.query(Project).filter(Project.district_id.in_(dist_ids)).all()
        print(f"\n{city_name} projects ({len(projs)}):")
        for p in projs:
            pr = session.query(PriceRecord).filter_by(project_id=p.id).first()
            price_str = f"${pr.price_usd_per_m2:,.0f}/m2" if pr and pr.price_usd_per_m2 else "N/A"
            d = session.get(District, p.district_id)
            print(f"  {p.name[:38]} | {p.grade_primary} | {p.status} | {price_str}")

    print("\nNew BD projects (ids 123-134):")
    for pid in range(123, 135):
        p = session.get(Project, pid)
        if p:
            pr = session.query(PriceRecord).filter_by(project_id=pid).first()
            price_str = f"${pr.price_usd_per_m2:,.0f}" if pr and pr.price_usd_per_m2 else "N/A"
            print(f"  [{pid}] {p.name[:38]} | {p.grade_primary} | {price_str}")

    pr_counts = session.query(PriceRecord.data_source, func.count(PriceRecord.id)).group_by(PriceRecord.data_source).all()
    print(f"\nPrice records by source: {dict(pr_counts)}")
    print(f"Total projects: {session.query(Project).count()}")
