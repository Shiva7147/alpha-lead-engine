"""Autonomous Campaign Loop & Follow-Up Tracker.
Monitors sent threads, triggers Day 3 and Day 7 follow-ups, and escalates interested replies.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from alpha_lead_engine.auditor.pipeline_store import PipelineStore
from alpha_lead_engine.auditor.schemas import EnrichedLead, HumanReviewCheckpoint, LeadStatus
from alpha_lead_engine.automation.reply_classifier import ReplyClassifier
from alpha_lead_engine.automation.sender import EmailSender

logger = logging.getLogger("alpha_lead_engine.automation.tracker")


class CampaignTracker:
    """Manages the autonomous lifecycle loop for sent email threads."""

    def __init__(
        self,
        store: PipelineStore,
        sender: EmailSender,
        classifier: Optional[ReplyClassifier] = None,
    ):
        self.store = store
        self.sender = sender
        self.classifier = classifier or ReplyClassifier()

    def process_campaign_cycle(self) -> dict:
        """Runs a complete check across all active leads in the pipeline."""
        now = datetime.utcnow()
        summary = {
            "initial_sent": 0,
            "followups_day3_sent": 0,
            "followups_day7_sent": 0,
            "replies_processed": 0,
            "escalated_to_human": 0,
        }

        # 1. Send initial emails for QUEUED leads
        queued_leads = self.store.list_leads(status=LeadStatus.QUEUED, limit=50)
        for lead in queued_leads:
            if not lead.email_draft or not lead.raw.email:
                continue

            success, thread_id, msg_id = self.sender.send_email(
                to_email=lead.raw.email,
                subject=lead.email_draft.subject,
                body=lead.email_draft.initial_email,
            )

            if success:
                lead.status = LeadStatus.SENT
                lead.thread_id = thread_id
                lead.last_message_id = msg_id
                lead.initial_sent_at = now
                self.store.save_lead(lead)
                summary["initial_sent"] += 1
                logger.info(f"Initial outreach sent to {lead.raw.email} ({lead.raw.business_name})")

        # 2. Check FOLLOWUP_PENDING / SENT leads for follow-ups
        active_leads = self.store.list_leads(status=LeadStatus.SENT, limit=100)
        active_leads += self.store.list_leads(status=LeadStatus.FOLLOWUP_PENDING, limit=100)

        for lead in active_leads:
            if not lead.initial_sent_at or not lead.email_draft or not lead.raw.email:
                continue

            # Day 3 Follow-up
            if not lead.followup_1_sent_at and (now - lead.initial_sent_at) >= timedelta(days=3):
                logger.info(f"Triggering Day 3 Follow-up for {lead.raw.business_name}...")
                success, thread_id, msg_id = self.sender.send_email(
                    to_email=lead.raw.email,
                    subject=f"Re: {lead.email_draft.subject}",
                    body=lead.email_draft.followup_day3,
                    thread_id=lead.thread_id,
                    in_reply_to=lead.last_message_id,
                )
                if success:
                    lead.followup_1_sent_at = now
                    lead.last_message_id = msg_id
                    lead.status = LeadStatus.FOLLOWUP_PENDING
                    self.store.save_lead(lead)
                    summary["followups_day3_sent"] += 1

            # Day 7 Follow-up
            elif (
                lead.followup_1_sent_at
                and not lead.followup_2_sent_at
                and (now - lead.initial_sent_at) >= timedelta(days=7)
            ):
                logger.info(f"Triggering Day 7 Final Follow-up for {lead.raw.business_name}...")
                success, thread_id, msg_id = self.sender.send_email(
                    to_email=lead.raw.email,
                    subject=f"Re: {lead.email_draft.subject}",
                    body=lead.email_draft.followup_day7,
                    thread_id=lead.thread_id,
                    in_reply_to=lead.last_message_id,
                )
                if success:
                    lead.followup_2_sent_at = now
                    lead.last_message_id = msg_id
                    self.store.save_lead(lead)
                    summary["followups_day7_sent"] += 1

        return summary

    def handle_inbound_reply(self, lead_id: str, reply_text: str) -> EnrichedLead:
        """Processes an incoming email response for a tracked lead."""
        lead = self.store.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead with id '{lead_id}' not found.")

        lead.last_reply_snippet = reply_text[:500]
        verdict = self.classifier.classify_reply(reply_text, lead.raw.business_name)

        if verdict.category == "UNSUBSCRIBE":
            lead.status = LeadStatus.SUPPRESSED
            logger.info(f"Prospect '{lead.raw.business_name}' opted out. Lead suppressed.")
        elif verdict.category == "NOT_NOW":
            # Leave in current state or snooze
            logger.info(f"Prospect '{lead.raw.business_name}' auto-reply noted (Out of office).")
        elif verdict.category in ("POSITIVE", "NEUTRAL") or verdict.requires_human_escalation:
            lead.status = LeadStatus.NEEDS_HUMAN_REVIEW
            lead.escalation = HumanReviewCheckpoint(
                checkpoint_id=f"chk_{lead.id[:8]}",
                lead_id=lead.id,
                reason=f"Prospect replied ({verdict.category}): {verdict.reasoning}",
                context={
                    "reply_text": reply_text,
                    "confidence": verdict.confidence,
                    "suggested_response": verdict.suggested_response_summary,
                },
                proposed_action="Review incoming reply and approve customized human response",
            )
            logger.info(f"🚨 HUMAN ESCALATION REQUIRED for '{lead.raw.business_name}': {verdict.reasoning}")

        self.store.save_lead(lead)
        return lead
