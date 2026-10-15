"""Crawl4AI Engine - High-speed local async crawler for LLMs without external API keys.
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from alpha_lead_engine.auditor.schemas import RawLead

logger = logging.getLogger("alpha_lead_engine.crawlers.crawl4ai")
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


class Crawl4AIEngine:
    """Async fast crawler utilizing crawl4ai if installed, otherwise clean HTML fallback."""

    def __init__(self):
        self._has_crawl4ai = False
        try:
            import crawl4ai
            self._has_crawl4ai = True
        except ImportError:
            self._has_crawl4ai = False

    @property
    def is_available(self) -> bool:
        return self._has_crawl4ai

    async def crawl(self, url: str, business_name: str = "") -> Optional[RawLead]:
        """Crawl URL asynchronously using crawl4ai."""
        if not url.startswith("http"):
            url = f"https://{url}"

        if not self._has_crawl4ai:
            logger.info("crawl4ai not installed. Skipping crawl4ai engine.")
            return None

        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler(verbose=False) as crawler:
                res = await crawler.arun(url=url)
                if not res.success:
                    logger.warning(f"crawl4ai failed for {url}")
                    return None

                md = res.markdown or res.cleaned_html or ""
                emails = EMAIL_REGEX.findall(md)
                clean_emails = [e for e in set(emails) if not any(e.endswith(ext) for ext in [".png", ".jpg", ".svg"])]

                b_name = business_name or urlparse(url).netloc

                return RawLead(
                    business_name=b_name,
                    website=url,
                    email=clean_emails[0] if clean_emails else None,
                    source_engine="crawl4ai",
                    scraped_text=md[:8000],
                    metadata={"all_emails": clean_emails}
                )
        except Exception as e:
            logger.warning(f"Error during crawl4ai execution for {url}: {e}")
            return None
