import logging
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

NAVIGATION_TIMEOUT_MS = 15000
ACTION_TIMEOUT_MS = 10000


class BrowserAgent:
    """
    Manages a single headless Chromium instance shared across scraper calls.
    Each scraper gets its own BrowserContext (isolated cookies/storage).
    """

    def __init__(self, headless: bool = True):
        self._headless = headless
        self._playwright = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        logger.info(f"Browser launched (headless={self._headless})")

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    @asynccontextmanager
    async def new_context(self, **kwargs):
        """Yield an isolated BrowserContext. Auto-closes on exit."""
        ctx = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            **kwargs,
        )
        ctx.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        ctx.set_default_timeout(ACTION_TIMEOUT_MS)

        # Block heavy resources to speed up page loads
        await ctx.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}",
            lambda route: route.abort(),
        )
        try:
            yield ctx
        finally:
            await ctx.close()

    @asynccontextmanager
    async def new_page(self, **ctx_kwargs):
        """Convenience: yield a Page inside a fresh context."""
        async with self.new_context(**ctx_kwargs) as ctx:
            page = await ctx.new_page()
            yield page


@asynccontextmanager
async def managed_browser(headless: bool = True):
    """Top-level context manager for the entire browser lifecycle."""
    agent = BrowserAgent(headless=headless)
    await agent.start()
    try:
        yield agent
    finally:
        await agent.stop()
