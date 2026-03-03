"""Scrape individual project detail pages from batdongsan.com.vn."""

import logging
from typing import Any, Optional

from playwright.async_api import Page

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.browser import BrowserManager
from src.scrapers.config import BDS_PROJECT_DETAIL_URL
from src.scrapers.parsers import clean_project_name, parse_int_from_text
from src.scrapers.rate_limiter import RateLimiter
from src.scrapers.selectors import ProjectDetailSelectors as S

logger = logging.getLogger(__name__)


class ProjectDetailScraper(BaseScraper):
    """Scrape detailed project information from individual project pages."""

    def __init__(
        self,
        browser: BrowserManager,
        rate_limiter: RateLimiter,
        project_slugs: list[str] | None = None,
    ) -> None:
        super().__init__(browser, rate_limiter)
        self.project_slugs = project_slugs or []

    async def parse_page(self, page: Page, url: str) -> list[dict[str, Any]]:
        """Extract project details from a project detail page."""
        result: dict[str, Any] = {"url": url}

        # Title
        title_el = await page.query_selector(S.TITLE)
        if title_el:
            raw = await title_el.inner_text()
            result["name"] = clean_project_name(raw)

        # Address
        addr_el = await page.query_selector(S.ADDRESS)
        if addr_el:
            result["address"] = (await addr_el.inner_text()).strip()

        # Short info items (developer, price, units, completion, type, status)
        result.update(await self._parse_short_info(page))

        # Amenities
        amenity_els = await page.query_selector_all(S.AMENITIES)
        amenities = []
        for el in amenity_els:
            text = (await el.inner_text()).strip()
            if text:
                amenities.append(text)
        if amenities:
            result["amenities"] = amenities

        return [result]

    async def _parse_short_info(self, page: Page) -> dict[str, Any]:
        """Parse the short info panel (developer, price range, units, etc.)."""
        info: dict[str, Any] = {}

        # Each info item has a label and value; use text-based selectors
        items = await page.query_selector_all("div.re__pr-short-info-item")
        for item in items:
            text = (await item.inner_text()).strip()

            if "Chủ đầu tư" in text:
                info["developer_name"] = text.replace("Chủ đầu tư", "").strip().strip(":")
            elif "Mức giá" in text:
                info["price_range_raw"] = text.replace("Mức giá", "").strip().strip(":")
            elif "Số căn hộ" in text or "Quy mô" in text:
                val = parse_int_from_text(text)
                if val:
                    info["total_units"] = val
            elif "Năm bàn giao" in text or "bàn giao" in text.lower():
                info["completion_date"] = text.split(":")[-1].strip() if ":" in text else text.replace("Năm bàn giao", "").strip()
            elif "Loại hình" in text:
                info["project_type"] = text.replace("Loại hình", "").strip().strip(":")
            elif "Tình trạng" in text:
                info["status"] = text.replace("Tình trạng", "").strip().strip(":")

        return info

    async def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Scrape details for all configured project slugs."""
        all_results: list[dict[str, Any]] = []

        for slug in self.project_slugs:
            url = BDS_PROJECT_DETAIL_URL.format(project_slug=slug)
            page = await self.fetch_page(url)
            if not page:
                continue

            try:
                results = await self.parse_page(page, url)
                for r in results:
                    r["slug"] = slug
                all_results.extend(results)
                logger.info("Scraped project detail: %s", slug)
            finally:
                await page.close()

        return all_results
