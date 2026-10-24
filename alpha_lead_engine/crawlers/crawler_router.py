"""Crawler Router & Orchestrator - Unifies multi-engine crawling with automated fallback and deduplication.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional
from urllib.parse import urlparse

from alpha_lead_engine.auditor.schemas import RawLead
from alpha_lead_engine.crawlers.apify_connector import ApifyConnector
from alpha_lead_engine.crawlers.crawl4ai_engine import Crawl4AIEngine
from alpha_lead_engine.crawlers.firecrawl_engine import FirecrawlEngine
from alpha_lead_engine.crawlers.maps_scraper import GoogleMapsScraper
from alpha_lead_engine.crawlers.playwright_engine import PlaywrightCrawlerEngine

logger = logging.getLogger("alpha_lead_engine.crawlers.router")


class CrawlerRouter:
    """Intelligent multi-crawler discovery orchestrator.
    Deduplicates results by root domain and merges contact information.
    """

    def __init__(self, headless: bool = True, slow_mo_ms: int = 250):
        self.headless = headless
        self.playwright_engine = PlaywrightCrawlerEngine(headless=headless, slow_mo_ms=slow_mo_ms)
        self.firecrawl_engine = FirecrawlEngine()
        self.crawl4ai_engine = Crawl4AIEngine()
        self.maps_scraper = GoogleMapsScraper(headless=headless)
        self.apify_connector = ApifyConnector()

    async def discover_leads(self, query: str, location: str, limit: int = 10) -> List[RawLead]:
        """Discovers initial business profiles via Maps/Directories, then deep-crawls each target."""
        logger.info(f"Starting discovery phase: query='{query}', location='{location}', limit={limit}")

        # Step 1: Discover candidate businesses
        candidates = await self.maps_scraper.search_businesses(query, location, limit=limit)
        logger.info(f"Discovered {len(candidates)} candidate business listings.")

        enriched_raw_leads: List[RawLead] = []

        # Step 2: Deep crawl each candidate website to harvest emails, phones, and context
        for candidate in candidates:
            if not candidate.website:
                enriched_raw_leads.append(candidate)
                continue

            clean_url = candidate.website
            logger.info(f"Deep crawling candidate site: {clean_url}")

            deep_lead: Optional[RawLead] = None

            # Priority 1: Firecrawl (if key available)
            if self.firecrawl_engine.is_available:
                deep_lead = self.firecrawl_engine.scrape_url(clean_url, candidate.business_name)

            # Priority 2: Crawl4AI (if installed and available)
            if not deep_lead and self.crawl4ai_engine.is_available:
                deep_lead = await self.crawl4ai_engine.crawl(clean_url, candidate.business_name)

            # Priority 3: Playwright Crawler Engine (Headless / Visual)
            if not deep_lead:
                deep_lead = await self.playwright_engine.crawl_site(clean_url, candidate.business_name)

            if deep_lead:
                # Merge directory metadata with deep crawl results
                deep_lead.phone = deep_lead.phone or candidate.phone
                deep_lead.address = deep_lead.address or candidate.address
                deep_lead.rating = candidate.rating
                deep_lead.review_count = candidate.review_count
                deep_lead.category = candidate.category
                enriched_raw_leads.append(deep_lead)
            else:
                enriched_raw_leads.append(candidate)

        # Step 3: Deduplicate by domain
        return self._deduplicate(enriched_raw_leads)

    def _deduplicate(self, leads: List[RawLead]) -> List[RawLead]:
        """Deduplicates leads by domain or normalized business name."""
        seen_domains = set()
        seen_names = set()
        unique_leads: List[RawLead] = []

        for lead in leads:
            domain = ""
            if lead.website:
                domain = urlparse(lead.website).netloc.lower().replace("www.", "")

            name_norm = lead.business_name.strip().lower()

            if domain and domain in seen_domains:
                continue
            if not domain and name_norm in seen_names:
                continue

            if domain:
                seen_domains.add(domain)
            seen_names.add(name_norm)
            unique_leads.append(lead)

        logger.info(f"Deduplication complete: {len(unique_leads)} unique target leads preserved.")
        return unique_leads
