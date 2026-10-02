"""Core Pydantic schemas and data models for Alpha Lead Engine.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class LeadStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    AUDITED = "AUDITED"
    QUEUED = "QUEUED"
    SENT = "SENT"
    FOLLOWUP_PENDING = "FOLLOWUP_PENDING"
    REPLIED = "REPLIED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    SUPPRESSED = "SUPPRESSED"


class FitTier(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    DISQUALIFIED = "Disqualified"


class RawLead(BaseModel):
    """Raw lead harvested by crawlers/scrapers."""
    business_name: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: Optional[str] = None
    source_engine: str = "crawler"
    social_links: Dict[str, str] = Field(default_factory=dict)
    scraped_text: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditScore(BaseModel):
    """Detailed audit verdict returned by the AI line-by-line auditor."""
    score: int = Field(ge=0, le=100, description="Overall score between 0 and 100")
    fit_tier: FitTier = Field(description="High, Medium, Low, or Disqualified")
    icp_fit_score: int = Field(default=0, ge=0, le=100)
    decision_maker_score: int = Field(default=0, ge=0, le=100)
    activity_score: int = Field(default=0, ge=0, le=100)
    reasoning: str
    priority_signals: List[str] = Field(default_factory=list)
    key_offerings_observed: List[str] = Field(default_factory=list)
    estimated_decision_maker: Optional[str] = None
    recommended_outreach_angle: Optional[str] = None


class EmailDraft(BaseModel):
    """Sequence of customized cold outreach messages."""
    lead_id: str
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    initial_email: str
    followup_day3: str
    followup_day7: str
    facts_referenced: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HumanReviewCheckpoint(BaseModel):
    """Escalation payload requiring human confirmation via CLI or mobile/push notification."""
    checkpoint_id: str
    lead_id: str
    reason: str
    context: Dict[str, Any] = Field(default_factory=dict)
    proposed_action: str
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, MODIFIED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    operator_notes: Optional[str] = None


class EnrichedLead(BaseModel):
    """Complete representation of an enriched lead tracked through the lifecycle."""
    id: str
    raw: RawLead
    clean_domain: str
    mx_valid: bool = False
    audit: Optional[AuditScore] = None
    email_draft: Optional[EmailDraft] = None
    status: LeadStatus = LeadStatus.DISCOVERED
    thread_id: Optional[str] = None
    last_message_id: Optional[str] = None
    initial_sent_at: Optional[datetime] = None
    followup_1_sent_at: Optional[datetime] = None
    followup_2_sent_at: Optional[datetime] = None
    last_reply_snippet: Optional[str] = None
    escalation: Optional[HumanReviewCheckpoint] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CampaignState(BaseModel):
    """Snapshot of active pipeline and metrics."""
    campaign_name: str
    total_discovered: int = 0
    total_mx_verified: int = 0
    total_audited: int = 0
    total_sent: int = 0
    total_followups_sent: int = 0
    total_replies: int = 0
    total_pending_human_review: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)
