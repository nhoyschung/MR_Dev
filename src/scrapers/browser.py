"""Playwright browser manager with anti-detection measures."""

import random
from types import TracebackType
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.scrapers.config import (
    DEFAULT_VIEWPORT_HEIGHT,
    DEFAULT_VIEWPORT_WIDTH,
    NAVIGATION_TIMEOUT_MS,
    PAGE_TIMEOUT_MS,
    USER_AGENTS,
    VIEWPORT_JITTER,
)


class BrowserManager:
    """Async context manager for Playwright browser with anti-detection.

    Usage:
        async with BrowserManager() as manager:
            page = await manager.new_page()
            await page.goto("https://example.com")
    """

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self) -> "BrowserManager":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        self._context = await self._create_context()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _create_context(self) -> BrowserContext:
        """Create a browser context with randomized fingerprint."""
        width = DEFAULT_VIEWPORT_WIDTH + random.randint(-VIEWPORT_JITTER, VIEWPORT_JITTER)
        height = DEFAULT_VIEWPORT_HEIGHT + random.randint(-VIEWPORT_JITTER, VIEWPORT_JITTER)
        user_agent = random.choice(USER_AGENTS)

        context = await self._browser.new_context(
            viewport={"width": width, "height": height},
            user_agent=user_agent,
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
        )
        context.set_default_timeout(PAGE_TIMEOUT_MS)
        context.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        return context

    async def new_page(self) -> Page:
        """Create a new page with anti-detection script injected."""
        page = await self._context.new_page()

        # Remove webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        return page

    async def close(self) -> None:
        """Manually close the browser (for non-context-manager use)."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
