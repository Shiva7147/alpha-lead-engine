"""Zero-dependency local HTTP web dashboard for Alpha Lead Engine.
Displays real-time lead tables, line-by-line audit metrics, and human review approvals in the browser.
"""

from __future__ import annotations

import http.server
import json
import logging
import socketserver
import threading
from urllib.parse import parse_qs, urlparse

from alpha_lead_engine.auditor.pipeline_store import PipelineStore
from alpha_lead_engine.auditor.schemas import LeadStatus

logger = logging.getLogger("alpha_lead_engine.dashboard")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alpha Lead Engine - Autonomous Intelligence Dashboard</title>
    <style>
        :root {
            --bg: #090d16;
            --surface: #111726;
            --surface-hover: #192238;
            --border: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #0ea5e9;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text-primary); padding: 32px 24px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
        h1 { font-size: 24px; font-weight: 600; letter-spacing: -0.02em; display: flex; align-items: center; gap: 12px; }
        .badge { background: rgba(14, 165, 233, 0.15); color: var(--accent); padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 500; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }
        .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
        .stat-label { color: var(--text-secondary); font-size: 13px; margin-bottom: 8px; }
        .stat-val { font-size: 28px; font-weight: 700; font-variant-numeric: tabular-nums; }
        .stat-val.green { color: var(--accent-green); }
        .stat-val.amber { color: var(--accent-amber); }
        .stat-val.blue { color: var(--accent); }
        
        .section-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
        .table-container { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin-bottom: 32px; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
        th { background: #0c1220; color: var(--text-secondary); padding: 12px 16px; font-weight: 500; border-bottom: 1px solid var(--border); }
        td { padding: 14px 16px; border-bottom: 1px solid var(--border); }
        tr:hover { background: var(--surface-hover); }
        .status-pill { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .status-NEEDS_HUMAN_REVIEW { background: rgba(245, 158, 11, 0.2); color: var(--accent-amber); }
        .status-SENT { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .status-QUEUED { background: rgba(14, 165, 233, 0.2); color: var(--accent); }
        .status-DISCOVERED { background: rgba(148, 163, 184, 0.2); color: var(--text-secondary); }
        
        button.action-btn { background: var(--accent); color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: 500; cursor: pointer; }
        button.action-btn:hover { background: #0284c7; }
        .score-pill { font-weight: 700; padding: 2px 8px; border-radius: 4px; }
        .score-high { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
        .score-med { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ Alpha Lead Engine <span class="badge">Live Pipeline</span></h1>
            <div style="color: var(--text-secondary); font-size: 13px;">Continuous Autonomous Line-by-Line Lead Qualification</div>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Discovered Targets</div>
                <div class="stat-val blue">__TOTAL_DISCOVERED__</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">MX Verified Mailboxes</div>
                <div class="stat-val green">__TOTAL_MX__</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Line-by-Line Audited</div>
                <div class="stat-val">__TOTAL_AUDITED__</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Pending Human Review 🚨</div>
                <div class="stat-val amber">__PENDING_HUMAN__</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Emails Dispatched</div>
                <div class="stat-val green">__TOTAL_SENT__</div>
            </div>
        </div>

        <div class="section-title">Tracked Targets & Intelligence Footprint</div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Target Company</th>
                        <th>Website / Source</th>
                        <th>Verified Contact</th>
                        <th>Audit Score</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    __LEAD_ROWS__
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    store = PipelineStore()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            metrics = self.store.get_campaign_metrics()
            leads = self.store.list_leads(limit=50)

            rows = []
            for l in leads:
                score = l.audit.score if l.audit else 0
                score_cls = "score-high" if score >= 75 else "score-med"
                status = l.status.value
                action_html = "-"
                if l.status == LeadStatus.NEEDS_HUMAN_REVIEW:
                    action_html = f"<form method='POST' action='/approve?id={l.id}' style='display:inline'><button class='action-btn' type='submit'>Approve & Send</button></form>"

                rows.append(f"""
                <tr>
                    <td><strong>{l.raw.business_name}</strong><br><span style='font-size:12px; color:var(--text-secondary);'>{l.audit.estimated_decision_maker if l.audit else ''}</span></td>
                    <td><a href='{l.raw.website or '#'}' target='_blank' style='color:var(--accent); text-decoration:none;'>{l.clean_domain or 'N/A'}</a></td>
                    <td>{l.raw.email or 'N/A'}<br><span style='font-size:11px; color:var(--accent-green);'>{'✔ MX Verified' if l.mx_valid else ''}</span></td>
                    <td><span class='score-pill {score_cls}'>{score}/100</span></td>
                    <td><span class='status-pill status-{status}'>{status}</span></td>
                    <td>{action_html}</td>
                </tr>
                """)

            html = HTML_TEMPLATE.replace("__TOTAL_DISCOVERED__", str(metrics.total_discovered))
            html = html.replace("__TOTAL_MX__", str(metrics.total_mx_verified))
            html = html.replace("__TOTAL_AUDITED__", str(metrics.total_audited))
            html = html.replace("__PENDING_HUMAN__", str(metrics.total_pending_human_review))
            html = html.replace("__TOTAL_SENT__", str(metrics.total_sent))
            html = html.replace("__LEAD_ROWS__", "\n".join(rows))

            self.wfile.write(html.encode("utf-8"))

        elif parsed.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            metrics = self.store.get_campaign_metrics()
            self.wfile.write(metrics.model_dump_json().encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/approve":
            params = parse_qs(parsed.query)
            lead_id = params.get("id", [None])[0]
            if lead_id:
                self.store.update_status(lead_id, LeadStatus.QUEUED)
                logger.info(f"Dashboard approved lead: {lead_id}")

            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()


def start_dashboard_server(port: int = 8501, blocking: bool = False):
    """Starts local zero-dependency HTTP dashboard."""
    server = socketserver.TCPServer(("", port), DashboardHandler)
    logger.info(f"Dashboard started at http://localhost:{port}")
    if blocking:
        server.serve_forever()
    else:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
