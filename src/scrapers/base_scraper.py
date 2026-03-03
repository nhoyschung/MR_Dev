"""Abstract base scraper with retry logic and error handling."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.scrapers.browser import BrowserManager
from src.scrapers.config import MAX_RETRIES, RETRY_BACKOFF_BASE
from src.scrapers.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract scraper with retry, rate limiting, and error capture.

    Subclasses implement `parse_page()` to extract data from a loaded page.
    """

    def __init__(
        self,
        browser: BrowserManager,
        rate_limiter: RateLimiter,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.browser = browser
        self.rate_limiter = rate_limiter
        self.max_retries = max_retries
        self.errors: list[dict[str, Any]] = []

    async def fetch_page(self, url: str) -> Optional[Page]:
        """Navigate to a URL with rate limiting and retry logic.

        Returns the loaded Page on success, or None after all retries fail.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                await self.rate_limiter.acquire()
                page = await self.browser.new_page()
                response = await page.goto(url, wait_until="domcontentloaded")

                if response and response.status == 200:
                    return page

                status = response.status if response else "no response"
                logger.warning(
                    "Non-200 status %s for %s (attempt %d/%d)",
                    status, url, attempt, self.max_retries,
                )
                await page.close()

            except PlaywrightTimeout:
                logger.warning(
                    "Timeout for %s (attempt %d/%d)",
                    url, attempt, self.max_retries,
                )
            except Exception as e:
                logger.error(
                    "Error fetching %s (attempt %d/%d): %s",
                    url, attempt, self.max_retries, e,
                )

            if attempt < self.max_retries:
                backoff = RETRY_BACKOFF_BASE ** attempt
                await asyncio.sleep(backoff)

        self._record_error(url, "Max retries exceeded")
        return None

    @abstractmethod
    async def parse_page(self, page: Page, url: str) -> list[dict[str, Any]]:
        """Extract structured data from a loaded page.

        Returns a list of parsed data dictionaries.
        """
        ...

    @abstractmethod
    async def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Run the full scrape workflow. Subclasses define targets and orchestration."""
        ...

    def _record_error(self, url: str, message: str) -> None:
        """Record an error for later reporting."""
        self.errors.append({
            "url": url,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_error_summary(self) -> str:
        """Return a summary of all errors encountered."""
        if not self.errors:
            return "No errors"
        lines = [f"  {e['url']}: {e['message']}" for e in self.errors]
        return f"{len(self.errors)} error(s):\n" + "\n".join(lines)
