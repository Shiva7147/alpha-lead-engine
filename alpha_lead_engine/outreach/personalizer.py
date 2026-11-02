"""Context-Aware Outreach Generator - Crafts factual, hyper-personalized cold outreach sequences.
Mandate: Cites actual offerings/facts discovered on the prospect's digital footprint.
"""

from __future__ import annotations

import logging
from typing import Optional

from alpha_lead_engine.auditor.schemas import AuditScore, EmailDraft, RawLead
from alpha_lead_engine.llm.client import LLMClient

logger = logging.getLogger("alpha_lead_engine.outreach.personalizer")


class OutreachPersonalizer:
    """Generates 3-step high-converting, fact-backed email sequences tailored to audited leads."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_sequence(
        self,
        lead_id: str,
        lead: RawLead,
        audit: AuditScore,
        sender_name: str,
        sender_offering: str,
    ) -> EmailDraft:
        """Constructs an initial email, Day 3 follow-up, and Day 7 follow-up citing real facts."""
        logger.info(f"Generating personalized email sequence for '{lead.business_name}'...")

        recipient_name = audit.estimated_decision_maker or f"Team at {lead.business_name}"
        facts_summary = "; ".join(audit.priority_signals + audit.key_offerings_observed)

        system_prompt = (
            "You are an elite B2B sales copywriter specializing in ultra-personalized, respectful, "
            "low-friction cold outreach. You strictly avoid generic buzzwords ('supercharge', 'synergy', 'revolutionary'). "
            "Every email must explicitly cite at least one real observation from the prospect's business."
        )

        prompt = f"""
Draft a personalized 3-part cold email sequence.

[PROSPECT INFORMATION]:
- Company Name: {lead.business_name}
- Website: {lead.website}
- Estimated Contact / Title: {recipient_name}
- Verified Signals / Offerings: {facts_summary}
- Lead Auditor Reasoning: {audit.reasoning}
- Recommended Angle: {audit.recommended_outreach_angle}

[SENDER VALUE PROPOSITION]:
- Sender Name: {sender_name}
- Product / Solution: {sender_offering}

MANDATORY RULES:
1. 'initial_email':
   - Max 85 words.
   - Genuine hook citing a specific service/detail from their site ({facts_summary}).
   - Plain statement of how {sender_name}'s offering helps them.
   - Low-friction interest call-to-action (e.g. 'Worth a 4-minute chat this Thursday?').
2. 'followup_day3':
   - Max 45 words.
   - Short conversational bump referencing the initial note.
3. 'followup_day7':
   - Max 60 words.
   - Value-add takeaway (e.g. sharing a quick observation or framework relevant to their space).
4. Subject line: Short, punchy, lowercase or title case, no spam words.
"""

        try:
            draft = self.llm.complete_structured(prompt, EmailDraft, system_prompt=system_prompt)
            draft.lead_id = lead_id
            draft.recipient_email = lead.email or "contact@unknown.com"
            draft.recipient_name = recipient_name
            draft.facts_referenced = audit.priority_signals[:3]
            logger.info(f"Generated draft for {lead.business_name}: Subject='{draft.subject}'")
            return draft
        except Exception as e:
            logger.warning(f"Structured outreach generation failed: {e}. Generating default high-craft template.")
            subject = f"Question regarding {lead.business_name}'s client acquisition"
            initial = (
                f"Hi {recipient_name},\n\n"
                f"I was reviewing {lead.business_name}'s recent work in {lead.category or 'your sector'} "
                f"and noticed your focus on {audit.key_offerings_observed[0] if audit.key_offerings_observed else 'client service'}.\n\n"
                f"We built {sender_name} to help companies like yours {sender_offering.lower()} without adding extra overhead.\n\n"
                f"Would you be open to a 5-minute chat this Thursday to see how this could work for {lead.business_name}?\n\n"
                f"Best,\n{sender_name}"
            )
            f_day3 = (
                f"Hi {recipient_name},\n\n"
                f"Following up briefly on my note from earlier this week. Would love to share two quick ideas tailored to {lead.business_name}'s current pipeline.\n\n"
                f"Best,\n{sender_name}"
            )
            f_day7 = (
                f"Hi {recipient_name},\n\n"
                f"Sharing a quick benchmark on how similar teams streamlined their workflow and generated consistent pipeline this quarter. "
                f"Happy to send over the 1-page summary if helpful.\n\n"
                f"Best,\n{sender_name}"
            )
            return EmailDraft(
                lead_id=lead_id,
                recipient_email=lead.email or "contact@unknown.com",
                recipient_name=recipient_name,
                subject=subject,
                initial_email=initial,
                followup_day3=f_day3,
                followup_day7=f_day7,
                facts_referenced=audit.priority_signals[:2],
            )
