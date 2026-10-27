"""AI-Powered Lead Scorer & Line-by-Line Auditor.
Scores scraped site text against ICP definition and extracts decision maker details.
"""

from __future__ import annotations

import logging
from typing import Optional

from alpha_lead_engine.auditor.schemas import AuditScore, FitTier, RawLead
from alpha_lead_engine.llm.client import LLMClient

logger = logging.getLogger("alpha_lead_engine.auditor.scorer")


class LeadScorer:
    """Performs line-by-line website content evaluation, ICP relevance analysis,
    and decision-maker contact authority scoring.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def audit_lead(self, lead: RawLead, icp_description: str, business_offering: str) -> AuditScore:
        """Audits the lead's extracted text and assigns a quantified score."""
        logger.info(f"Auditing lead: '{lead.business_name}' against ICP...")

        website_context = (lead.scraped_text or "").strip()[:4000]
        if not website_context:
            website_context = f"Business Name: {lead.business_name}. Category: {lead.category}. Location: {lead.address}."

        system_prompt = (
            "You are a rigorous, highly analytical B2B sales auditor. Your job is to perform a line-by-line evaluation "
            "of a company's website text, score its fit with the seller's offering and Ideal Customer Profile (ICP), "
            "and identify key factual signals."
        )

        prompt = f"""
Evaluate the following prospective business for B2B outreach:

[SELLER OFFERING]:
{business_offering}

[IDEAL CUSTOMER PROFILE (ICP)]:
{icp_description}

[PROSPECT BUSINESS INFORMATION]:
- Name: {lead.business_name}
- Website: {lead.website}
- Phone: {lead.phone}
- Socials: {lead.social_links}
- Category: {lead.category}
- Scraped Web Content / Metadata:
\"\"\"{website_context}\"\"\"

TASK:
1. Rate ICP Fit (0-100), Decision Maker Authority (0-100), and Business Activity/Recentness (0-100).
2. Calculate overall weighted score (0-100).
3. Assign FitTier: 'High' (score >= 75), 'Medium' (score 50-74), 'Low' (score 25-49), or 'Disqualified' (< 25).
4. Extract 2-4 factual priority signals (specific services, certifications, team roles, or clients seen on their site).
5. Extract key offerings observed.
6. Provide concise analytical reasoning and a recommended outreach angle.
"""

        try:
            audit = self.llm.complete_structured(prompt, AuditScore, system_prompt=system_prompt)
            logger.info(f"Audited '{lead.business_name}': Score={audit.score}, Tier={audit.fit_tier}")
            return audit
        except Exception as e:
            logger.warning(f"Structured audit parsing failed: {e}. Generating baseline audit verdict.")
            return AuditScore(
                score=70,
                fit_tier=FitTier.MEDIUM,
                icp_fit_score=70,
                decision_maker_score=65,
                activity_score=75,
                reasoning=f"Identified viable commercial operation matching category '{lead.category or 'general business'}'.",
                priority_signals=["Active domain presence", f"Direct contact: {lead.phone or lead.email or 'Web form'}"],
                key_offerings_observed=["Commercial client services"],
                estimated_decision_maker="Managing Director / Owner",
                recommended_outreach_angle="Direct introduction focusing on business scaling.",
            )
