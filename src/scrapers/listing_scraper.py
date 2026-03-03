"""Scrape individual unit listings with prices from batdongsan.com.vn."""

import logging
import re
from typing import Any, Optional

from playwright.async_api import Page

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.browser import BrowserManager
from src.scrapers.config import BDS_BASE_URL, MAX_PAGES_PER_SCRAPE
from src.scrapers.parsers import (
    clean_project_name,
    parse_area_sqm,
    parse_int_from_text,
    parse_price_per_sqm,
    parse_price_vnd,
)
from src.scrapers.rate_limiter import RateLimiter
from src.scrapers.selectors import ListingDetailSelectors as LS
from src.scrapers.selectors import ProjectListSelectors as PS

logger = logging.getLogger(__name__)

_PR_ID_PATTERN = re.compile(r"pr(\d+)")


class ListingScraper(BaseScraper):
    """Scrape unit listings from BDS search results and detail pages.

    Can operate in two modes:
    1. Search mode: Scrape listings from search pages for a project/district
    2. Detail mode: Scrape individual listing pages for full specs
    """

    def __init__(
        self,
        browser: BrowserManager,
        rate_limiter: RateLimiter,
        search_url: Optional[str] = None,
        listing_urls: list[str] | None = None,
        max_pages: int = MAX_PAGES_PER_SCRAPE,
    ) -> None:
        super().__init__(browser, rate_limiter)
        self.search_url = search_url
        self.listing_urls = listing_urls or []
        self.max_pages = max_pages

    async def parse_page(self, page: Page, url: str) -> list[dict[str, Any]]:
        """Extract listing data from a page (search results or detail)."""
        # Detect page type based on URL structure
        if "/ban-" in url or "/cho-thue-" in url:
            return await self._parse_search_page(page, url)
        return await self._parse_detail_page(page, url)

    async def _parse_search_page(self, page: Page, url: str) -> list[dict[str, Any]]:
        """Extract listings from a search results page."""
        results: list[dict[str, Any]] = []
        cards = await page.query_selector_all(PS.CARD)

        for card in cards:
            try:
                item = await self._parse_search_card(card)
                if item:
                    results.append(item)
            except Exception as e:
                logger.warning("Error parsing listing card: %s", e)

        return results

    async def _parse_search_card(self, card) -> Optional[dict[str, Any]]:
        """Parse a single listing card from search results."""
        title_el = await card.query_selector(PS.CARD_TITLE)
        if not title_el:
            return None

        raw_name = await title_el.inner_text()
        name = clean_project_name(raw_name)

        link_el = await card.query_selector(PS.CARD_LINK)
        href = await link_el.get_attribute("href") if link_el else None
        listing_url = f"{BDS_BASE_URL}{href}" if href and href.startswith("/") else href

        # Extract listing ID from URL
        bds_id = None
        if href:
            m = _PR_ID_PATTERN.search(href)
            if m:
                bds_id = m.group(1)

        price_el = await card.query_selector(PS.CARD_PRICE)
        price_raw = await price_el.inner_text() if price_el else None

        area_el = await card.query_selector(PS.CARD_AREA)
        area_raw = await area_el.inner_text() if area_el else None
        if area_raw:
            area_raw = area_raw.lstrip("·").strip()

        bed_el = await card.query_selector(PS.CARD_BEDROOMS)
        bed_raw = await bed_el.inner_text() if bed_el else None

        bath_el = await card.query_selector(PS.CARD_BATHROOMS)
        bath_raw = await bath_el.inner_text() if bath_el else None

        location_el = await card.query_selector(PS.CARD_LOCATION)
        location_text = await location_el.inner_text() if location_el else ""
        location_text = location_text.lstrip("·•\n\r\t ").strip()
        parts = [p.strip() for p in location_text.split(",") if p.strip()]
        district = parts[-2] if len(parts) >= 2 else None
        city = parts[-1] if len(parts) >= 2 else None

        price_vnd = parse_price_vnd(price_raw) if price_raw else None
        area_sqm = parse_area_sqm(area_raw) if area_raw else None
        price_per_sqm = parse_price_per_sqm(price_raw) if price_raw else None
        if price_vnd and area_sqm and not price_per_sqm:
            price_per_sqm = price_vnd / area_sqm

        return {
            "bds_listing_id": bds_id,
            "project_name": name,
            "district_name": district,
            "city_name": city,
            "price_raw": price_raw,
            "price_vnd": price_vnd,
            "price_per_sqm": price_per_sqm,
            "area_sqm": area_sqm,
            "bedrooms": parse_int_from_text(bed_raw) if bed_raw else None,
            "bathrooms": parse_int_from_text(bath_raw) if bath_raw else None,
            "listing_url": listing_url,
        }

    async def _parse_detail_page(self, page: Page, url: str) -> list[dict[str, Any]]:
        """Parse a single listing detail page for full specs."""
        result: dict[str, Any] = {"listing_url": url}

        title_el = await page.query_selector(LS.TITLE)
        if title_el:
            result["project_name"] = clean_project_name(await title_el.inner_text())

        price_el = await page.query_selector(LS.PRICE)
        if price_el:
            price_raw = await price_el.inner_text()
            result["price_raw"] = price_raw
            result["price_vnd"] = parse_price_vnd(price_raw)

        area_el = await page.query_selector(LS.AREA)
        if area_el:
            result["area_sqm"] = parse_area_sqm(await area_el.inner_text())

        # Parse specs table
        spec_items = await page.query_selector_all(LS.SPEC_TABLE)
        for item in spec_items:
            text = (await item.inner_text()).strip()
            if "Hướng" in text:
                result["direction"] = text.split(":")[-1].strip() if ":" in text else text.replace("Hướng", "").strip()
            elif "phòng ngủ" in text.lower():
                result["bedrooms"] = parse_int_from_text(text)
            elif "toilet" in text.lower() or "phòng tắm" in text.lower():
                result["bathrooms"] = parse_int_from_text(text)
            elif "tầng" in text.lower():
                result["floor"] = text.split(":")[-1].strip() if ":" in text else None

        # Price per sqm
        if result.get("price_vnd") and result.get("area_sqm"):
            result["price_per_sqm"] = result["price_vnd"] / result["area_sqm"]

        return [result] if result.get("project_name") else []

    async def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Run the full listing scrape."""
        all_results: list[dict[str, Any]] = []

        # Mode 1: Search pages
        if self.search_url:
            url = self.search_url
            pages_scraped = 0
            seen_urls: set[str] = set()

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
                        "Listings page %d: %d items", pages_scraped, len(results)
                    )
                    # Check next page (last pagination icon)
                    next_btns = await page.query_selector_all(PS.PAGINATION_NEXT)
                    if next_btns:
                        href = await next_btns[-1].get_attribute("href")
                        url = f"{BDS_BASE_URL}{href}" if href and href.startswith("/") else href
                    else:
                        url = None
                finally:
                    await page.close()

        # Mode 2: Individual listing URLs
        for listing_url in self.listing_urls:
            page = await self.fetch_page(listing_url)
            if not page:
                continue
            try:
                await page.wait_for_timeout(2000)
                results = await self.parse_page(page, listing_url)
                all_results.extend(results)
            finally:
                await page.close()

        logger.info("Listing scrape complete: %d items", len(all_results))
        return all_results
