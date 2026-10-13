"""Firecrawl Engine Integration - Turns URLs into clean structured Markdown for LLMs.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse

from alpha_lead_engine.auditor.schemas import RawLead

logger = logging.getLogger("alpha_lead_engine.crawlers.firecrawl")
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


class FirecrawlEngine:
    """Wrapper around Firecrawl SDK (`firecrawl-py`) for high-fidelity markdown synthesis."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from firecrawl import FirecrawlApp
                self.client = FirecrawlApp(api_key=self.api_key)
            except ImportError:
                logger.warning("firecrawl-py is not installed. Run `pip install firecrawl-py` to enable.")

    @property
    def is_available(self) -> bool:
        return bool(self.client and self.api_key)

    def scrape_url(self, url: str, business_name: str = "") -> Optional[RawLead]:
        """Scrapes URL via Firecrawl and parses structured markdown."""
        if not self.is_available:
            logger.info("Firecrawl API key not set or client unavailable. Skipping Firecrawl engine.")
            return None

        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            logger.info(f"Scraping {url} with Firecrawl...")
            result = self.client.scrape_url(url, params={"formats": ["markdown"]})
            markdown_content = result.get("markdown", "")
            metadata = result.get("metadata", {})

            # Extract emails from markdown
            emails = EMAIL_REGEX.findall(markdown_content)
            clean_emails = [e for e in set(emails) if not any(e.endswith(ext) for ext in [".png", ".jpg", ".svg"])]

            b_name = business_name or metadata.get("title") or urlparse(url).netloc
            b_name = b_name.split("-")[0].split("|")[0].strip()

            return RawLead(
                business_name=b_name,
                website=url,
                email=clean_emails[0] if clean_emails else None,
                source_engine="firecrawl",
                scraped_text=markdown_content[:8000],
                metadata={"firecrawl_metadata": metadata, "all_emails": clean_emails}
            )
        except Exception as e:
            logger.warning(f"Firecrawl scrape failed for {url}: {e}")
            return None
