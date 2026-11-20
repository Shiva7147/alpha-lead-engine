import os
import pytest
from alpha_lead_engine.auditor.schemas import RawLead, AuditScore, FitTier, EmailDraft, EnrichedLead, LeadStatus
from alpha_lead_engine.auditor.syntax_and_mx_validator import SyntaxAndMXValidator
from alpha_lead_engine.auditor.lead_scorer import LeadScorer
from alpha_lead_engine.auditor.pipeline_store import PipelineStore
from alpha_lead_engine.outreach.personalizer import OutreachPersonalizer
from alpha_lead_engine.automation.reply_classifier import ReplyClassifier
from alpha_lead_engine.automation.tracker_and_followup import CampaignTracker
from alpha_lead_engine.automation.sender import EmailSender


def test_syntax_and_mx_validator():
    validator = SyntaxAndMXValidator()
    # Invalid syntax
    valid, reason = validator.validate_email("notanemail")
    assert not valid
    assert "Invalid email address syntax" in reason

    # Empty email
    valid, reason = validator.validate_email("")
    assert not valid

    # Known domain syntax check
    valid, reason = validator.validate_email("test@google.com")
    assert valid


def test_pipeline_store(tmp_path):
    db_file = tmp_path / "test_leads.db"
    store = PipelineStore(db_path=str(db_file))

    raw = RawLead(business_name="Acme Corp", website="https://acme.test", email="contact@acme.test")
    lead = EnrichedLead(id="lead_123", raw=raw, clean_domain="acme.test", status=LeadStatus.DISCOVERED)

    store.save_lead(lead)
    retrieved = store.get_lead("lead_123")
    assert retrieved is not None
    assert retrieved.raw.business_name == "Acme Corp"

    # Test status update
    store.update_status("lead_123", LeadStatus.QUEUED)
    updated = store.get_lead("lead_123")
    assert updated.status == LeadStatus.QUEUED


def test_lead_scorer_and_personalizer():
    scorer = LeadScorer()
    raw = RawLead(
        business_name="Peak AI Agency",
        website="https://peakai.example",
        email="hello@peakai.example",
        category="AI Consulting",
        scraped_text="Peak AI delivers enterprise LLM agent deployment and autonomous workflows for SaaS founders."
    )
    audit = scorer.audit_lead(
        lead=raw,
        icp_description="B2B AI Agencies",
        business_offering="Autonomous Lead Discovery Engine"
    )
    assert audit.score > 0
    assert audit.fit_tier in [FitTier.HIGH, FitTier.MEDIUM, FitTier.LOW, FitTier.DISQUALIFIED]

    personalizer = OutreachPersonalizer()
    draft = personalizer.generate_sequence(
        lead_id="test_lead",
        lead=raw,
        audit=audit,
        sender_name="Alpha Engine",
        sender_offering="Autonomous Lead Generation",
    )
    assert draft.subject
    assert draft.initial_email
    assert draft.followup_day3
    assert draft.followup_day7


def test_reply_classifier():
    classifier = ReplyClassifier()
    positive = classifier.classify_reply(
        "Hi Shiva, thanks for reaching out. Yes, we would love to see how this works. Are you free Thursday at 2 PM?",
        "Peak AI"
    )
    assert positive.category == "POSITIVE"
    assert positive.requires_human_escalation is True

    unsub = classifier.classify_reply(
        "Please remove me from your mailing list and unsubscribe.",
        "Peak AI"
    )
    assert unsub.category == "UNSUBSCRIBE"
    assert unsub.requires_human_escalation is False
