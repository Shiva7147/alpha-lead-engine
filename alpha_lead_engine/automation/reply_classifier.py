"""Incoming Reply Classifier & Sentiment Analyzer.
Categorizes responses into POSITIVE / INTERESTED, NOT_NOW / OOO, or UNSUBSCRIBE.
"""

from __future__ import annotations

import logging
from typing import Optional
from pydantic import BaseModel, Field

from alpha_lead_engine.llm.client import LLMClient

logger = logging.getLogger("alpha_lead_engine.automation.classifier")


class ReplyVerdict(BaseModel):
    category: str = Field(description="POSITIVE, NOT_NOW, UNSUBSCRIBE, or NEUTRAL")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    reasoning: str
    requires_human_escalation: bool = False
    suggested_response_summary: Optional[str] = None


class ReplyClassifier:
    """Classifies inbound prospect emails and detects sentiment/intent."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def classify_reply(self, email_body: str, lead_company_name: str) -> ReplyVerdict:
        """Analyzes email text to determine the next action in the automated sequence."""
        system_prompt = (
            "You are a sales intent classification engine. Analyze incoming prospect responses and categorize them into:\n"
            "1. POSITIVE: The prospect is interested, wants to schedule a call, asked for pricing/info, or invited next steps.\n"
            "2. NOT_NOW: Out of office, sabbatical, parental leave, or told to check back in Q3/Q4.\n"
            "3. UNSUBSCRIBE: Direct request to stop emailing, remove from list, or hostility.\n"
            "4. NEUTRAL: Ambiguous, asking who this is, or routing to someone else.\n\n"
            "Flag `requires_human_escalation=True` if POSITIVE, NEUTRAL, or if they asked a specific technical question."
        )

        prompt = f"""
Incoming email response from prospect at '{lead_company_name}':
\"\"\"{email_body[:2000]}\"\"\"

Determine the category, confidence, reasoning, whether it requires human escalation, and provide a suggested response summary.
"""

        try:
            verdict = self.llm.complete_structured(prompt, ReplyVerdict, system_prompt=system_prompt)
            logger.info(f"Classified reply from '{lead_company_name}': {verdict.category} (Human Escalation: {verdict.requires_human_escalation})")
            return verdict
        except Exception as e:
            logger.warning(f"Error during reply classification: {e}. Running rule-based classifier.")
            lower = email_body.lower()
            if any(w in lower for w in ["interested", "call", "zoom", "schedule", "thursday", "pricing", "send info"]):
                return ReplyVerdict(
                    category="POSITIVE",
                    reasoning="Detected positive buying or discovery intent keywords.",
                    requires_human_escalation=True,
                    suggested_response_summary="Share calendar link and 2 available time slots."
                )
            if any(w in lower for w in ["unsubscribe", "remove", "stop emailing", "take me off"]):
                return ReplyVerdict(
                    category="UNSUBSCRIBE",
                    reasoning="Detected explicit opt-out request.",
                    requires_human_escalation=False,
                )
            if any(w in lower for w in ["out of the office", "on leave", "vacation", "auto-reply"]):
                return ReplyVerdict(
                    category="NOT_NOW",
                    reasoning="Detected standard out-of-office automated reply.",
                    requires_human_escalation=False,
                )
            return ReplyVerdict(
                category="NEUTRAL",
                reasoning="Generic inquiry requiring sales operator inspection.",
                requires_human_escalation=True,
                suggested_response_summary="Review conversation context manually."
            )
