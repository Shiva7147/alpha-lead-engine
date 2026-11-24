# ⚡ Alpha Lead Engine

> **Production-ready, autonomous AI lead discovery, line-by-line validation, and multi-channel outreach framework.**  
> Built to turn scattered, unstructured public web data into clean, structured, verified records.  
> Designed to run natively inside **Google Antigravity** or as a standalone CLI application.

---

## 🌟 The Core Problem We Solve

Across modern sales, commercial partnerships, and tender analysis, teams waste hundreds of hours manually browsing directories, public portals, commercial registries, and fragmented websites.

Standard scrapers only dump noisy, unvetted data into CSVs. 
**Alpha Lead Engine takes an entirely different architectural approach:**
1. **Multi-Engine Discovery**: Crawls target directories and websites via Playwright (visible or headless), Firecrawl, and Crawl4AI.
2. **Line-by-Line AI Auditing**: Evaluates the real extracted website text or document against the operator's exact capability profile—scoring alignment from 0 to 100.
3. **Real-time DNS & MX Verification**: Validates mail server exchange records in real-time with `dnspython` to guarantee deliverability and eliminate bounces before anything is queued.
4. **Context-Aware Fact-Backed Personalization**: Synthesizes outreach drafts citing real, verified offerings and facts from the target's digital footprint.
5. **Strict Human Escalation (Human-in-the-Loop)**: High-impact actions (sending initial emails, qualifying tenders, or replying to inquiries) trigger an immediate escalation checkpoint with real-time mobile push notifications (**ntfy.sh**, **Telegram**, or webhook).
6. **Autonomous Lifecycle Engine**: Integrates Google OAuth 2.0 (Gmail API) to dispatch approved emails, automatically manage Day 3 and Day 7 follow-ups if unreplied, and pause sequences the instant an interested reply is detected.

---

## 🏛 Public Record & Tender Qualification Architecture

In addition to commercial B2B lead generation, Alpha Lead Engine includes an **Unstructured Public Record Ingestion Engine (`alpha_lead_engine/public_records.py`)**:
- Ingests messy, unstructured public tenders, commercial RFPs, and expressions of interest (EOIs).
- Measures technical specifications and industry classifications (NAICS, UNSPSC, SIC) against an organization's verified capabilities and past performance.
- Eliminates noise by automatically disqualifying non-matching notices and preparing review-ready response angles for high-fit opportunities.
- Guarantees human oversight through mandatory sign-off checkpoints before any response is dispatched.

---

## 📂 Complete File Tree & Architecture

The entire codebase is cleanly structured and decoupled:

```
alpha-lead-engine/
├── README.md                                 # Architecture overview and quickstart guide
├── pyproject.toml                            # Modern pyproject configuration
├── requirements.txt                          # Production dependency specifications
├── .gitignore                                # Environment and database exclusions
│
├── alpha_lead_engine/                        # Core Engine Package
│   ├── __init__.py                           # Package exports
│   ├── __main__.py                           # CLI entrypoint
│   ├── engine.py                             # High-level pipeline coordinator
│   ├── cli.py                                # Rich interactive CLI terminal & review console
│   ├── dashboard.py                          # Zero-dependency local HTTP web dashboard (port 8501)
│   ├── public_records.py                     # Unstructured public notice & tender qualification engine
│   │
│   ├── crawlers/                             # Multi-Engine Discovery Pipeline
│   │   ├── __init__.py
│   │   ├── crawler_router.py                 # Multi-engine orchestrator & domain deduplication
│   │   ├── playwright_engine.py              # Visual/Headless browser crawler with stealth protection
│   │   ├── firecrawl_engine.py               # Markdown synthesis for LLM ingestion
│   │   ├── crawl4ai_engine.py                # Async local crawler without external API keys
│   │   ├── maps_scraper.py                   # Local business & directory scraper
│   │   └── apify_connector.py                # Optional distributed cloud scraper connector
│   │
│   ├── auditor/                              # Line-by-Line AI Auditor & DNS Validator
│   │   ├── __init__.py
│   │   ├── schemas.py                        # Pydantic v2 data models & state enums
│   │   ├── syntax_and_mx_validator.py        # Real-time DNS/MX mail server validation
│   │   ├── lead_scorer.py                    # Line-by-line LLM auditor & fit scoring (0-100)
│   │   └── pipeline_store.py                 # Persistent SQLite database & state manager
│   │
│   ├── outreach/                             # Context-Aware Fact-Backed Outreach
│   │   ├── __init__.py
│   │   └── personalizer.py                   # 3-part factual sequence generator (Initial, D3, D7)
│   │
│   ├── automation/                           # Autonomous Campaign Lifecycle & Gmail API
│   │   ├── __init__.py
│   │   ├── gmail_oauth.py                    # Google OAuth 2.0 flow & token management
│   │   ├── sender.py                         # Threaded MIME message dispatcher
│   │   ├── tracker_and_followup.py           # Day 3 & Day 7 follow-up tracking daemon
│   │   └── reply_classifier.py               # Intent classifier (Positive, Not Now, Unsubscribe)
│   │
│   ├── escalation/                           # Human-in-the-Loop & Mobile Bridge
│   │   ├── __init__.py
│   │   └── bridge.py                         # Push notifications to phone (ntfy.sh, Telegram, Webhook)
│   │
│   └── llm/                                  # Multi-Provider LLM Wrapper
│       ├── __init__.py
│       └── client.py                         # Gemini 2.5, OpenAI, Claude, and deterministic fallback
│
├── examples/                                 # Executable End-to-End Demonstrations
│   ├── quickstart_demo.py                    # Commercial lead discovery, live crawl & audit demo
│   └── public_record_audit_demo.py           # Public tender & opportunity qualification showcase
│
└── tests/                                    # Automated Pytest Suite
    └── test_core.py                          # Unit & integration tests for all subsystems
```

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/Shiva7147/alpha-lead-engine.git
cd alpha-lead-engine

# Install dependencies
pip install -e .

# Install Playwright browser binaries
playwright install chromium
```

### 2. Run Interactive Discovery (Watch Playwright Live!)

```bash
python -m alpha_lead_engine run
```
You can toggle `Run browser visible? [y/n]` to **watch Chromium open on your screen**, navigate directories, and extract contact records in real time.

### 3. Launch the Web Dashboard

```bash
python -c "from alpha_lead_engine.dashboard import start_dashboard_server; start_dashboard_server(8501, blocking=True)"
```
Open **http://localhost:8501** in your browser to inspect discovered targets, view line-by-line audit metrics, and approve drafted emails.

### 4. Run the Public Record & Tender Qualification Demo

```bash
python examples/public_record_audit_demo.py
```

### 5. Review Flagged Leads via Human Escalation Console

```bash
python -m alpha_lead_engine review
```

---

## 📱 Mobile Phone Escalation Bridge

Alpha Lead Engine guarantees that high-stakes actions require human review:
1. Install the free **ntfy** app on your iPhone or Android ([ntfy.sh](https://ntfy.sh)).
2. Subscribe to a topic (e.g., `alpha_lead_engine_alerts`).
3. Set `NTFY_TOPIC=alpha_lead_engine_alerts` in your environment.
4. Alerts vibrate directly on your mobile device with prospect details and an approval action link.

---

## 🧪 Testing

```bash
pytest
```

---

## 📄 License
Open-source under the **Apache-2.0 License**.
