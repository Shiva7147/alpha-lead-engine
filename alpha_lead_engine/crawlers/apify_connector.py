"""Apify SDK Connector for large-scale crawling and distributed scrapers.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from alpha_lead_engine.auditor.schemas import RawLead

logger = logging.getLogger("alpha_lead_engine.crawlers.apify")


class ApifyConnector:
    """Connector using Apify Client SDK (`apify-client`) for optional cloud-scale scraping."""

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        self.client = None
        if self.api_token:
            try:
                from apify_client import ApifyClient
                self.client = ApifyClient(token=self.api_token)
            except ImportError:
                logger.info("apify-client not installed. Run `pip install apify-client` to enable.")

    @property
    def is_available(self) -> bool:
        return bool(self.client and self.api_token)

    def run_actor_scraper(self, actor_id: str, run_input: Dict[str, Any]) -> List[RawLead]:
        """Runs an Apify Actor (such as Google Maps or Instagram scraper) and converts results."""
        if not self.is_available:
            logger.info("Apify API token not configured. Skipping Apify connector.")
            return []

        leads: List[RawLead] = []
        try:
            logger.info(f"Triggering Apify Actor '{actor_id}'...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            dataset = self.client.dataset(run["defaultDatasetId"])

            for item in dataset.iterate_items():
                name = item.get("title") or item.get("name") or "Business"
                website = item.get("website") or item.get("url")
                email = item.get("email") or item.get("contactEmail")
                phone = item.get("phone") or item.get("phoneUnformatted")
                address = item.get("address") or item.get("city")

                leads.append(RawLead(
                    business_name=name,
                    website=website,
                    email=email,
                    phone=phone,
                    address=address,
                    source_engine=f"apify:{actor_id}",
                    scraped_text=str(item)[:2000],
                    metadata={"apify_item": item}
                ))
        except Exception as e:
            logger.error(f"Apify execution failed: {e}")

        return leads
