"""Standalone quickstart demo showcasing lead discovery, line-by-line audit,
personalized outreach generation, and mobile human escalation checkpoints.
"""

import asyncio
from alpha_lead_engine.engine import AlphaLeadEngine
from alpha_lead_engine.auditor.schemas import LeadStatus


async def run_demo():
    print("=" * 60)
    print("🚀 ALPHA LEAD ENGINE - Autonomous Lead Discovery & Outreach")
    print("=" * 60)

    # Initialize in safe dry-run mode with human review checkpoints enabled
    engine = AlphaLeadEngine(
        db_path="demo_leads.db",
        headless=True,
        dry_run=True,
        require_human_approval_to_send=True
    )

    print("\n[Step 1] Running Multi-Engine Discovery & Line-by-Line AI Audit...")
    leads = await engine.execute_discovery_and_audit(
        business_name="Nexus Growth AI",
        business_offering="Autonomous AI B2B Lead Acquisition and Line-by-Line Sales Pipeline Validation",
        icp_keywords="Digital Marketing Agencies",
        location="Miami, FL",
        limit=3,
        progress_callback=lambda msg, curr, tot: print(f"  [{curr}/{tot}] {msg}"),
    )

    print(f"\n[Step 2] Processing Completed! Found {len(leads)} leads:")
    for lead in leads:
        print("\n" + "-" * 50)
        print(f"🏢 Company: {lead.raw.business_name}")
        print(f"🌐 Website: {lead.raw.website}")
        print(f"📧 Email:   {lead.raw.email} (MX Record Valid: {lead.mx_valid})")
        if lead.audit:
            print(f"📊 Audit Score: {lead.audit.score}/100 (Tier: {lead.audit.fit_tier.value})")
            print(f"💡 Observed Offerings: {', '.join(lead.audit.key_offerings_observed)}")
            print(f"🎯 Recommended Angle:  {lead.audit.recommended_outreach_angle}")
        if lead.email_draft:
            print(f"✉️ Subject: {lead.email_draft.subject}")
            print(f"📝 Draft Preview:\n{lead.email_draft.initial_email[:200]}...")

        if lead.status == LeadStatus.NEEDS_HUMAN_REVIEW:
            print("🚨 Status: Awaiting Human Escalation Approval (Notification Dispatched to Phone)")

    # Simulate Human Operator Approval for the top lead
    if leads:
        top_lead = leads[0]
        print(f"\n[Step 3] Operator reviews and approves '{top_lead.raw.business_name}'...")
        engine.approve_lead_for_sending(top_lead.id)

        print("\n[Step 4] Triggering Autonomous Campaign Cycle...")
        summary = engine.run_campaign_cycle()
        print(f"  Cycle Results: {summary}")

    print("\n[Step 5] Checking Updated Pipeline Metrics:")
    metrics = engine.get_metrics()
    print(f"  Total Discovered: {metrics.total_discovered}")
    print(f"  Total Audited:    {metrics.total_audited}")
    print(f"  Total Sent:       {metrics.total_sent}")
    print(f"  Pending Review:   {metrics.total_pending_human_review}")
    print("=" * 60)
    print("✔ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_demo())
