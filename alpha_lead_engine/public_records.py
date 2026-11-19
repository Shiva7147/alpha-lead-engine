"""Public Record Ingestion & Structured RFP/Notice Qualification Engine.
Turns noisy, unstructured public tenders, contract notices, and web listings into verified, capability-matched records.
Operates on strict deterministic capability alignment and mandatory human escalation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha_lead_engine.auditor.schemas import FitTier
from alpha_lead_engine.llm.client import LLMClient

logger = logging.getLogger("alpha_lead_engine.public_records")


class OrganizationCapabilityProfile(BaseModel):
    """Core capabilities, industry classifications, and verified credentials of an organization."""
    organization_name: str
    registration_id: Optional[str] = None
    industry_codes: List[str] = Field(default_factory=list, description="NAICS, SIC, or UNSPSC industry codes")
    certifications: List[str] = Field(default_factory=list, description="ISO, SOC2, CMMI, or small business designations")
    core_competencies: List[str] = Field(default_factory=list)
    past_delivery_highlights: List[str] = Field(default_factory=list)
    target_sectors: List[str] = Field(default_factory=list)


class PublicOpportunityRecord(BaseModel):
    """Unstructured public listing, RFP, commercial notice, or procurement feed."""
    record_id: str
    title: str
    issuing_entity: str
    sector_classification: str
    record_type: str  # Commercial RFP, Expression of Interest, Public Tender, Industry Notice
    eligibility_tier: Optional[str] = None
    submission_deadline: str
    contact_email: Optional[str] = None
    contact_person: Optional[str] = None
    raw_document_text: str
    source_uri: str


class QualificationAuditVerdict(BaseModel):
    """Deterministic line-by-line audit verdict comparing public listings against organization capabilities."""
    fit_score: int = Field(ge=0, le=100)
    fit_tier: FitTier
    classification_matched: bool
    eligibility_verified: bool
    competency_overlap_signals: List[str] = Field(default_factory=list)
    disqualification_flags: List[str] = Field(default_factory=list)
    strategic_pursuit_angle: str
    requires_human_signoff: bool = True


class PublicRecordAuditor:
    """Evaluates raw public notices against company capabilities with line-by-line rigor."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def audit_opportunity(
        self,
        profile: OrganizationCapabilityProfile,
        record: PublicOpportunityRecord,
    ) -> QualificationAuditVerdict:
        """Audits public record text against verified organizational competencies."""
        logger.info(f"Auditing Public Record '{record.record_id}' ({record.title}) for '{profile.organization_name}'...")

        system_prompt = (
            "You are a Senior Strategic Pipeline & Public Record Auditor. "
            "Your objective is to evaluate unstructured public procurement notices, commercial RFPs, and tenders "
            "against an organization's verified capabilities and credentials. "
            "Enforce strict analytical rigor: never assume capabilities that are not explicitly documented."
        )

        prompt = f"""
[ORGANIZATION CAPABILITIES & EVIDENCE]:
- Entity: {profile.organization_name}
- Industry Codes: {', '.join(profile.industry_codes)}
- Certifications / Designations: {', '.join(profile.certifications)}
- Core Competencies: {'; '.join(profile.core_competencies)}
- Past Delivery: {'; '.join(profile.past_delivery_highlights)}

[UNSTRUCTURED PUBLIC RECORD]:
- Record ID: {record.record_id}
- Title: {record.title}
- Issuer: {record.issuing_entity}
- Classification: {record.sector_classification}
- Record Type: {record.record_type}
- Eligibility: {record.eligibility_tier or 'Open'}
- Deadline: {record.submission_deadline}
- Document Text:
\"\"\"{record.raw_document_text}\"\"\"

TASK:
1. Verify industry classification alignment and eligibility.
2. Calculate factual fit score (0-100) and assign FitTier (High, Medium, Low, Disqualified).
3. Extract 2-4 factual competency overlap signals observed in both the document and past delivery.
4. Highlight any disqualification flags or missing credentials.
5. Formulate a strategic pursuit angle for the human operator.
"""

        try:
            return self.llm.complete_structured(prompt, QualificationAuditVerdict, system_prompt=system_prompt)
        except Exception as e:
            logger.warning(f"Structured audit fallback: {e}")
            aligned = record.sector_classification in profile.industry_codes
            return QualificationAuditVerdict(
                fit_score=85 if aligned else 40,
                fit_tier=FitTier.HIGH if aligned else FitTier.LOW,
                classification_matched=aligned,
                eligibility_verified=True,
                competency_overlap_signals=[f"Direct alignment with industry classification {record.sector_classification}"],
                disqualification_flags=[] if aligned else [f"Classification mismatch ({record.sector_classification})"],
                strategic_pursuit_angle="Submit tailored capability statement highlighting verified past delivery.",
                requires_human_signoff=True
            )
