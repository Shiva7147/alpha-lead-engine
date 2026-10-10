"""Playwright Crawler Engine with visible/headless toggle and stealth anti-detection.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from alpha_lead_engine.auditor.schemas import RawLead

logger = logging.getLogger("alpha_lead_engine.crawlers.playwright")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class PlaywrightCrawlerEngine:
    """Production-grade Playwright crawler supporting headless or visual live browser sessions."""

    def __init__(self, headless: bool = True, slow_mo_ms: int = 250):
        self.headless = headless
        self.slow_mo_ms = slow_mo_ms

    async def crawl_site(self, url: str, business_name: str = "") -> RawLead:
        """Navigates to URL, extracts full DOM text, emails, phones, and social handles."""
        if not url.startswith("http"):
            url = f"https://{url}"

        scraped_text = ""
        emails: List[str] = []
        phones: List[str] = []
        socials: Dict[str, str] = {}

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                ua = random.choice(USER_AGENTS)
                viewport = random.choice([
                    {"width": 1920, "height": 1080},
                    {"width": 1440, "height": 900},
                    {"width": 1366, "height": 768},
                ])

                browser = await p.chromium.launch(
                    headless=self.headless,
                    slow_mo=self.slow_mo_ms if not self.headless else 0,
                    args=["--disable-blink-features=AutomationControlled"]
                )

                context = await browser.new_context(
                    user_agent=ua,
                    viewport=viewport,
                    locale="en-US",
                )
                page = await context.new_page()

                logger.info(f"Navigating to {url} (headless={self.headless})...")
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(1000)

                # Scroll down slightly to trigger lazy loading
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(500)

                content = await page.content()
                inner_text = await page.inner_text("body")
                scraped_text = inner_text[:8000]

                # Extract emails from mailto: links and regex
                mailto_links = await page.locator("a[href^='mailto:']").all()
                for link in mailto_links:
                    href = await link.get_attribute("href")
                    if href:
                        email = href.replace("mailto:", "").split("?")[0].strip()
                        if email and email not in emails:
                            emails.append(email)

                # Regex fallback for text
                found_emails = EMAIL_REGEX.findall(content)
                for e in found_emails:
                    e_clean = e.strip().rstrip(".")
                    if not any(e_clean.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"]):
                        if e_clean not in emails:
                            emails.append(e_clean)

                # Extract phones
                found_phones = PHONE_REGEX.findall(inner_text)
                for ph in found_phones:
                    if isinstance(ph, tuple):
                        ph = "".join(ph)
                    ph_clean = ph.strip()
                    if ph_clean and ph_clean not in phones:
                        phones.append(ph_clean)

                # Social handles
                links = await page.locator("a[href]").all()
                for l in links[:50]:
                    href = await l.get_attribute("href")
                    if href:
                        h_lower = href.lower()
                        if "linkedin.com" in h_lower and "linkedin" not in socials:
                            socials["linkedin"] = href
                        elif "twitter.com" in h_lower or "x.com" in h_lower and "twitter" not in socials:
                            socials["twitter"] = href
                        elif "instagram.com" in h_lower and "instagram" not in socials:
                            socials["instagram"] = href
                        elif "facebook.com" in h_lower and "facebook" not in socials:
                            socials["facebook"] = href

                # If no business name provided, use page title
                if not business_name:
                    title = await page.title()
                    business_name = title.split("-")[0].split("|")[0].strip() or urlparse(url).netloc

                await browser.close()

        except Exception as e:
            logger.warning(f"Playwright crawl error for {url}: {e}. Falling back to standard HTTP scraper.")
            import urllib.request
            try:
                req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html_text = resp.read().decode("utf-8", errors="ignore")
                    scraped_text = html_text[:5000]
                    found_emails = EMAIL_REGEX.findall(html_text)
                    for e in found_emails:
                        if not any(e.endswith(ext) for ext in [".png", ".jpg"]):
                            emails.append(e)
            except Exception as http_err:
                logger.error(f"HTTP fallback error for {url}: {http_err}")

        primary_email = emails[0] if emails else None
        primary_phone = phones[0] if phones else None

        return RawLead(
            business_name=business_name or urlparse(url).netloc,
            website=url,
            email=primary_email,
            phone=primary_phone,
            source_engine="playwright",
            social_links=socials,
            scraped_text=scraped_text or f"Website discovered at {url}",
            metadata={"all_emails": emails, "all_phones": phones}
        )
