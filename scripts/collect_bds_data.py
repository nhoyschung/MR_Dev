"""Collect real estate listing data from batdongsan.com.vn for all cities.

Uses fresh browser instances per city and human-like behavior to avoid blocks.
"""

import asyncio
import logging
import random
import re
import sys
from datetime import datetime, timezone

from src.db.connection import get_session
from src.db.models import ScrapeJob, ScrapedListing
from src.scrapers.config import BDS_BASE_URL, CITY_SLUGS
from src.scrapers.parsers import (
    clean_project_name,
    parse_area_sqm,
    parse_int_from_text,
    parse_price_per_sqm,
    parse_price_vnd,
)
from src.scrapers.pipeline import ScrapePipeline
from src.scrapers.selectors import ProjectListSelectors as S

from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_PR_ID_PATTERN = re.compile(r"pr(\d+)")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


def _parse_location(text: str):
    if not text:
        return None, None
    text = text.lstrip("·•\n\r\t ").strip()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    if len(parts) == 1:
        return parts[0], None
    return None, None


async def _parse_card(card):
    title_el = await card.query_selector(S.CARD_TITLE)
    if not title_el:
        return None
    raw_name = await title_el.inner_text()
    name = clean_project_name(raw_name)
    if not name:
        return None

    link_el = await card.query_selector(S.CARD_LINK)
    href = await link_el.get_attribute("href") if link_el else None
    listing_url = f"{BDS_BASE_URL}{href}" if href and href.startswith("/") else href

    bds_id = None
    if href:
        m = _PR_ID_PATTERN.search(href)
        if m:
            bds_id = m.group(1)

    price_el = await card.query_selector(S.CARD_PRICE)
    price_raw = await price_el.inner_text() if price_el else None

    area_el = await card.query_selector(S.CARD_AREA)
    area_raw = await area_el.inner_text() if area_el else None
    if area_raw:
        area_raw = area_raw.lstrip("·").strip()

    bed_el = await card.query_selector(S.CARD_BEDROOMS)
    bed_raw = await bed_el.inner_text() if bed_el else None

    bath_el = await card.query_selector(S.CARD_BATHROOMS)
    bath_raw = await bath_el.inner_text() if bath_el else None

    location_el = await card.query_selector(S.CARD_LOCATION)
    location_text = await location_el.inner_text() if location_el else ""
    district_name, city_name = _parse_location(location_text)

    price_vnd = parse_price_vnd(price_raw) if price_raw else None
    area_sqm = parse_area_sqm(area_raw) if area_raw else None
    price_per_sqm = parse_price_per_sqm(price_raw) if price_raw else None
    if price_vnd and area_sqm and not price_per_sqm:
        price_per_sqm = price_vnd / area_sqm

    return {
        "bds_listing_id": bds_id,
        "project_name": name,
        "district_name": district_name,
        "city_name": city_name,
        "price_raw": price_raw,
        "price_vnd": price_vnd,
        "price_per_sqm": price_per_sqm,
        "area_sqm": area_sqm,
        "bedrooms": int(bed_raw) if bed_raw and bed_raw.strip().isdigit() else None,
        "bathrooms": int(bath_raw) if bath_raw and bath_raw.strip().isdigit() else None,
        "listing_url": listing_url,
    }


async def scrape_single_city(city_key: str, max_pages: int = 3):
    """Scrape one city with a dedicated fresh browser instance."""
    city_slug = CITY_SLUGS[city_key]
    base_url = f"{BDS_BASE_URL}/ban-can-ho-chung-cu-{city_slug}"
    all_items = []

    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )

        ua = random.choice(USER_AGENTS)
        width = 1366 + random.randint(-100, 100)
        height = 768 + random.randint(-50, 50)

        context = await browser.new_context(
            viewport={"width": width, "height": height},
            user_agent=ua,
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
        )
        context.set_default_timeout(30000)
        context.set_default_navigation_timeout(60000)

        page = await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        for page_num in range(1, max_pages + 1):
            url = base_url if page_num == 1 else f"{base_url}/p{page_num}"
            logger.info("[%s] Page %d: %s", city_key.upper(), page_num, url)

            # Human-like delay before navigation
            await asyncio.sleep(random.uniform(6, 10))

            try:
                response = await page.goto(url, wait_until="domcontentloaded")
                status = response.status if response else 0

                if status == 403:
                    logger.warning("[%s] 403 blocked on page %d — stopping", city_key.upper(), page_num)
                    break
                if status != 200:
                    logger.warning("[%s] Status %s on page %d", city_key.upper(), status, page_num)
                    continue

                # Wait for content + simulate scrolling
                await page.wait_for_timeout(2000)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                await page.wait_for_timeout(1000)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await page.wait_for_timeout(1000)

                cards = await page.query_selector_all(S.CARD)
                logger.info("[%s] Found %d cards", city_key.upper(), len(cards))

                page_items = []
                for card in cards:
                    try:
                        item = await _parse_card(card)
                        if item:
                            page_items.append(item)
                    except Exception as e:
                        logger.debug("Card error: %s", e)

                all_items.extend(page_items)
                logger.info("[%s] Page %d: %d items (total %d)",
                           city_key.upper(), page_num, len(page_items), len(all_items))

                if not cards:
                    break

            except Exception as e:
                logger.error("[%s] Error: %s", city_key.upper(), e)
                break

        await context.close()
        await browser.close()
    finally:
        await pw.stop()

    return all_items


async def main():
    cities = ["hcmc", "hanoi", "binh_duong"]
    max_pages = 3

    print("=" * 80)
    print("  BatDongSan.com.vn — Full Data Collection")
    print(f"  Cities: {', '.join(c.upper() for c in cities)}")
    print(f"  Pages per city: up to {max_pages}")
    print(f"  Strategy: fresh browser per city, human-like delays")
    print("=" * 80)

    session = get_session()
    pipeline = ScrapePipeline(session)
    grand_found = 0
    grand_saved = 0

    for city_key in cities:
        city_slug = CITY_SLUGS[city_key]
        print(f"\n{'─' * 60}")
        print(f"  {city_key.upper()} ({city_slug})")
        print(f"{'─' * 60}")

        job = pipeline.create_job(
            job_type="project_list",
            target_url=f"{BDS_BASE_URL}/ban-can-ho-chung-cu-{city_slug}",
        )
        session.commit()

        try:
            items = await scrape_single_city(city_key, max_pages)
            grand_found += len(items)

            if items:
                valid, saved = pipeline.process_listings(items, job)
                pipeline.complete_job(job, len(items), saved)
                session.commit()
                grand_saved += saved
                print(f"  => {len(items)} found | {valid} valid | {saved} new saved to DB")
            else:
                pipeline.complete_job(job, 0, 0, "No items scraped")
                session.commit()
                print(f"  => No items scraped")

        except Exception as e:
            pipeline.complete_job(job, 0, 0, str(e))
            session.commit()
            print(f"  => Error: {e}")

        # Long pause between cities (fresh browser each time anyway)
        if city_key != cities[-1]:
            wait = random.uniform(15, 25)
            print(f"  Cooling down {wait:.0f}s before next city...")
            await asyncio.sleep(wait)

    # Summary
    print(f"\n{'=' * 80}")
    print("  COLLECTION SUMMARY")
    print(f"{'=' * 80}")

    total = session.query(ScrapedListing).count()
    matched = session.query(ScrapedListing).filter(
        ScrapedListing.matched_project_id.isnot(None)
    ).count()
    unmatched = total - matched

    print(f"  This run:  {grand_found} found, {grand_saved} new")
    print(f"  Total DB:  {total} listings")
    print(f"  Matched:   {matched} ({matched/total*100:.0f}%)" if total else "  Matched:   0")
    print(f"  Unmatched: {unmatched}")

    # Price summary by city
    print(f"\n  Price by city:")
    from sqlalchemy import func
    for city_name_like in ["Ho Chi Minh", "Ha Noi", "Binh Duong"]:
        stats = session.query(
            func.count(ScrapedListing.id),
            func.avg(ScrapedListing.price_vnd),
            func.min(ScrapedListing.price_vnd),
            func.max(ScrapedListing.price_vnd),
        ).filter(
            ScrapedListing.city_name.like(f"%{city_name_like}%"),
            ScrapedListing.price_vnd.isnot(None),
        ).first()

        if stats[0] > 0:
            print(f"    {city_name_like}: {stats[0]} listings, "
                  f"avg {stats[1]/1e9:.1f} ty, "
                  f"range {stats[2]/1e9:.1f}-{stats[3]/1e9:.1f} ty")

    # Jobs summary
    print(f"\n  Recent jobs:")
    jobs = session.query(ScrapeJob).order_by(ScrapeJob.id.desc()).limit(10).all()
    for j in jobs:
        dur = ""
        if j.started_at and j.completed_at:
            dur = f" ({(j.completed_at - j.started_at).total_seconds():.0f}s)"
        status_icon = "OK" if j.status == "completed" else "FAIL"
        print(f"    #{j.id} [{status_icon}] {j.job_type} found={j.items_found} saved={j.items_saved}{dur}")

    session.close()
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(main())
