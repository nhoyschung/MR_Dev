"""Collect price data from developer/distributor websites for Binh Duong projects.

Sources scraped:
  - angialand.com.vn      → Le Phong Group distributor (Emerald series)
  - bconsvietnam.com.vn   → Bcons Group developer
  - datxanh.homes         → Dat Xanh Group (Opal Boulevard)
  - phudonggroup.com.vn   → Phu Dong Group (Sky One)
  - rever.vn              → Multi-project aggregator (C-SkyView)
  - picity.com.vn         → Phat Dat Group (Picity Sky Park)

Prices stored with data_source='distributor_web', period = 2025 H1 (id=9).
Idempotent: skips project if (project_id, period_id, data_source='distributor_web') exists.

Usage:
    python -m scripts.collect_distributor_prices
    python -m scripts.collect_distributor_prices --dry-run
    python -m scripts.collect_distributor_prices --period-id 10
"""

import argparse
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.connection import get_session
from src.db.models import DataLineage, PriceRecord, SourceReport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Price parsing ──────────────────────────────────────────────────────────────
# Matches patterns like: "37 triệu/m²", "42.5tr/m2", "55 triệu đồng/m²"
_MILLION_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:triệu|tr)[^\d/]*/?[^\d]*m²?",
    re.IGNORECASE | re.UNICODE,
)

# Matches raw VND amounts: "37.000.000 đ/m²" or "37,000,000/m²"
_RAW_VND_PATTERN = re.compile(
    r"(\d{2,3}(?:[.,]\d{3}){2})\s*(?:đ|vnđ|đồng)?[^\d]*/?[^\d]*m²?",
    re.IGNORECASE | re.UNICODE,
)


def _parse_prices_from_text(text: str) -> list[float]:
    """Extract all VND/m² prices from plain text. Returns list in VND."""
    prices: list[float] = []

    for m in _MILLION_PATTERN.finditer(text):
        val_str = m.group(1).replace(",", ".")
        try:
            prices.append(float(val_str) * 1_000_000)
        except ValueError:
            pass

    for m in _RAW_VND_PATTERN.finditer(text):
        val_str = re.sub(r"[.,]", "", m.group(1))
        try:
            val = float(val_str)
            if 10_000_000 <= val <= 200_000_000:  # sanity: 10M–200M VND/m²
                prices.append(val)
        except ValueError:
            pass

    return prices


def extract_price_from_html(html: str) -> Optional[float]:
    """Parse median VND/m² from page HTML. Returns None if nothing found."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/styles to reduce noise
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    prices = _parse_prices_from_text(text)
    if not prices:
        return None
    prices.sort()
    # Return median (robust against outliers)
    mid = len(prices) // 2
    return prices[mid]


# ── HTTP fetching ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}


def fetch_html(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch URL; returns HTML string or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        logger.debug("HTTP %d for %s", resp.status_code, url)
        return None
    except Exception as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
        return None


# ── Source definitions ─────────────────────────────────────────────────────────
# price_min/max are from research agent findings (VND/m²), used as fallback.
# urls: ordered list to try; first successful fetch with a parseable price wins.
DISTRIBUTOR_SOURCES = [
    # ── Emerald series (Le Phong Group / Ang Gia Land distributor) ──
    {
        "project_id": 117,
        "project_name": "The Emerald Golf View",
        "source_name": "angialand.com.vn",
        "urls": [
            "https://angialand.com.vn/du-an/the-emerald-golf-view/",
            "https://angialand.com.vn/the-emerald-golf-view/",
            "https://angialand.com.vn/can-ho-the-emerald-golf-view/",
        ],
        "price_min_vnd": 37_000_000,
        "price_max_vnd": 45_000_000,
        "source_url": "https://angialand.com.vn",
    },
    {
        "project_id": 104,
        "project_name": "The Emerald Garden View",
        "source_name": "angialand.com.vn",
        "urls": [
            "https://angialand.com.vn/du-an/the-emerald-garden-view/",
            "https://angialand.com.vn/the-emerald-garden-view/",
            "https://angialand.com.vn/can-ho-the-emerald-garden-view/",
        ],
        "price_min_vnd": 30_000_000,
        "price_max_vnd": 35_000_000,
        "source_url": "https://angialand.com.vn",
    },
    {
        "project_id": 122,
        "project_name": "The Emerald 68",
        "source_name": "angialand.com.vn",
        "urls": [
            "https://angialand.com.vn/du-an/the-emerald-68/",
            "https://angialand.com.vn/the-emerald-68/",
            "https://datxanh.homes/du-an/the-emerald-68/",
        ],
        "price_min_vnd": 42_000_000,
        "price_max_vnd": 68_000_000,
        "source_url": "https://angialand.com.vn",
    },
    # ── Bcons Group ──
    {
        "project_id": 16,
        "project_name": "Bcons City",
        "source_name": "bconsvietnam.com.vn",
        "urls": [
            "https://bconsvietnam.com.vn/du-an/bcons-city/",
            "https://bconsvietnam.com.vn/bcons-city/",
            "https://bconsps.net/bcons-city/",
            "https://bconsps.net/du-an/bcons-city/",
        ],
        "price_min_vnd": 52_000_000,
        "price_max_vnd": 56_000_000,
        "source_url": "https://bconsvietnam.com.vn",
    },
    {
        "project_id": 98,
        "project_name": "Bcons Center City",
        "source_name": "bconsvietnam.com.vn",
        "urls": [
            "https://bconsvietnam.com.vn/du-an/bcons-center-city/",
            "https://bconsvietnam.com.vn/bcons-center-city/",
            "https://bconsps.net/bcons-center-city/",
            "https://bconsps.net/du-an/bcons-center-city/",
        ],
        "price_min_vnd": 54_000_000,
        "price_max_vnd": 57_000_000,
        "source_url": "https://bconsvietnam.com.vn",
    },
    {
        "project_id": 116,
        "project_name": "Bcons Newsky",
        "source_name": "bconsvietnam.com.vn",
        "urls": [
            "https://bconsvietnam.com.vn/du-an/bcons-newsky/",
            "https://bconsvietnam.com.vn/bcons-newsky/",
            "https://bconsps.net/bcons-newsky/",
            "https://bconsps.net/du-an/bcons-newsky/",
        ],
        "price_min_vnd": 40_000_000,
        "price_max_vnd": 45_000_000,
        "source_url": "https://bconsvietnam.com.vn",
    },
    # ── Dat Xanh Group ──
    {
        "project_id": 43,
        "project_name": "Opal Boulevard",
        "source_name": "datxanh.homes",
        "urls": [
            "https://datxanh.homes/du-an/opal-boulevard/",
            "https://datxanh.homes/opal-boulevard/",
            "https://datxanh.vn/du-an/opal-boulevard/",
        ],
        "price_min_vnd": 30_000_000,
        "price_max_vnd": 37_600_000,
        "source_url": "https://datxanh.homes",
    },
    # ── Phu Dong Group ──
    {
        "project_id": 115,
        "project_name": "Phu Dong SkyOne",
        "source_name": "phudonggroup.com.vn",
        "urls": [
            "https://phudonggroup.com.vn/du-an/phu-dong-sky-one/",
            "https://phudonggroup.com.vn/phu-dong-sky-one/",
            "https://phudonggroup.com.vn/phu-dong-skyOne/",
        ],
        "price_min_vnd": 31_500_000,
        "price_max_vnd": 34_000_000,
        "source_url": "https://phudonggroup.com.vn",
    },
    # ── C-SkyView (Rever aggregator) ──
    {
        "project_id": 120,
        "project_name": "C-SkyView",
        "source_name": "rever.vn",
        "urls": [
            "https://rever.vn/du-an/c-sky-view/",
            "https://rever.vn/du-an/c-skyview/",
            "https://rever.vn/du-an/c-sky-view-binh-duong/",
        ],
        "price_min_vnd": 31_000_000,
        "price_max_vnd": 35_000_000,
        "source_url": "https://rever.vn",
    },
    # ── Picity Sky Park (Phat Dat) ──
    {
        "project_id": 15,
        "project_name": "Picity Sky Park",
        "source_name": "phatdat.vn",
        "urls": [
            "https://phatdat.vn/du-an/picity-sky-park/",
            "https://picity.com.vn/",
            "https://rever.vn/du-an/picity-sky-park/",
        ],
        "price_min_vnd": 38_000_000,
        "price_max_vnd": 46_000_000,
        "source_url": "https://phatdat.vn",
    },
]


# ── Price record helpers ───────────────────────────────────────────────────────

def check_existing(session, project_id: int, period_id: int) -> bool:
    """Return True if a distributor_web record already exists."""
    return (
        session.query(PriceRecord)
        .filter_by(
            project_id=project_id,
            period_id=period_id,
            data_source="distributor_web",
        )
        .first()
        is not None
    )


def store_price(
    session,
    project_id: int,
    period_id: int,
    price_vnd: float,
    source_url: str,
    source_name: str,
    scraped: bool,
    dry_run: bool,
) -> None:
    """Insert price record + lineage. Commits if not dry_run."""
    note = "(live scrape)" if scraped else "(research fallback)"
    logger.info(
        "  [%s] Storing %.1fM VND/m² %s",
        source_name,
        price_vnd / 1_000_000,
        note,
    )

    if dry_run:
        return

    source_report = SourceReport(
        filename=f"distributor_{source_name}",
        report_type="distributor_web",
        ingested_at=datetime.now(timezone.utc),
        status="completed",
    )
    session.add(source_report)
    session.flush()

    confidence = 0.8 if scraped else 0.7  # slightly lower for fallback
    price_record = PriceRecord(
        project_id=project_id,
        period_id=period_id,
        price_vnd_per_m2=price_vnd,
        price_incl_vat=True,
        source_report=source_url,
        data_source="distributor_web",
    )
    session.add(price_record)
    session.flush()

    lineage = DataLineage(
        table_name="price_records",
        record_id=price_record.id,
        source_report_id=source_report.id,
        confidence_score=confidence,
        extracted_at=datetime.now(timezone.utc),
    )
    session.add(lineage)
    session.commit()


# ── Main ───────────────────────────────────────────────────────────────────────

def run(period_id: int = 9, dry_run: bool = False) -> None:
    label = "[DRY RUN] " if dry_run else ""
    print("=" * 70)
    print(f"  {label}Binh Duong Distributor Price Collection")
    print(f"  Period ID: {period_id}  |  Sources: {len(DISTRIBUTOR_SOURCES)}")
    print("=" * 70)

    session = get_session()
    stored = 0
    skipped = 0
    live_scraped = 0
    fallback_used = 0

    for src in DISTRIBUTOR_SOURCES:
        pid = src["project_id"]
        name = src["project_name"]

        print(f"\n  [{pid}] {name}")
        print(f"       Source: {src['source_name']}")

        # Check idempotency
        if not dry_run and check_existing(session, pid, period_id):
            print(f"       => SKIP (distributor_web record already exists for period {period_id})")
            skipped += 1
            continue

        # Fallback price = midpoint of research range
        fallback_vnd = (src["price_min_vnd"] + src["price_max_vnd"]) / 2
        price_vnd = None
        used_url = src["source_url"]

        # Try live fetch
        for url in src["urls"]:
            print(f"       Trying: {url}")
            html = fetch_html(url)
            if html is None:
                continue

            parsed = extract_price_from_html(html)
            if parsed:
                # Sanity check: must be within 30% of the research range
                lo = src["price_min_vnd"] * 0.7
                hi = src["price_max_vnd"] * 1.3
                if lo <= parsed <= hi:
                    price_vnd = parsed
                    used_url = url
                    live_scraped += 1
                    print(f"       => Live price: {parsed / 1_000_000:.1f}M VND/m²")
                    break
                else:
                    logger.debug(
                        "Parsed price %.1fM out of expected range [%.1f–%.1f]M, ignoring",
                        parsed / 1_000_000,
                        src["price_min_vnd"] / 1_000_000,
                        src["price_max_vnd"] / 1_000_000,
                    )

            time.sleep(1.5)  # polite delay between URL attempts

        if price_vnd is None:
            # Use fallback
            price_vnd = fallback_vnd
            fallback_used += 1
            print(
                f"       => Fallback: {price_vnd / 1_000_000:.1f}M VND/m²"
                f"  (range {src['price_min_vnd']/1_000_000:.0f}–"
                f"{src['price_max_vnd']/1_000_000:.0f}M, research data)"
            )

        store_price(
            session,
            project_id=pid,
            period_id=period_id,
            price_vnd=price_vnd,
            source_url=used_url,
            source_name=src["source_name"],
            scraped=(price_vnd != fallback_vnd or live_scraped > fallback_used),
            dry_run=dry_run,
        )
        stored += 1

        time.sleep(2.0)  # polite delay between projects

    session.close()

    print(f"\n{'=' * 70}")
    print(f"  {label}COMPLETE")
    print(f"    Stored:        {stored}")
    print(f"    Skipped:       {skipped} (already had distributor_web record)")
    print(f"    Live scraped:  {live_scraped}")
    print(f"    Fallback used: {fallback_used}")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect distributor prices for Binh Duong")
    parser.add_argument(
        "--period-id",
        type=int,
        default=9,
        help="Report period ID to store prices under (default: 9 = 2025 H1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be stored without writing to DB",
    )
    args = parser.parse_args()
    run(period_id=args.period_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
