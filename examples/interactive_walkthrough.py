"""Interactive end-to-end walkthrough for new operators.
Guides you through setting up a business profile, understanding how the multi-crawler pipeline operates,
and reviewing an actual qualified lead with DNS verification.
"""

import sys
import time

def slow_print(text: str, delay: float = 0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def main():
    print("=" * 70)
    print("⚡ ALPHA LEAD ENGINE - Interactive Operator Walkthrough")
    print("=" * 70)
    
    slow_print("\nWelcome to Alpha Lead Engine.")
    slow_print("This framework was built so that you don't have to buy stale lead lists or run generic cold emails.")
    slow_print("Instead, it finds live, active businesses, parses their real website content, and drafts human-in-the-loop outreach.\n")

    print("[Phase 1: Defining Your Business & Target ICP]")
    print("  You tell the engine:")
    print("    1. What you sell: 'Enterprise Cloud Migration & Automated SOC2 Auditing'")
    print("    2. Target Industry: 'B2B FinTech Companies'")
    print("    3. Target Location: 'Austin, TX (or Worldwide)'")

    input("\nPress [Enter] to see how the crawler discovers targets...")

    print("\n[Phase 2: Multi-Engine Discovery & Visual Playwright Crawling]")
    print("  The engine boots an automated browser session:")
    print("    • Searches Google Maps & directory listings matching your niche")
    print("    • Resolves root domains (e.g. https://peakfinancial.example.com)")
    print("    • Opens the page visibly so you can watch it scroll and read the DOM")
    print("    • Extracts: Company name, emails, office phone, and key executive names")

    input("\nPress [Enter] to see how the DNS & MX Verification works...")

    print("\n[Phase 3: Real-Time DNS & MX Deliverability Gate]")
    print("  Before drafting any outreach, we protect your email sender reputation:")
    print("    • Queries target domain's MX (Mail Exchange) record via dnspython")
    print("    • Verifies target mailbox can accept SMTP connections")
    print("    • Rejects dead domains and disposable temporary emails automatically")

    input("\nPress [Enter] to see how the Line-by-Line AI Auditor evaluates content...")

    print("\n[Phase 4: Line-by-Line AI Auditing & Scoring]")
    print("  The engine evaluates the extracted text against your ICP:")
    print("    • Fit Score: 88/100 (Tier: High)")
    print("    • Key Offerings Observed: Cloud banking API integrations, automated reconciliation")
    print("    • Decision Maker Identified: CTO / VP of Infrastructure")
    print("    • Disqualification Flags: None (Active B2B software operation)")

    input("\nPress [Enter] to see the Context-Aware Outreach Draft...")

    print("\n[Phase 5: Fact-Backed Draft Generation]")
    print("  Instead of generic spam, it drafts an email referencing actual facts from their site:")
    print("-" * 70)
    print("Subject: Question regarding Peak Financial's cloud reconciliation architecture\n")
    print("Hi Alex,\n")
    print("I noticed Peak Financial's recent work on automated banking API integrations and real-time reconciliation.")
    print("We help FinTech teams streamline continuous compliance audits and AWS infrastructure migrations without taking engineering focus away from your core product.\n")
    print("Would you be open to a brief 5-minute conversation this Thursday to explore if we can accelerate your upcoming audit cycle?\n")
    print("Best regards,")
    print("Alpha Lead Engine Operator")
    print("-" * 70)

    input("\nPress [Enter] to see the Human Escalation Checkpoint...")

    print("\n[Phase 6: Human Escalation Checkpoint & Mobile Notifications]")
    print("  The system halts before sending:")
    print("    • A push notification vibrates on your phone via ntfy.sh or Telegram")
    print("    • You can review the draft on your phone or in the terminal")
    print("    • Once you approve, it queues for dispatch through your Gmail OAuth connection")

    print("\n" + "=" * 70)
    print("✔ Walkthrough complete!")
    print("To run the real engine on your computer:")
    print("  python -m alpha_lead_engine run")
    print("=" * 70)

if __name__ == "__main__":
    main()
