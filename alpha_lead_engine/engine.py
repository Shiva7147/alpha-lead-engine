"""High-Level Alpha Lead Engine Orchestration Workflow.
Ties together Discovery -> Line-by-Line AI Audit -> MX Verification -> Outreach Gen -> Human Escalation -> Email Campaign.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, List, Optional
from urllib.parse import urlparse
import uuid

from alpha_lead_engine.auditor.lead_scorer import LeadScorer
from alpha_lead_engine.auditor.pipeline_store import PipelineStore
from alpha_lead_engine.auditor.schemas import (
    CampaignState,
    EnrichedLead,
    FitTier,
    HumanReviewCheckpoint,
    LeadStatus,
    RawLead,
)
from alpha_lead_engine.auditor.syntax_and_mx_validator import SyntaxAndMXValidator
from alpha_lead_engine.automation.sender import EmailSender
from alpha_lead_engine.automation.tracker_and_followup import CampaignTracker
from alpha_lead_engine.crawlers.crawler_router import CrawlerRouter
from alpha_lead_engine.escalation.bridge import MobileEscalationBridge
from alpha_lead_engine.llm.client import LLMClient
from alpha_lead_engine.outreach.personalizer import OutreachPersonalizer

logger = logging.getLogger("alpha_lead_engine.engine")


class AlphaLeadEngine:
    """End-to-end autonomous engine coordinating discovery, auditing, outreach, and escalation."""

    def __init__(
        self,
        db_path: str = "alpha_leads.db",
        headless: bool = True,
        dry_run: bool = False,
        require_human_approval_to_send: bool = True,
        llm_client: Optional[LLMClient] = None,
    ):
        self.headless = headless
        self.dry_run = dry_run
        self.require_human_approval_to_send = require_human_approval_to_send

        # Core Components
        self.llm = llm_client or LLMClient()
        self.store = PipelineStore(db_path=db_path)
        self.crawler = CrawlerRouter(headless=headless)
        self.mx_validator = SyntaxAndMXValidator()
        self.scorer = LeadScorer(llm_client=self.llm)
        self.personalizer = OutreachPersonalizer(llm_client=self.llm)
        self.sender = EmailSender(dry_run=dry_run)
        self.tracker = CampaignTracker(store=self.store, sender=self.sender)
        self.mobile_bridge = MobileEscalationBridge()

    async def execute_discovery_and_audit(
        self,
        business_name: str,
        business_offering: str,
        icp_keywords: str,
        location: str,
        limit: int = 5,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[EnrichedLead]:
        """Runs multi-engine discovery, line-by-line AI auditing, and draft personalization."""
        logger.info(f"=== Starting Engine Workflow: '{business_name}' -> '{icp_keywords}' in '{location}' ===")

        if progress_callback:
            progress_callback(f"Discovering candidate businesses across directories...", 1, 4)

        # 1. Multi-crawler discovery
        raw_leads = await self.crawler.discover_leads(query=icp_keywords, location=location, limit=limit)
        logger.info(f"Retrieved {len(raw_leads)} candidate targets.")

        enriched_results: List[EnrichedLead] = []
        total = len(raw_leads)

        # 2. Line-by-line audit & enrichment
        for idx, raw in enumerate(raw_leads):
            if progress_callback:
                progress_callback(f"Auditing '{raw.business_name}'...", idx + 1, total)

            domain = ""
            if raw.website:
                domain = urlparse(raw.website).netloc.lower().replace("www.", "")

            lead_id = str(uuid.uuid4())[:12]

            # MX Record Verification
            mx_valid = False
            if raw.email:
                mx_valid, mx_reason = self.mx_validator.validate_email(raw.email)
                logger.info(f"MX Verification for {raw.email}: {mx_valid} ({mx_reason})")

            # Line-by-line AI Audit
            audit = self.scorer.audit_lead(
                lead=raw,
                icp_description=f"Keywords: {icp_keywords}. Location: {location}",
                business_offering=business_offering,
            )

            # Personalize cold outreach email sequence
            draft = self.personalizer.generate_sequence(
                lead_id=lead_id,
                lead=raw,
                audit=audit,
                sender_name=business_name,
                sender_offering=business_offering,
            )

            # Determine initial status
            initial_status = LeadStatus.DISCOVERED
            checkpoint = None

            if audit.fit_tier == FitTier.DISQUALIFIED or audit.score < 30:
                initial_status = LeadStatus.SUPPRESSED
            elif not raw.email or not mx_valid:
                initial_status = LeadStatus.AUDITED
            elif self.require_human_approval_to_send:
                initial_status = LeadStatus.NEEDS_HUMAN_REVIEW
                checkpoint = HumanReviewCheckpoint(
                    checkpoint_id=f"chk_{lead_id}",
                    lead_id=lead_id,
                    reason=f"High-fit lead ({audit.score}/100) prepared. Human review required before dispatching email.",
                    context={
                        "company": raw.business_name,
                        "email": raw.email,
                        "subject": draft.subject,
                        "initial_email": draft.initial_email,
                        "audit_score": audit.score,
                    },
                    proposed_action=f"Approve sending cold email to {raw.email}",
                )
                # Dispatch mobile notification to phone
                self.mobile_bridge.dispatch_alert(checkpoint, raw.business_name, raw.email)
            else:
                initial_status = LeadStatus.QUEUED

            enriched = EnrichedLead(
                id=lead_id,
                raw=raw,
                clean_domain=domain,
                mx_valid=mx_valid,
                audit=audit,
                email_draft=draft,
                status=initial_status,
                escalation=checkpoint,
            )

            self.store.save_lead(enriched)
            enriched_results.append(enriched)

        logger.info(f"Workflow completed! Processed {len(enriched_results)} leads.")
        return enriched_results

    def approve_lead_for_sending(self, lead_id: str) -> bool:
        """Approves a flagged lead and moves it to the dispatch queue."""
        lead = self.store.get_lead(lead_id)
        if not lead:
            return False

        lead.status = LeadStatus.QUEUED
        if lead.escalation:
            lead.escalation.status = "APPROVED"
        self.store.save_lead(lead)
        logger.info(f"Lead '{lead.raw.business_name}' approved by human operator.")
        return True

    def run_campaign_cycle(self) -> dict:
        """Executes one cycle of sending queued emails and checking follow-ups."""
        return self.tracker.process_campaign_cycle()

    def get_metrics(self) -> CampaignState:
        """Returns campaign state and statistics."""
        return self.store.get_campaign_metrics()
