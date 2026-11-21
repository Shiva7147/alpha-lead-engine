"""Enterprise Public Record & Tender Qualification Demonstration.
Demonstrates converting noisy public tenders and expressions of interest (EOIs)
into structured, capability-matched records with human-in-the-loop review.
"""

from alpha_lead_engine.public_records import (
    OrganizationCapabilityProfile,
    PublicOpportunityRecord,
    PublicRecordAuditor,
)


def run_public_record_audit_demo():
    print("=" * 75)
    print("⚡ ALPHA LEAD ENGINE - Public Record & Tender Qualification Showcase")
    print("=" * 75)

    # 1. Organization Capability Profile
    profile = OrganizationCapabilityProfile(
        organization_name="Vanguard Cloud & Cyber Engineering Group",
        registration_id="CORP-98214-X",
        industry_codes=["541512", "541519", "518210"],
        certifications=["ISO-27001", "SOC2 Type II", "State Small Business Enterprise"],
        core_competencies=[
            "Enterprise Zero-Trust Architecture",
            "Continuous Cloud Compliance & DevSecOps",
            "Autonomous AI-Assisted Security Telemetry & Log Triage",
        ],
        past_delivery_highlights=[
            "Multi-region hybrid cloud migration for regional infrastructure authority",
            "Continuous automated vulnerability intelligence pipeline",
        ],
        target_sectors=["Enterprise IT", "State & Local Infrastructure", "Healthcare Systems"],
    )

    print(f"\n[Organization Registered]: {profile.organization_name}")
    print(f"  • Certifications: {', '.join(profile.certifications)}")
    print(f"  • Industry Codes: {', '.join(profile.industry_codes)}")
    print(f"  • Key Delivery:   {profile.past_delivery_highlights[0]}")

    # 2. Raw Public Notices Scraped from Public Data Portals
    records = [
        PublicOpportunityRecord(
            record_id="PUB-TEN-2026-089",
            title="Expression of Interest: Enterprise Zero-Trust Architecture & Threat Ingestion Pipeline",
            issuing_entity="Regional Transportation & Logistics Infrastructure Authority",
            sector_classification="541512",
            record_type="Public Expression of Interest",
            eligibility_tier="Enterprise Certified Small Business",
            submission_deadline="2026-12-18",
            contact_email="procurement@infra-transit.example.gov",
            contact_person="Director of Digital Infrastructure",
            raw_document_text=(
                "The Authority seeks qualified technical providers to design and deploy an enterprise zero-trust cloud network. "
                "The solution requires continuous compliance auditing, SOC2/ISO aligned telemetry ingestion, and automated threat log synthesis "
                "across distributed regional transit cloud environments."
            ),
            source_uri="https://procurement.transit-portal.org/notices/PUB-TEN-2026-089"
        ),
        PublicOpportunityRecord(
            record_id="PUB-TEN-2026-114",
            title="Request for Proposal: Commercial Fleet Mechanical Transmission & Bearing Overhaul",
            issuing_entity="Municipal Heavy Transit Operations",
            sector_classification="336411",
            record_type="Commercial RFP",
            eligibility_tier="Standard Commercial",
            submission_deadline="2026-12-22",
            contact_email="fleet.contracts@transit.example.gov",
            contact_person="Fleet Maintenance Superintendent",
            raw_document_text=(
                "Municipal Heavy Transit is soliciting proposals for precision machine fabrication, depot-level mechanical transmission overhauls, "
                "and heavy vehicle powertrain refurbishments."
            ),
            source_uri="https://procurement.transit-portal.org/notices/PUB-TEN-2026-114"
        ),
    ]

    auditor = PublicRecordAuditor()

    print(f"\n[Executing Line-by-Line Qualification on {len(records)} Public Notices]...\n")

    for idx, rec in enumerate(records):
        verdict = auditor.audit_opportunity(profile, rec)

        print("-" * 75)
        print(f"Record [{idx+1}/{len(records)}]: {rec.record_id} - {rec.title}")
        print(f"  Issuer:         {rec.issuing_entity} | Classification: {rec.sector_classification}")
        print(f"  Fit Score:      {verdict.fit_score}/100 (Tier: {verdict.fit_tier.value})")
        print(f"  Code Matched:   {'✔ YES' if verdict.classification_matched else '❌ NO'} | Eligibility: {'✔ VERIFIED' if verdict.eligibility_verified else '❌ NO'}")
        print(f"  Signals:        {', '.join(verdict.competency_overlap_signals)}")
        if verdict.disqualification_flags:
            print(f"  Flags:          {', '.join(verdict.disqualification_flags)}")
        print(f"  Pursuit Angle:  {verdict.strategic_pursuit_angle}")
        print(f"  Escalation:     {'🚨 Mandatory Human Operator Review (Review-Ready Draft Prepared)' if verdict.requires_human_signoff else 'Auto-archived'}")

    print("\n" + "=" * 75)
    print("✔ Qualification Complete: Irrelevant notices discarded; high-fit tender flagged for human review.")
    print("=" * 75)


if __name__ == "__main__":
    run_public_record_audit_demo()
