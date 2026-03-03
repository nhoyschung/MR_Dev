"""Scrape office lease listings from batdongsan.com.vn/cho-thue-van-phong."""

import logging
import re
from typing import Any, Optional

from playwright.async_api import Page

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.browser import BrowserManager
from src.scrapers.config import BDS_BASE_URL, BDS_OFFICE_LEASE_URL, CITY_SLUGS, MAX_PAGES_PER_SCRAPE
from src.scrapers.parsers import (
    clean_project_name,
    parse_area_sqm,
    parse_office_floor,
    parse_rent_usd_per_m2_month,
    parse_rent_vnd_per_m2_month,
)
from src.scrapers.rate_limiter import RateLimiter
from src.scrapers.selectors import OfficeListingSelectors as OS

logger = logging.getLogger(__name__)

_LISTING_ID_PATTERN = re.compile(r"pr(\d+)")


class OfficeScraper(BaseScraper):
    """Scrape office lease listings from batdongsan.com.vn.

    Targets: /cho-thue-van-phong-{city_slug}
    Produces: list of dicts matching ScrapedOfficeListingData fields.
    """

    def __init__(
        self,
        browser: BrowserManager,
        rate_limiter: RateLimiter,
        city: str = "hcmc",
        max_pages: int = MAX_PAGES_PER_SCRAPE,
    ) -> None:
        super().__init__(browser, rate_limiter)
        self.city = city
        self.city_slug = CITY_SLUGS.get(city, "tp-hcm")
        self.max_pages = max_pages
        self.start_url = BDS_OFFICE_LEASE_URL.format(city_slug=self.city_slug)

    async def parse_page(self, page: Page, url: str) -> list[dict[str, Any]]:
        """Extract office listing data from a search results page."""
        results: list[dict[str, Any]] = []
        cards = await page.query_selector_all(OS.CARD)

        for card in cards:
            try:
                item = await self._parse_card(card)
                if item:
                    results.append(item)
            except Exception as e:
                logger.warning("Error parsing office card: %s", e)

        return results

    async def _parse_card(self, card) -> Optional[dict[str, Any]]:
        """Parse a single office listing card."""
        title_el = await card.query_selector(OS.CARD_TITLE)
        if not title_el:
            return None

        raw_name = await title_el.inner_text()
        building_name = self._clean_office_name(raw_name)
        if not building_name:
            return None

        link_el = await card.query_selector(OS.CARD_LINK)
        href = await link_el.get_attribute("href") if link_el else None
        listing_url = (
            f"{BDS_BASE_URL}{href}" if href and href.startswith("/") else href
        )

        listing_id = None
        if href:
            m = _LISTING_ID_PATTERN.search(href)
            if m:
                listing_id = f"office_{m.group(1)}"

        price_el = await card.query_selector(OS.CARD_PRICE)
        rent_raw = await price_el.inner_text() if price_el else None

        area_el = await card.query_selector(OS.CARD_AREA)
        area_raw = await area_el.inner_text() if area_el else None
        if area_raw:
            area_raw = area_raw.lstrip("·").strip()

        location_el = await card.query_selector(OS.CARD_LOCATION)
        location_text = await location_el.inner_text() if location_el else ""
        location_text = location_text.lstrip("·•\n\r\t ").strip()
        parts = [p.strip() for p in location_text.split(",") if p.strip()]
        district = parts[-2] if len(parts) >= 2 else None
        city = parts[-1] if len(parts) >= 1 else None

        area_m2 = parse_area_sqm(area_raw) if area_raw else None
        rent_vnd = parse_rent_vnd_per_m2_month(rent_raw, area_m2) if rent_raw else None
        rent_usd = parse_rent_usd_per_m2_month(rent_raw) if rent_raw else None

        return {
            "listing_id": listing_id,
            "building_name": building_name,
            "address": None,
            "district_name": district,
            "city_name": city,
            "rent_raw": rent_raw,
            "rent_vnd_per_m2_month": rent_vnd,
            "rent_usd_per_m2_month": rent_usd,
            "area_m2": area_m2,
            "floor": None,
            "listing_url": listing_url,
        }

    def _clean_office_name(self, raw: str) -> Optional[str]:
        """Clean office building name by removing Vietnamese prefix words."""
        if not raw:
            return None
        name = raw.strip()
        # Remove common office listing title prefixes
        prefixes = re.compile(
            r"^(?:Cho\s+thuê\s+văn\s+phòng|Văn\s+phòng|VP|Cho\s+thuê)\s+",
            re.IGNORECASE,
        )
        name = prefixes.sub("", name).strip()
        return name if len(name) >= 3 else None

    async def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Run the full office listing scrape."""
        all_results: list[dict[str, Any]] = []
        url = self.start_url
        pages_scraped = 0
        seen_urls: set[str] = set()

        logger.info("Office scrape start: %s", url)

        while url and pages_scraped < self.max_pages:
            if url in seen_urls:
                break
            seen_urls.add(url)

            page = await self.fetch_page(url)
            if not page:
                break

            try:
                await page.wait_for_timeout(2000)
                results = await self.parse_page(page, url)
                all_results.extend(results)
                pages_scraped += 1
                logger.info(
                    "Office listings page %d: %d items", pages_scraped, len(results)
                )

                # Pagination: last pagination icon = next page
                next_btns = await page.query_selector_all(OS.PAGINATION_NEXT)
                if next_btns:
                    href = await next_btns[-1].get_attribute("href")
                    url = (
                        f"{BDS_BASE_URL}{href}"
                        if href and href.startswith("/")
                        else href
                    )
                else:
                    url = None
            finally:
                await page.close()

        logger.info("Office scrape complete: %d total items", len(all_results))
        return all_results
