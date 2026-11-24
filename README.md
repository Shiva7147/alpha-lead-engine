# Alpha Lead Engine

Alpha Lead Engine is an open-source, production-grade autonomous framework for discovering B2B prospects, qualifying them through line-by-line web auditing, and running verified cold outreach directly through your own Gmail or Google Workspace account.

It is designed for small business owners, agency operators, and technical founders who need real pipeline growth without paying $400/month for fragmented SaaS scrapers that return stale, unverified databases.

```
                      +---------------------------------------+
                      |       1. Business Configuration       |
                      |   Offering, Target Keywords, Region   |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |       2. Multi-Engine Discovery       |
                      |   Playwright (Visible), Maps, DDG     |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |      3. DNS & MX Record Validator     |
                      |   Real-time Mail Exchange Verification|
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |    4. Line-by-Line AI Auditor (0-100) |
                      |    Evaluates Real Web Page Content    |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |  5. Fact-Backed Outreach Generation   |
                      |   Custom 3-Step Sequence (Initial/D3/D7)|
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |    6. Human Escalation Checkpoint     |
                      |    Mobile Push (ntfy/TG) or CLI Review|
                      +-------------------+-------------------+
                                          |
                                   [Operator Approves]
                                          |
                                          v
                      +---------------------------------------+
                      |     7. Autonomous Campaign Loop       |
                      |   Gmail OAuth Threading & Classifier  |
                      +---------------------------------------+
```

---

## Why This Exists: The Problem with Traditional Lead Generation

Most lead generation tools fail for three predictable reasons:

1. **Stale, Recycled Databases**: Contact databases like Apollo or ZoomInfo resell static lists compiled months or years ago. Decision makers change jobs, companies rebrand, and mailboxes get decommissioned.
2. **Generic Spam Templates**: Spray-and-pray emails that claim "I saw your website and loved what you're doing" burn domain reputation and land straight in spam folders.
3. **No Human Control**: Black-box automated bots send emails without checking deliverability or allowing the business owner to review the pitch, risking customer relationships.

Alpha Lead Engine takes a different approach:
- **Discovers fresh, active businesses** directly from public web directories, search engines, and target domains in real time.
- **Launches an actual browser instance** via Playwright. You can run it with `--visible` to watch the browser navigate, scroll, and parse content live on your screen.
- **Validates mail servers on the fly**: Before an email is ever queued, it performs an live DNS MX record lookup using `dnspython`. If the domain cannot accept mail, it is discarded immediately.
- **Performs line-by-line qualification**: Reads the actual text on the company's website to identify what they sell, their scale, and their decision makers, assigning an objective score from 0 to 100.
- **Cites real observations**: Every outreach draft must cite at least one specific offering or update found on their site.
- **Keeps humans in control**: High-scoring prospects pause at a human review checkpoint. You receive an alert on your phone (via free mobile push or terminal prompt) to review and approve the draft before a single email is dispatched.

---

## What Happens When You Run It (End-to-End Walkthrough)

When you clone this repository and run the engine, here is the exact progression:

### Step 1: Input Your Business Parameters
You supply three simple inputs in the interactive terminal:
```text
Enter your business/product name: Apex Cloud Consulting
Describe what you offer in 1-2 sentences: We help B2B companies automate security audits and migrate workloads to AWS.
Enter target niche / search keywords: B2B FinTech Companies
Enter target location: Austin, TX
Run browser visible? [y/n]: y
```

### Step 2: Live Browser Crawling & Discovery
If you select visible mode, an automated Chromium window opens on your screen. You watch the agent:
1. Search local business directories and maps for active companies matching your query.
2. Navigate directly to each prospect's website.
3. Scroll through homepages and `/about` or `/contact` pages.
4. Extract structured contact points: verified phone numbers, direct email addresses, physical office addresses, and LinkedIn/social profiles.

### Step 3: Real-Time DNS & MX Mailbox Verification
The engine takes every discovered email and performs an authoritative DNS query against the target domain's MX (Mail Exchange) records.
```text
Checking: david@fintech-firm.com
-> DNS MX query resolved to: aspmx.l.google.com (Priority 1)
-> Deliverability Status: VERIFIED
```
If the domain fails to resolve or is a known disposable provider, the email is flagged and blocked from the dispatch queue.

### Step 4: Line-by-Line AI Auditing
The engine analyzes the extracted website text against your business offering and assigns a quantified score:
```text
Target: Peak Financial Systems
Audit Score: 88/100 (Tier: High)
Observed Offerings: Cloud banking API integrations, automated reconciliation
Decision Maker Identified: Chief Technology Officer / Head of Infrastructure
Strategic Angle: Emphasize compliance acceleration and reduced migration downtime
```

### Step 5: Fact-Backed Draft Generation
Instead of generic fluff, the engine drafts an initial email and two follow-up bumps that cite the prospect's real services:
```text
Subject: Question regarding Peak Financial's cloud reconciliation architecture

Hi Alex,

I noticed Peak Financial's recent work on automated banking API integrations and real-time reconciliation. 

We built Apex Cloud Consulting to help FinTech teams streamline continuous compliance audits and AWS infrastructure migrations without taking engineering focus away from your core product.

Would you be open to a brief 5-minute conversation this Thursday to explore if we can accelerate your upcoming audit cycle?

Best regards,
Apex Cloud Consulting
```

### Step 6: Human Escalation Review (Phone & Terminal)
Before anything sends, a notification arrives:
- **On your phone**: If configured with **ntfy.sh** (free on iOS/Android) or **Telegram**, your phone vibrates with the prospect summary and email preview.
- **In your terminal**: Run `python -m alpha_lead_engine review` to inspect the draft, adjust the copy if desired, and press `[Approve]` or `[Reject]`.

### Step 7: Autonomous Campaign Loop via Gmail API
Approved emails are queued and dispatched through your authenticated Google OAuth connection:
- Day 1: Initial email sent with proper threading headers.
- Day 4 (Day 3 follow-up): If unreplied, a conversational 2-sentence bump is sent in the same thread.
- Day 8 (Day 7 follow-up): A final value-add note is sent with a relevant insight.
- **Inbound Reply Detection**: If the prospect replies:
  - If **Positive**: The sequence pauses immediately, flags `NEEDS_HUMAN_REVIEW`, and alerts you so you can close the conversation personally.
  - If **Unsubscribe**: The prospect is added to a local suppression list and never contacted again.

---

## Quickstart Guide

### 1. Requirements
- Python 3.10 or higher
- An internet connection for live crawling and DNS verification

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Shiva7147/alpha-lead-engine.git
cd alpha-lead-engine

# Option A: Fast install with pip
pip install -e .

# Option B: Fast install with uv
uv venv
uv pip install -e .

# Install Playwright browser binaries
playwright install chromium
```

### 3. Launching the Engine

#### Run Interactive Discovery & Auditing
```bash
python -m alpha_lead_engine run
```

#### Run the Standalone Verified Demo
To run a self-contained demonstration with mock and live data:
```bash
python examples/quickstart_demo.py
```

#### Launch the Local Web Dashboard
Alpha Lead Engine includes a zero-dependency HTTP dashboard:
```bash
python -c "from alpha_lead_engine.dashboard import start_dashboard_server; start_dashboard_server(8501, blocking=True)"
```
Open **`http://localhost:8501`** in your browser to view your pipeline metrics, live audit scores, and approve pending emails with one click.

#### Inspect Pipeline Status via Terminal
```bash
python -m alpha_lead_engine status
```

---

## Configuration & Optional Integrations

All core features work out of the box with zero external API keys using built-in search fallbacks and Playwright. For full production capabilities:

### 1. LLM Providers
Set your preferred API key in a `.env` file or terminal environment:
```bash
export GEMINI_API_KEY="your_key"
# or
export OPENAI_API_KEY="your_key"
# or
export ANTHROPIC_API_KEY="your_key"
```
*(If no API key is provided, the engine runs in deterministic standalone mode with built-in heuristic scoring).*

### 2. Google OAuth 2.0 (Gmail API)
To send emails directly from your own Gmail or Google Workspace address:
1. Download `credentials.json` from Google Cloud Console (Desktop Application).
2. Place `credentials.json` in the root folder.
3. Run `python -m alpha_lead_engine init` to complete the one-time browser sign-in.

### 3. Mobile Push Notifications (Free & Instant)
1. Install the free **ntfy** app on iOS or Android ([ntfy.sh](https://ntfy.sh)).
2. Subscribe to a topic name (e.g., `my_lead_alerts`).
3. Set `NTFY_TOPIC=my_lead_alerts` in your environment. Alerts will push to your device whenever an operator decision is needed.

---

## Repository Architecture

```
alpha-lead-engine/
├── README.md                                 # Complete documentation & walkthrough
├── pyproject.toml                            # Modern package manifest
├── requirements.txt                          # Production dependencies
│
├── alpha_lead_engine/                        # Core Application
│   ├── engine.py                             # High-level orchestrator & state coordinator
│   ├── cli.py                                # Rich interactive terminal & review console
│   ├── dashboard.py                          # Zero-dependency local web dashboard (port 8501)
│   ├── public_records.py                     # Unstructured public tender & record qualification engine
│   │
│   ├── crawlers/                             # Discovery & Web Ingestion
│   │   ├── crawler_router.py                 # Multi-engine orchestrator & domain deduplication
│   │   ├── playwright_engine.py              # Visual & headless browser crawler with stealth
│   │   ├── firecrawl_engine.py               # Markdown extraction for LLMs
│   │   ├── crawl4ai_engine.py                # Local async crawler
│   │   ├── maps_scraper.py                   # Local business & directory scraper
│   │   └── apify_connector.py                # Optional distributed cloud scraper
│   │
│   ├── auditor/                              # Line-by-Line AI Auditor & DNS Gate
│   │   ├── schemas.py                        # Pydantic v2 data models & state enums
│   │   ├── syntax_and_mx_validator.py        # Real-time DNS/MX deliverability checks
│   │   ├── lead_scorer.py                    # Line-by-line website text evaluation (0-100)
│   │   └── pipeline_store.py                 # Persistent SQLite database & state manager
│   │
│   ├── outreach/                             # Context-Aware Fact-Backed Outreach
│   │   └── personalizer.py                   # 3-part factual sequence generator (Initial, D3, D7)
│   │
│   ├── automation/                           # Autonomous Campaign Lifecycle & Gmail API
│   │   ├── gmail_oauth.py                    # Google OAuth 2.0 flow & token management
│   │   ├── sender.py                         # Threaded MIME message dispatcher
│   │   ├── tracker_and_followup.py           # Day 3 & Day 7 follow-up tracking daemon
│   │   └── reply_classifier.py               # Intent classifier (Positive, Not Now, Unsubscribe)
│   │
│   ├── escalation/                           # Human-in-the-Loop & Mobile Bridge
│   │   └── bridge.py                         # Push notifications to phone (ntfy.sh, Telegram, Webhook)
│   │
│   └── llm/                                  # Multi-Provider LLM Wrapper
│       └── client.py                         # Unified client for Gemini, OpenAI, Claude & fallback
│
├── frontend/                                 # Modern TypeScript / React UI Tier
│   ├── src/App.tsx                           # Pipeline visual dashboard & approval UI
│   ├── package.json                          # Vite, React, Lucide dependencies
│   └── tsconfig.json                         # TypeScript compiler configuration
│
├── config/                                   # Engine Configurations
│   └── default_config.yaml                   # Crawler, auditor, and campaign settings
│
├── docs/                                     # Architecture & Setup Guides
│   ├── architecture/system_design.md         # In-depth architectural breakdown
│   ├── guides/google_oauth_setup.md          # Gmail API OAuth 2.0 setup guide
│   └── guides/mobile_push_setup.md           # Real-time mobile push notifications setup
│
├── scripts/                                  # Development & Benchmarking Utilities
│   └── benchmark_pipeline.py                 # Latency & throughput benchmarking
│
├── examples/                                 # Executable Demonstrations
│   ├── quickstart_demo.py                    # Commercial lead discovery, live crawl & audit demo
│   └── public_record_audit_demo.py           # Public tender & opportunity qualification showcase
│
└── tests/                                    # Automated Pytest Suite
    └── test_core.py                          # Unit & integration tests for all subsystems
```

---

## Testing

Run the automated test suite with pytest:

```bash
pytest
```

---

## Contributing & Open Source License

Alpha Lead Engine is open-source under the **Apache-2.0 License**. You are free to fork this repository, build custom integrations, adapt it for client services, or run it internally for your own business pipeline.
