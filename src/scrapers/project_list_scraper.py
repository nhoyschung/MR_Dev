"""Scrape project/listing cards from batdongsan.com.vn search pages."""

import logging
import re
from typing import Any, Optional

from playwright.async_api import Page

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.browser import BrowserManager
from src.scrapers.config import (
    BDS_BASE_URL,
    BDS_PROJECT_LIST_URL,
    CITY_SLUGS,
    MAX_PAGES_PER_SCRAPE,
)
from src.scrapers.parsers import (
    clean_project_name,
    extract_slug_from_url,
    parse_area_sqm,
    parse_price_per_sqm,
    parse_price_vnd,
)
from src.scrapers.rate_limiter import RateLimiter
from src.scrapers.selectors import ProjectListSelectors as S

logger = logging.getLogger(__name__)

# Extract listing ID from URL pattern like "pr43432712"
_PR_ID_PATTERN = re.compile(r"pr(\d+)")


class ProjectListScraper(BaseScraper):
    """Scrape project listing cards from BDS search result pages.

    Handles pagination and extracts basic project info from each card.
    """

    def __init__(
        self,
        browser: BrowserManager,
        rate_limiter: RateLimiter,
        city: str = "hcmc",
        district_slug: Optional[str] = None,
        max_pages: int = MAX_PAGES_PER_SCRAPE,
    ) -> None:
        super().__init__(browser, rate_limiter)
        self.city = city
        self.district_slug = district_slug
        self.max_pages = max_pages

    def _build_start_url(self) -> str:
        """Build the starting URL for the scrape."""
        city_slug = CITY_SLUGS.get(self.city, self.city)
        if self.district_slug:
            return f"{BDS_BASE_URL}/ban-can-ho-chung-cu-{self.district_slug}"
        return BDS_PROJECT_LIST_URL.format(city_slug=city_slug)

    async def parse_page(self, page: Page, url: str) -> list[dict[str, Any]]:
        """Extract listing cards from a single search results page."""
        results: list[dict[str, Any]] = []

        cards = await page.query_selector_all(S.CARD)
        logger.info("Found %d cards on %s", len(cards), url)

        for card in cards:
            try:
                item = await self._parse_card(card)
                if item:
                    results.append(item)
            except Exception as e:
                logger.warning("Error parsing card on %s: %s", url, e)

        return results

    async def _parse_card(self, card) -> Optional[dict[str, Any]]:
        """Extract data from a single listing card element."""
        # Title / project name (span.js__card-title for premium, h3 for regular)
        title_el = await card.query_selector(S.CARD_TITLE)
        if not title_el:
            return None
        raw_name = await title_el.inner_text()
        name = clean_project_name(raw_name)
        if not name:
            return None

        # Listing URL from the wrapping <a> link
        link_el = await card.query_selector(S.CARD_LINK)
        href = await link_el.get_attribute("href") if link_el else None
        listing_url = f"{BDS_BASE_URL}{href}" if href and href.startswith("/") else href

        # Extract listing ID from URL pattern (pr12345678)
        bds_id = None
        if href:
            m = _PR_ID_PATTERN.search(href)
            if m:
                bds_id = m.group(1)

        # Price
        price_el = await card.query_selector(S.CARD_PRICE)
        price_raw = await price_el.inner_text() if price_el else None
        price_vnd = parse_price_vnd(price_raw) if price_raw else None
        price_per_sqm = parse_price_per_sqm(price_raw) if price_raw else None

        # Area (may have leading "·" character)
        area_el = await card.query_selector(S.CARD_AREA)
        area_raw = await area_el.inner_text() if area_el else None
        if area_raw:
            area_raw = area_raw.lstrip("·").strip()
        area_sqm = parse_area_sqm(area_raw) if area_raw else None

        # Calculate price per sqm if we have total price and area
        if price_vnd and area_sqm and not price_per_sqm:
            price_per_sqm = price_vnd / area_sqm

        # Location (format: "· Ward, District, City" or "· District, City")
        location_el = await card.query_selector(S.CARD_LOCATION)
        location_text = await location_el.inner_text() if location_el else ""
        district_name, city_name = self._parse_location(location_text)

        # Bedrooms
        bed_el = await card.query_selector(S.CARD_BEDROOMS)
        bedrooms_raw = await bed_el.inner_text() if bed_el else None
        bedrooms = int(bedrooms_raw) if bedrooms_raw and bedrooms_raw.strip().isdigit() else None

        # Bathrooms
        bath_el = await card.query_selector(S.CARD_BATHROOMS)
        bath_raw = await bath_el.inner_text() if bath_el else None
        bathrooms = int(bath_raw) if bath_raw and bath_raw.strip().isdigit() else None

        return {
            "bds_listing_id": bds_id,
            "project_name": name,
            "district_name": district_name,
            "city_name": city_name,
            "price_raw": price_raw,
            "price_vnd": price_vnd,
            "price_per_sqm": price_per_sqm,
            "area_sqm": area_sqm,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "listing_url": listing_url,
            "slug": extract_slug_from_url(listing_url),
        }

    @staticmethod
    def _parse_location(text: str) -> tuple[Optional[str], Optional[str]]:
        """Parse location text like '· Quận 9, Hồ Chí Minh' into (district, city)."""
        if not text:
            return None, None
        # Strip leading dots, bullets, whitespace
        text = text.lstrip("·•\n\r\t ").strip()
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        if len(parts) == 1:
            return parts[0], None
        return None, None

    async def _has_next_page(self, page: Page) -> Optional[str]:
        """Check for a next page link. Returns the URL or None."""
        try:
            # The last a.re__pagination-icon is the "next" button
            next_btns = await page.query_selector_all(S.PAGINATION_NEXT)
            if next_btns:
                last_btn = next_btns[-1]
                href = await last_btn.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        return f"{BDS_BASE_URL}{href}"
                    return href
        except Exception:
            pass
        return None

    async def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Scrape all pages of project listings for the configured city/district."""
        all_results: list[dict[str, Any]] = []
        url = self._build_start_url()
        pages_scraped = 0
        seen_urls: set[str] = set()

        while url and pages_scraped < self.max_pages:
            # Prevent infinite loops
            if url in seen_urls:
                break
            seen_urls.add(url)

            page = await self.fetch_page(url)
            if not page:
                break

            try:
                # Wait for cards to render
                await page.wait_for_timeout(2000)
                results = await self.parse_page(page, url)
                all_results.extend(results)
                pages_scraped += 1

                logger.info(
                    "Page %d: %d items (total: %d)",
                    pages_scraped, len(results), len(all_results),
                )

                # Check for next page
                next_url = await self._has_next_page(page)
                url = next_url
            finally:
                await page.close()

        logger.info(
            "Scrape complete: %d pages, %d items, %d errors",
            pages_scraped, len(all_results), len(self.errors),
        )
        return all_results
